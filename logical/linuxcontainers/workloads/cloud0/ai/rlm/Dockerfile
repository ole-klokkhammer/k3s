FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir . websockets && \
    chmod +x /app/entrypoint.sh

EXPOSE 8765 8766

ENV LLM_BASE_URL=http://gpu-worker-0:8080/v1 \
    LLM_MODEL=nvidia/nemotron-3-nano \
    LLM_API_KEY=sk-not-needed \
    RLM_MCP_WS_PORT=8765 \
    RLM_MCP_HTTP_PORT=8766

CMD ["/app/entrypoint.sh"]
