#!/usr/bin/env python3
"""Camera-still embedder ("ai-utils" role in the camagent LXC).

Watches the movement detector's stills dir, embeds new stills with a CLIP
image encoder, stores the event row + vector in postgres (pgvector) and
publishes one NATS message per still.

Also serves POST /embed {text} so the query agent can embed search text
into the same vector space.

All config is environment (podman quadlet EnvironmentFile) - see
embedder.env.example.
"""
import glob
import json
import logging
import os
import re
import sqlite3
import sys
import threading
import time

import numpy as np


def env(name, default, cast=str):
    v = os.environ.get(name)
    return cast(v) if v not in (None, '') else cast(default)


POLL_DIR   = env('EMBEDDER_POLL_DIR', '/media/detector/events')
STATE_DB   = env('EMBEDDER_STATE_DB', '/config/embedder/state.db')
MODEL_ID   = env('EMBEDDER_MODEL', '/models/clip-vit-b32')
DEVICE     = env('EMBEDDER_DEVICE', 'cuda:0')
PORT       = env('EMBEDDER_PORT', 8101, int)
POLL_SECS  = env('EMBEDDER_POLL_SECS', 5, int)
CAMERA     = env('EMBEDDER_CAMERA', 'entrance_roof')
NATS_URL   = env('NATS_URL', 'nats://127.0.0.1:4222')
SUBJECT    = env('NATS_SUBJECT', 'surveillance.still')
PG_DSN     = env('PG_DSN', '')

# stills are named <class>_<YYYYMMDD>_<HHMMSS>.jpg (detector.py convention)
STILL_RE = re.compile(r'^(\w+)_(\d{8})_(\d{6})\.jpg$')

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', stream=sys.stdout)
log = logging.getLogger('embedder')

# --- model -----------------------------------------------------------------
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

model = CLIPModel.from_pretrained(MODEL_ID)
processor = CLIPProcessor.from_pretrained(MODEL_ID)
if DEVICE != 'cpu':
    model = model.half().to(DEVICE)
model.eval()


def _norm(f):
    return f / (float(np.linalg.norm(f)) + 1e-12)


def embed_image(path):
    img = Image.open(path).convert('RGB')
    inputs = processor(images=img, return_tensors='pt')
    if DEVICE != 'cpu':
        inputs = {k: (v.half().to(DEVICE) if torch.is_tensor(v) else v)
                  for k, v in inputs.items()}
    with torch.no_grad():
        f = model.get_image_features(**inputs)[0].float().cpu().numpy()
    return _norm(f)


def embed_text(text):
    inputs = processor(text=text, return_tensors='pt',
                       padding=True, truncation=True, max_length=77)
    with torch.no_grad():
        f = model.get_text_features(**inputs)[0].float().cpu().numpy()
    return _norm(f)


def vec_literal(v):
    return '(' + ','.join(f'{x:.6f}' for x in v) + ')'


# --- seen-state (sqlite) ----------------------------------------------------
def open_state():
    con = sqlite3.connect(STATE_DB)
    con.execute('CREATE TABLE IF NOT EXISTS seen '
                '(still_path TEXT PRIMARY KEY, embedded_at TEXT)')
    return con


state = open_state()


def mark_seen(path):
    state.execute('INSERT OR IGNORE INTO seen (still_path, embedded_at) '
                  'VALUES (?, ?)', (path, time.strftime('%Y-%m-%dT%H:%M:%S')))
    state.commit()


def seen_paths():
    return {r[0] for r in state.execute('SELECT still_path FROM seen')}


# --- postgres ---------------------------------------------------------------
pg = {'conn': None}


def pg_exec(query, params=()):
    """Run once, retrying for up to 2 min while postgres is unreachable."""
    import psycopg2
    for _ in range(60):
        try:
            if pg['conn'] is None:
                pg['conn'] = psycopg2.connect(PG_DSN, autocommit=True)
            cur = pg['conn'].cursor()
            cur.execute(query, params)
            return True
        except Exception as e:
            log.warning('postgres unavailable (%s); retry in 2s', e)
            pg['conn'] = None
            time.sleep(2)
    return False


def insert_event(ts_iso, cls, still, vec):
    return pg_exec(
        'INSERT INTO surveillance.events (ts, camera, class, still_path, embedding) '
        'VALUES (%s::timestamptz, %s, %s, %s, %s::vector)',
        (ts_iso, CAMERA, cls, still, vec_literal(vec)))


# --- nats -------------------------------------------------------------------
nc = None


def nats_pub(payload):
    global nc
    try:
        import nats as nats_lib
        if nc is None:
            nc = nats_lib.connect(NATS_URL)[0]
        nc.publish(SUBJECT.encode(), json.dumps(payload).encode())
    except Exception as e:
        log.warning('nats publish failed (%s); will retry next cycle', e)
        nc = None


# --- poller -----------------------------------------------------------------
def poll_once():
    known = seen_paths()
    for f in sorted(glob.glob(os.path.join(POLL_DIR, '*.jpg'))):
        if f in known:
            continue
        m = STILL_RE.match(os.path.basename(f))
        if not m:
            log.warning('skipping unparseable still %s', f)
            mark_seen(f)
            continue
        cls, d, t = m.group(1), m.group(2), m.group(3)
        ts_iso = f'{d[:4]}-{d[4:6]}-{d[6:8]}T{t[:2]}:{t[2:4]}:{t[4:6]}'
        vec = embed_image(f)
        if not insert_event(ts_iso, cls, f, vec):
            log.warning('postgres write failed for %s; leaving unmarked', f)
            continue
        mark_seen(f)
        nats_pub({'still': f, 'ts': ts_iso, 'camera': CAMERA, 'class': cls})
        log.info('embedded %s (%s @ %s)', os.path.basename(f), cls, ts_iso)


def poll_loop():
    while True:
        try:
            poll_once()
        except Exception:
            log.exception('poll cycle failed')
        time.sleep(POLL_SECS)


# --- http -------------------------------------------------------------------
from fastapi import FastAPI
from pydantic import BaseModel

import uvicorn

app = FastAPI(title='camera embedder')


class Emb(BaseModel):
    text: str


@app.post('/embed')
def embed(e: Emb):
    v = embed_text(e.text)
    return {'vector': [float(x) for x in v], 'dim': int(v.shape[0])}


@app.get('/healthz')
def healthz():
    return {'ok': True, 'model': MODEL_ID, 'device': DEVICE,
            'seen': len(seen_paths()), 'pg': bool(PG_DSN)}


if __name__ == '__main__':
    threading.Thread(target=poll_loop, daemon=True).start()
    log.info('embedder on :%d (poll %s every %ds, nats=%s)',
             PORT, POLL_DIR, POLL_SECS, NATS_URL)
    uvicorn.run(app, host='0.0.0.0', port=PORT)
