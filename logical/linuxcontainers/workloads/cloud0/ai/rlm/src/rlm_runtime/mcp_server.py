"""
RLM MCP Server - Model Context Protocol server exposing RLM as tools.

Usage:
    python -m rlm_runtime.mcp_server        # stdio transport
    python -m rlm_runtime.ws_mcp            # WebSocket transport

Environment Variables:
    LLM_BASE_URL    OpenAI-compatible endpoint (default: http://gpu-worker-0:8080/v1)
    LLM_MODEL       Model to use (default: nvidia/nemotron-3-nano)
    LLM_API_KEY     API key if required (default: sk-not-needed)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

from .adapters import GenericChatAdapter
from .context import Context
from .policy import Policy
from .prompts import LLAMA_SYSTEM_PROMPT
from .rlm import RLM

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("rlm_mcp_server")


class MCPServer:
    """MCP server implementation."""

    def __init__(self) -> None:
        self.base_url = os.getenv("LLM_BASE_URL", "http://gpu-worker-0:8080/v1")
        self.model = os.getenv("LLM_MODEL", "nvidia/nemotron-3-nano")
        self.api_key = os.getenv("LLM_API_KEY", "sk-not-needed")

        self.adapter = GenericChatAdapter(
            base_url=self.base_url,
            model=self.model,
            api_key=self.api_key,
        )
        self.policy = Policy(max_steps=15, max_subcalls=10, max_total_tokens=20000)
        self.rlm = RLM(
            adapter=self.adapter,
            policy=self.policy,
            system_prompt=LLAMA_SYSTEM_PROMPT,
            require_repl_before_final=True,
        )
        logger.info(f"RLM MCP Server initialized with {self.base_url}, model={self.model}")

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "rlm-server", "version": "0.1.0"},
        }

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "rlm_query",
                "description": (
                    "Query over large documents using Recursive Language Models (RLM). "
                    "Handles arbitrarily large contexts by treating them as environment state."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The question to answer"},
                        "context": {"type": "string", "description": "Full text content to query"},
                        "file_path": {"type": "string", "description": "Path to file to load as context"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "rlm_query_files",
                "description": "Query over multiple files using RLM.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The question to answer"},
                        "file_paths": {"type": "array", "items": {"type": "string"}, "description": "List of file paths"},
                        "glob_pattern": {"type": "string", "description": "Glob pattern to find files"},
                    },
                    "required": ["query"],
                },
            },
        ]

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "rlm_query":
            return self._handle_rlm_query(arguments)
        elif name == "rlm_query_files":
            return self._handle_rlm_query_files(arguments)
        return {"error": f"Unknown tool: {name}"}

    def _handle_rlm_query(self, args: dict[str, Any]) -> dict[str, Any]:
        query = args.get("query", "")
        context_text = args.get("context", "")
        file_path = args.get("file_path")

        if file_path:
            try:
                context_text = Path(file_path).expanduser().read_text()
                logger.info(f"Loaded {len(context_text)} chars from {file_path}")
            except Exception as e:
                return {"error": f"Failed to load file: {e}"}

        if not context_text:
            return {"error": "No context provided. Supply 'context' or 'file_path'."}

        context = Context.from_text(context_text)
        logger.info(f"Running RLM query over {context.len_chars()} chars")

        try:
            output, trace = self.rlm.run(query, context)
            return {"answer": output, "steps": len(trace.steps), "context_size": context.len_chars()}
        except Exception as e:
            logger.exception("RLM query failed")
            return {"error": str(e)}

    def _handle_rlm_query_files(self, args: dict[str, Any]) -> dict[str, Any]:
        query = args.get("query", "")
        file_paths = args.get("file_paths", [])
        glob_pattern = args.get("glob_pattern")

        documents: list[str] = []
        for fp in file_paths:
            try:
                content = Path(fp).expanduser().read_text()
                documents.append(f"=== {fp} ===\n{content}")
            except Exception as e:
                logger.warning(f"Failed to load {fp}: {e}")

        if glob_pattern:
            for path in Path.cwd().glob(glob_pattern):
                if path.is_file():
                    try:
                        documents.append(f"=== {path} ===\n{path.read_text()}")
                    except Exception as e:
                        logger.warning(f"Failed to load {path}: {e}")

        if not documents:
            return {"error": "No files loaded."}

        context = Context.from_documents(documents)
        try:
            output, trace = self.rlm.run(query, context)
            return {"answer": output, "steps": len(trace.steps), "files_loaded": len(documents)}
        except Exception as e:
            logger.exception("RLM query failed")
            return {"error": str(e)}

    async def handle_message(self, message: dict[str, Any]) -> dict[str, Any] | None:
        method = message.get("method")
        msg_id = message.get("id")
        params = message.get("params", {})
        result: Any = None

        if method == "initialize":
            result = self.get_capabilities()
        elif method == "notifications/initialized":
            return None
        elif method == "tools/list":
            result = {"tools": self.list_tools()}
        elif method == "tools/call":
            tool_result = self.call_tool(params.get("name", ""), params.get("arguments", {}))
            result = {"content": [{"type": "text", "text": json.dumps(tool_result, indent=2)}]}
        else:
            return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}

        if msg_id is not None:
            return {"jsonrpc": "2.0", "id": msg_id, "result": result}
        return None

    async def run_stdio(self) -> None:
        logger.info("RLM MCP Server starting on stdio...")
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)
        writer_transport, writer_protocol = await asyncio.get_event_loop().connect_write_pipe(
            asyncio.streams.FlowControlMixin, sys.stdout
        )
        writer = asyncio.StreamWriter(writer_transport, writer_protocol, reader, asyncio.get_event_loop())

        while True:
            try:
                line = await reader.readline()
                if not line:
                    break
                message = json.loads(line.decode("utf-8").strip())
                response = await self.handle_message(message)
                if response:
                    writer.write((json.dumps(response) + "\n").encode("utf-8"))
                    await writer.drain()
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
            except Exception as e:
                logger.exception(f"Error: {e}")


def main() -> None:
    server = MCPServer()
    asyncio.run(server.run_stdio())


if __name__ == "__main__":
    main()
