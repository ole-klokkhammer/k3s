"""
WebSocket MCP wrapper for rlm-runtime.

Listens on RLM_MCP_WS_PORT and accepts JSON-RPC messages.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os

import websockets

from .mcp_server import MCPServer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rlm_ws_mcp")

PORT = int(os.getenv("RLM_MCP_WS_PORT", "8765"))
HOST = os.getenv("RLM_MCP_WS_HOST", "0.0.0.0")

server = MCPServer()


async def handler(ws):
    async for msg in ws:
        try:
            payload = json.loads(msg)
            resp = await server.handle_message(payload)
            if resp is not None:
                await ws.send(json.dumps(resp))
        except Exception as e:
            logger.exception("handler error")
            await ws.send(json.dumps({"error": str(e)}))


async def main():
    async with websockets.serve(handler, HOST, PORT):
        logger.info(f"RLM WS MCP listening on ws://{HOST}:{PORT}")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
