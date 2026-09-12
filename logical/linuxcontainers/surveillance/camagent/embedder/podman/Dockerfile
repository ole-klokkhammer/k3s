# Embedder image: CUDA 13.0 runtime for Blackwell (sm_120) + CLIP encoder
# + pgvector/nats clients. Same base + torch-cu130 convention as the
# detector image. fully-qualified image name (LXC has no
# unqualified-search registries).
FROM docker.io/nvidia/cuda:13.0.3-cudnn-runtime-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.12 python3-pip ca-certificates libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY embedder.py /app/embedder.py

# torch (cu130) first, then the rest
RUN python3.12 -m pip install --no-cache-dir "torch==2.13.0+cu130" --index-url https://download.pytorch.org/whl/cu130 \
    && python3.12 -m pip install --no-cache-dir transformers pillow fastapi "uvicorn[standard]" psycopg2-binary nats-py

# bake in the default CLIP model so the container has no internet dependency
# (512-dim - matches the vector(512) column in ../../sql/schema.sql)
RUN python3.12 -m pip install --no-cache-dir huggingface_hub \
    && python3.12 -c "from huggingface_hub import snapshot_download; snapshot_download('openai/clip-vit-base-patch32', local_dir='/models/clip-vit-b32')"

CMD ["python3", "/app/embedder.py"]
