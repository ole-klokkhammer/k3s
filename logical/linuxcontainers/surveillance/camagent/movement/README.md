# detector - camera object detection (cats)

GPU YOLO service running in the **camagent LXC** (`core:camagent`; mediamtx runs in its own LXC).
Watches a mediamtx re-served stream and raises cat-detection events with
throttled stills on the recordings pool.

## data flow

    camera -> mediamtx (:8554, TCP) -> detector (GPU) -> events/stills
                                                 (mediamtx keeps recording the sub separately)

the detector consumes the MAIN stream (2560px), downscale
longest edge to `DETECTOR_INPUT_SIZE` (1280 default), and infer on
the RTX 5060 Ti. v1 detection scope: **cat** (COCO class 15) with the
generic YOLO11m; fine-tune later, see "model" below.

## layout

    detector/
      podman/
        detector.py            the service (env-configured, JSON events to journal)
        Dockerfile             nvidia/cuda 13.0 + torch cu130 (Blackwell sm_120) + ultralytics
        detector.container     podman quadlet (Network=host, CDI GPU, config/media mounts)
        detector.env.example   copy to LXC /config/detector/.env
        Makefile               image (build in LXC) / deploy / logs
        .gitignore             .env, detector.env never in git

## LXC preflight (run once)

    lxc exec core:camagent -- sh -c '
      nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv
      systemctl is-active nvidia-cdi-refresh.service
      df -h /var/lib/containers /media'

# CUDA note: nvidia-smi's "CUDA Version" line is the DRIVER ceiling.
# the container ships its own CUDA 13.0 runtime; the driver (13.3-capable)
# is forward-compatible with older runtimes, so 13.0 runs on it.

requirements:
* the LXC's registries.conf defines no unqualified-search registries, so
  image names must be fully qualified (docker.io/..., registry.linole.org/...)
* NVIDIA driver visible inside the LXC (profile gpu=0 passthrough)
* CDI generated + service running (nvidia-container-toolkit setup is in
  ../README.md) - the quadlet uses `Device=nvidia.com/gpu=all`
* ~10 GB free in /var/lib/containers (cuda base + torch cu130 + ultralytics)
* one-off proof of GPU-in-container (the test from ../README.md):
      lxc exec core:camagent -- podman run --rm --device nvidia.com/gpu=all \
          nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi -L

## deploy

    cd logical/linuxcontainers/surveillance/detector/podman
    make image        # ~6-10 min first time (cuda base + torch + model download)
    make deploy       # dirs + .env (first time) + quadlet + restart
    make logs         # watch: "model ready; watching ...", then heartbeats

expected log lines:

    model ready; watching rtsp://127.0.0.1:8554/entrance_roof (input 1280px, conf 0.50)
    {"event": "cat_detection", "ts": 1729999999.0, "dets": 1, "best_conf": 0.63, "bbox": [x1,y1,x2,y2], "fps": 9.7}
    heartbeat: frames=600 fps=9.8 last_dets=0 stream_ok=1

## config (env, in /config/detector/.env)

    DETECTOR_RTSP_URL      rtsp://127.0.0.1:8554/entrance_roof   # mediamtx main, TCP
    DETECTOR_INPUT_SIZE    1280                                    # downscale longest edge
    DETECTOR_CONF          0.5
    DETECTOR_DEVICE        cuda:0                                  # cpu to test without GPU
    DETECTOR_MODEL         /models/yolo11m.pt                      # baked into image
    DETECTOR_EVENT_DIR     /media/detector/events
    DETECTOR_STILL_EVERY   10                                       # seconds between stills
    DETECTOR_LOG_EVERY     60

## events

a detection burst (>=3 detections inside 2 s) logs one JSON line
(dedupe: one event per burst, not per frame) and writes a still
throttled by DETECTOR_STILL_EVERY.

stills: LXC /media/detector/events/cat_YYYYMMDD_HHMMSS.jpg
        host /hdd/surveillance/detector/events/  (/media <-> host /hdd/surveillance)

## model

* v1: generic COCO YOLO11m (25 MB, cat = class 15). Good enough to see
  if the pipeline works; expect false positives (birds, shadows) at
  this resolution.
* fine-tune (on any machine with the GPU): collect images from the
  stills you've accumulated, label cats, then
      yolo detect train model=yolo11m.pt data=cats.yaml epochs=50 imgsz=1280
  and point DETECTOR_MODEL at the fine-tuned .pt in /config/detector/.
  No image rebuild needed.
* stream is VFR: ~2 fps static, 10 fps on motion - the detector is
  effectively motion-conditional, which is what you want for a counter.

## ops

    make logs                       # journal follow
    lxc exec core:camagent -- journalctl -u detector --since today | grep cat_detection | wc -l
    lxc exec core:camagent -- du -sh /media/detector/events
