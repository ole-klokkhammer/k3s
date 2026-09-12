#!/usr/bin/env python3
"""Camera object detector.

Consumes a mediamtx re-served RTSP stream (TCP), runs GPU YOLO detection
on a down-resampled frame, and raises "cat" events:

  * JSON event lines to stdout (journal)
  * throttled stills into DETECTOR_EVENT_DIR
  * auto-reconnect on stream loss (backoff, capped)

All config is environment (podman quadlet EnvironmentFile) - see
detector.env.example.
"""
import json
import logging
import os
import sys
import time
from collections import deque

def env(name, default, cast=str):
    v = os.environ.get(name)
    return cast(v) if v not in (None, '') else cast(default)

RTSP_URL      = env('DETECTOR_RTSP_URL', 'rtsp://127.0.0.1:8554/entrance_roof')
INPUT_SIZE    = env('DETECTOR_INPUT_SIZE', 1280, int)     # downscale longest edge
CONF          = env('DETECTOR_CONF', 0.5, float)
DEVICE        = env('DETECTOR_DEVICE', 'cuda:0')
MODEL         = env('DETECTOR_MODEL', '/models/yolo11m.pt')
EVENT_DIR     = env('DETECTOR_EVENT_DIR', '/media/detector/events')
STILL_EVERY   = env('DETECTOR_STILL_EVERY', 10, int)      # seconds between stills
CAT_CLASS     = env('DETECTOR_CAT_CLASS', 15, int)        # COCO cat id
LOG_EVERY     = env('DETECTOR_LOG_EVERY', 60, int)        # heartbeat interval
BURST_WINDOW  = 2.0                                        # seconds
BURST_COUNT   = 3                                          # detections in window => event

# must be set BEFORE cv2.VideoCapture opens the stream (ffmpeg backend)
os.environ.setdefault('OPENCV_FFMPEG_CAPTURE_OPTIONS', 'rtsp_transport;tcp')

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', stream=sys.stdout)
log = logging.getLogger('detector')

def open_stream():
    import cv2
    cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)   # avoid buffering a pile of stale frames
    return cap

def main():
    import cv2
    from ultralytics import YOLO

    log.info('loading model %s on %s', MODEL, DEVICE)
    model = YOLO(MODEL)
    # one warm-up inference: loads weights to the GPU, compiles paths
    import numpy as np
    dummy = np.zeros((INPUT_SIZE, INPUT_SIZE, 3), dtype=np.uint8)
    model(dummy, conf=CONF, classes=[CAT_CLASS], device=DEVICE, verbose=False)
    log.info('model ready; watching %s (input %spx, conf %.2f)', RTSP_URL, INPUT_SIZE, CONF)

    cap = open_stream()
    backoff, fails = 1, 0
    bursts = deque()            # timestamps of detections (for event dedupe)
    last_still, last_log = 0.0, 0.0
    n_frames, t_start = 0, time.time()

    while True:
        ok, frame = cap.read()
        if not ok:
            fails += 1
            log.warning('stream read failed (fail %d); reconnecting in %ds', fails, backoff)
            cap.release()
            time.sleep(backoff)
            backoff = min(backoff * 2, 30)
            cap = open_stream()
            fails = 0
            continue

        # downscale longest edge to INPUT_SIZE (2560 -> 1280 by default)
        h, w = frame.shape[:2]
        scale = INPUT_SIZE / max(h, w)
        if scale < 1.0:
            frame = cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

        now = time.time()
        res = model(frame, conf=CONF, classes=[CAT_CLASS], device=DEVICE, verbose=False)[0]
        det = res.boxes
        n_det = 0 if det is None else len(det)
        if n_det:
            confs = [float(c) for c in det.conf]
            bursts.append(now)
            while now - bursts[0] > BURST_WINDOW:
                bursts.popleft()
            if len(bursts) >= BURST_COUNT:   # burst: something persistent, log it
                i = int(det.conf.argmax())
                x1, y1, x2, y2 = [int(v) for v in det.xyxy[i]]
                best = float(det.conf[i])
                log.info(json.dumps({
                    'event': 'cat_detection', 'ts': now,
                    'dets': n_det, 'best_conf': round(best, 3),
                    'bbox': [x1, y1, x2, y2],
                    'fps': round(n_frames / max(now - t_start, 1), 1),
                }))
                if now - last_still >= STILL_EVERY:
                    os.makedirs(EVENT_DIR, exist_ok=True)
                    p = f"{EVENT_DIR}/cat_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
                    cv2.imwrite(p, frame)
                    log.info('still written %s', p)
                    last_still = now
        n_frames += 1
        if now - last_log >= LOG_EVERY:
            log.info('heartbeat: frames=%d fps=%.2f last_dets=%d stream_ok=1',
                     n_frames, n_frames / max(now - t_start, 1), n_det)
            last_log = now

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
