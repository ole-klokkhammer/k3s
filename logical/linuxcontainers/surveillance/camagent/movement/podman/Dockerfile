# Detector image: CUDA 13.0 runtime for Blackwell (sm_120) + Python YOLO service.
# host driver is CUDA 13.3-capable, >= container runtime 13.0 (driver is
# forward-compatible with older runtimes).
# torch must come from the cu130 index - its wheels carry sm_120 kernels.
# fully-qualified: the LXC's registries.conf has no unqualified-search
# registries, so short names fail (same convention as the mediamtx quadlet)
FROM docker.io/nvidia/cuda:13.0.3-cudnn-runtime-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.12 python3-pip ca-certificates libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY detector.py /app/detector.py

# torch (cu130) first, then ultralytics keeps it; opencv for RTSP capture
RUN python3.12 -m pip install --no-cache-dir "torch==2.13.0+cu130" --index-url https://download.pytorch.org/whl/cu130 \
    && python3.12 -m pip install --no-cache-dir ultralytics opencv-python-headless

# bake in the default model so the container has no internet dependency
RUN mkdir -p /models \
    && cd /models \
    && python3.12 -c "from ultralytics import YOLO; YOLO('yolo11m.pt')"

CMD ["python3", "/app/detector.py"]
