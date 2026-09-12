#!/bin/sh
set -e

# Start HTTP MCP server in background
python -m rlm_runtime.http_mcp &
HTTP_PID=$!

# Start WebSocket MCP server in foreground
#python -m rlm_runtime.ws_mcp &
#WS_PID=$!

# Wait for either to exit
wait $HTTP_PID #$WS_PID
