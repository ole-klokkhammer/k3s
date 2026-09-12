"""
HTTP MCP wrapper for rlm-runtime.

Provides both HTTP POST endpoint and SSE (Server-Sent Events) for MCP protocol.
Continue uses SSE transport for MCP servers.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import time
import uuid
from queue import Empty, Queue
from typing import Any

from .mcp_server import MCPServer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rlm_http_mcp")

PORT = int(os.getenv("RLM_MCP_HTTP_PORT", "8766"))
HOST = os.getenv("RLM_MCP_HTTP_HOST", "0.0.0.0")

server = MCPServer()


class _Session:
    def __init__(self) -> None:
        self.id = uuid.uuid4().hex
        self.inbox: Queue[dict[str, Any]] = Queue()
        self.outbox: Queue[dict[str, Any]] = Queue()
        self.stop = threading.Event()
        self.worker = threading.Thread(target=self._run, name=f"mcp-session-{self.id}", daemon=True)
        self.worker.start()

    def _run(self) -> None:
        while not self.stop.is_set():
            try:
                msg = self.inbox.get(timeout=0.5)
            except Empty:
                continue

            try:
                response = asyncio.run(server.handle_message(msg))
                if response is not None:
                    self.outbox.put(response)
            except Exception as e:
                self.outbox.put({"jsonrpc": "2.0", "id": msg.get("id"), "error": {"code": -32000, "message": str(e)}})


_sessions: dict[str, _Session] = {}
_sessions_lock = threading.Lock()


class MCPHTTPHandler(BaseHTTPRequestHandler):
    """HTTP handler for MCP JSON-RPC requests."""

    def log_message(self, format, *args):
        logger.info("%s - %s", self.address_string(), format % args)

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK\n")
        elif self.path in ("/sse", "/events"):
            # MCP over SSE (Continue will typically try /sse)
            self.handle_sse()
        elif self.path == "/":
            # Helpful landing page
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"RLM MCP Server\n\nEndpoints:\n  GET  /health\n  GET  /sse\n  POST /message?session=<id>\n  POST /mcp (direct JSON-RPC)\n")
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/mcp":
            # Direct JSON-RPC (sync) - useful for curl
            self.handle_mcp_post()
        elif self.path.startswith("/message"):
            # MCP over SSE message channel (async)
            self.handle_sse_message()
        else:
            self.send_response(404)
            self.end_headers()

    def handle_mcp_post(self):
        """Handle MCP JSON-RPC over HTTP POST."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            payload = json.loads(body.decode("utf-8"))

            # Run async handler in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(server.handle_message(payload))
            finally:
                loop.close()

            if response:
                response_body = json.dumps(response).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_cors_headers()
                self.send_header("Content-Length", str(len(response_body)))
                self.end_headers()
                self.wfile.write(response_body)
            else:
                self.send_response(204)
                self.end_headers()

        except json.JSONDecodeError as e:
            self.send_error(400, f"Invalid JSON: {e}")
        except Exception as e:
            logger.exception("MCP handler error")
            self.send_error(500, str(e))

    def handle_sse(self):
        """Handle SSE connection for MCP.

        Minimal MCP-over-SSE:
        - Client opens GET /sse
        - Server replies with an "endpoint" event telling where to POST messages
        - Client POSTs JSON-RPC messages to that endpoint
        - Server sends JSON-RPC responses back as "message" events
        """

        session = _Session()
        with _sessions_lock:
            _sessions[session.id] = session

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_cors_headers()
        self.end_headers()

        # Tell client where to POST messages.
        endpoint_payload = {
            # Some clients look for uri, others for url.
            "uri": f"/message?session={session.id}",
            "url": f"/message?session={session.id}",
        }
        self.send_sse_event("endpoint", endpoint_payload)

        # Stream responses.
        try:
            last_keepalive = 0.0
            while True:
                now = time.time()
                if now - last_keepalive > 25:
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
                    last_keepalive = now

                try:
                    resp = session.outbox.get(timeout=0.5)
                except Empty:
                    continue

                self.send_sse_event("message", resp)
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            session.stop.set()
            with _sessions_lock:
                _sessions.pop(session.id, None)


    def handle_sse_message(self) -> None:
        """Handle POSTs to the SSE message endpoint."""
        # Parse session id from query string.
        session_id = None
        if "?" in self.path:
            _path, query = self.path.split("?", 1)
            for part in query.split("&"):
                if part.startswith("session="):
                    session_id = part.split("=", 1)[1]
                    break

        if not session_id:
            self.send_error(400, "Missing session")
            return

        with _sessions_lock:
            session = _sessions.get(session_id)

        if session is None:
            self.send_error(404, "Unknown session")
            return

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            payload = json.loads(body.decode("utf-8"))
        except Exception as e:
            self.send_error(400, f"Invalid request: {e}")
            return

        # Enqueue and return quickly.
        session.inbox.put(payload)
        self.send_response(202)
        self.send_cors_headers()
        self.end_headers()

    def send_sse_event(self, event: str, data: Any):
        """Send an SSE event."""
        self.wfile.write(f"event: {event}\n".encode())
        self.wfile.write(f"data: {json.dumps(data)}\n\n".encode())
        self.wfile.flush()


def main():
    httpd = ThreadingHTTPServer((HOST, PORT), MCPHTTPHandler)
    logger.info(f"RLM HTTP MCP listening on http://{HOST}:{PORT}")
    logger.info("  GET  /health")
    logger.info("  GET  /sse")
    logger.info("  POST /message?session=<id>")
    logger.info("  POST /mcp (direct JSON-RPC)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()


if __name__ == "__main__":
    main()
