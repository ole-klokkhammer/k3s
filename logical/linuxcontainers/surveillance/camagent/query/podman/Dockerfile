# Query agent: CPU-only. Tool execution + HTTP plumbing live here; the LLM
# (Gemma) runs on the 5090 llm LXC behind QUERY_LLM_BASE_URL.
FROM docker.io/python:3.12-slim-bookworm

WORKDIR /app
COPY agent.py /app/agent.py
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" httpx psycopg2-binary

CMD ["python3", "/app/agent.py"]
