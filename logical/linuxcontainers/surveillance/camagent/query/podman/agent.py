#!/usr/bin/env python3
"""Camera query agent.

POST /query {question} -> natural-language answer about the camera system.
The LLM (OpenAI-compatible endpoint, typically Gemma on the 5090 llm LXC)
understands the question and picks tools; this service executes the tool
calls and feeds results back:

  count_events     - SQL count over surveillance.events
  recent_events    - latest matching events
  search_stills    - pgvector similarity (text embedded via the local embedder)
  get_clip         - mediamtx playback URL (mediamtx LXC)
  list_recordings  - mediamtx VOD listing (mediamtx LXC)
  vision_check     - optional: latest still -> VL model on the ai-utils LXC

All config is environment - see query.env.example.
"""
import base64
import json
import logging
import os
import sys
import time

import httpx
import psycopg2
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel


def env(name, default=''):
    return os.environ.get(name, default)


PORT         = int(env('QUERY_PORT', '8100'))
LLM_BASE     = env('QUERY_LLM_BASE_URL', 'http://llm.home.lan:8000/v1').rstrip('/')
LLM_MODEL    = env('QUERY_LLM_MODEL', 'gemma-4-31b-it')
LLM_KEY      = env('QUERY_LLM_API_KEY')
PG_DSN       = env('QUERY_PG_DSN', '')
EMBED_URL    = env('QUERY_EMBED_URL', 'http://127.0.0.1:8101').rstrip('/')
MEDIAMTX     = env('QUERY_MEDIAMTX', 'http://mediamtx.homelan:9996').rstrip('/')
VISION_URL   = env('QUERY_VISION_URL')
VISION_MODEL = env('QUERY_VISION_MODEL')
MAX_ROUNDS   = int(env('QUERY_MAX_ROUNDS', '4'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', stream=sys.stdout)
log = logging.getLogger('query')

# --- postgres ---------------------------------------------------------------
pg = {'conn': None}


def sql(query, params=()):
    """Run a query; retry for up to 1 min while postgres is unreachable."""
    for _ in range(30):
        try:
            if pg['conn'] is None:
                pg['conn'] = psycopg2.connect(PG_DSN, autocommit=True)
            cur = pg['conn'].cursor()
            cur.execute(query, params)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
        except Exception as e:
            log.warning('postgres unavailable (%s); retry in 2s', e)
            pg['conn'] = None
            time.sleep(2)
    return []


# --- tools ------------------------------------------------------------------
def count_events(cls=None, camera=None, since_hours=None):
    q, params = 'SELECT count(*) AS n FROM surveillance.events', []
    if cls:
        q += ' WHERE class = %s'
        params.append(cls)
    if camera:
        q += (' AND' if cls else ' WHERE') + ' camera = %s'
        params.append(camera)
    if since_hours:
        q += (' AND' if (cls or camera) else ' WHERE') +             " ts >= now() - (%s || ' hours')::interval"
        params.append(str(since_hours))
    return sql(q, params)[0]['n']


def recent_events(cls=None, camera=None, limit=20):
    q, params = ('SELECT ts, camera, class, conf, still_path '
                 'FROM surveillance.events'), []
    if cls:
        q += ' WHERE class = %s'
        params.append(cls)
    if camera:
        q += (' AND' if cls else ' WHERE') + ' camera = %s'
        params.append(camera)
    q += ' ORDER BY ts DESC LIMIT %s'
    params.append(int(limit))
    return sql(q, params)


def search_stills(text, top_k=5):
    r = httpx.post(f'{EMBED_URL}/embed', json={'text': text}, timeout=60)
    vec = r.json()['vector']
    qstr = '(' + ','.join(f'{v:.6f}' for v in vec) + ')'
    return sql(
        'SELECT still_path, camera, ts, '
        'round(1 - (embedding <=> %s::vector), 3) AS similarity '
        'FROM surveillance.events WHERE embedding IS NOT NULL '
        'ORDER BY embedding <=> %s::vector LIMIT %s',
        (qstr, qstr, int(top_k)))


def get_clip(camera, start, duration=60):
    url = (f'{MEDIAMTX}/get?path={camera}&start={start}'
           f'&duration={int(duration)}&format=mp4')
    return {'url': url,
            'note': 'http URL on the mediamtx LXC - fetch from a network its ufw allows'}


def list_recordings(camera, start=None):
    u = f'{MEDIAMTX}/list?path={camera}' + (f'&start={start}' if start else '')
    return httpx.get(u, timeout=60).json()


def vision_check(camera, prompt='Describe this camera frame. Is a person present?'):
    if not VISION_URL:
        return {'error': 'vision_check disabled: set QUERY_VISION_URL'}
    rows = sql('SELECT still_path FROM surveillance.events '
               'WHERE camera = %s AND still_path IS NOT NULL '
               'ORDER BY ts DESC LIMIT 1', (camera,))
    if not rows or not os.path.exists(rows[0]['still_path']):
        return {'error': f'no recent still found for {camera}'}
    still = rows[0]['still_path']
    b64 = base64.b64encode(open(still, 'rb').read()).decode()
    headers = {'Content-Type': 'application/json'}
    if LLM_KEY:
        headers['Authorization'] = f'Bearer {LLM_KEY}'
    r = httpx.post(f'{VISION_URL.rstrip("/")}/chat/completions', headers=headers,
                   json={'model': VISION_MODEL,
                         'max_tokens': 300,
                         'messages': [{'role': 'user', 'content': [
                             {'type': 'text', 'text': prompt},
                             {'type': 'image_url',
                              'image_url': {'url': f'data:image/jpeg;base64,{b64}'}}]}]},
                   timeout=180)
    return {'camera': camera, 'still': still,
            'answer': r.json()['choices'][0]['message']['content']}


DISPATCH = {
    'count_events': count_events,
    'recent_events': recent_events,
    'search_stills': search_stills,
    'get_clip': get_clip,
    'list_recordings': list_recordings,
    'vision_check': vision_check,
}

TOOLS = [
    {'type': 'function', 'function': {
        'name': 'count_events',
        'description': 'Count detection events, optionally filtered by object class '
                       '(e.g. cat, person), camera, and time window in hours.',
        'parameters': {'type': 'object', 'properties': {
            'class': {'type': 'string'},
            'camera': {'type': 'string'},
            'since_hours': {'type': 'number',
                           'description': 'only events this many hours back from now'}}}}},
    {'type': 'function', 'function': {
        'name': 'recent_events',
        'description': 'Latest matching detection events (timestamps, class, '
                       'confidence, still path).',
        'parameters': {'type': 'object', 'properties': {
            'class': {'type': 'string'},
            'camera': {'type': 'string'},
            'limit': {'type': 'integer'}}}}},
    {'type': 'function', 'function': {
        'name': 'search_stills',
        'description': 'Semantic search over recorded stills: find frames similar '
                       'to a text description (e.g. "cat at the front door").',
        'parameters': {'type': 'object', 'properties': {
            'text': {'type': 'string'},
            'top_k': {'type': 'integer'}},
            'required': ['text']}}},
    {'type': 'function', 'function': {
        'name': 'get_clip',
        'description': 'Build a playback URL for a recorded clip (RFC3339 start time).',
        'parameters': {'type': 'object', 'properties': {
            'camera': {'type': 'string'},
            'start': {'type': 'string',
                      'description': 'RFC3339, e.g. 2026-09-12T15:00:00Z'},
            'duration': {'type': 'integer', 'description': 'seconds', 'default': 60}},
            'required': ['camera', 'start']}}},
    {'type': 'function', 'function': {
        'name': 'list_recordings',
        'description': 'List recorded segments for a camera (mediamtx VOD server).',
        'parameters': {'type': 'object', 'properties': {
            'camera': {'type': 'string'},
            'start': {'type': 'string'}},
            'required': ['camera']}}},
    {'type': 'function', 'function': {
        'name': 'vision_check',
        'description': 'Ask a vision model about the most recent still from a camera. '
                       'Use for "right now / live" questions like "is anyone in the livingroom".',
        'parameters': {'type': 'object', 'properties': {
            'camera': {'type': 'string'},
            'prompt': {'type': 'string'}},
            'required': ['camera']}}},
]

SYSTEM = ('You answer questions about a home camera system. Use the tools for facts '
          '(counts, recent events, similar stills, clips) and answer concisely. '
          'For "right now / live" questions use vision_check when available. '
          'If a fact cannot be established, say so instead of guessing.')


def dispatch(name, args):
    if name in ('count_events', 'recent_events'):
        args = {'cls': args.pop('class', None), **args}
    fn = DISPATCH.get(name)
    if fn is None:
        return {'error': f'unknown tool {name}'}
    try:
        return fn(**args)
    except TypeError as e:
        return {'error': f'bad args for {name}: {e}'}
    except Exception as e:
        return {'error': f'{name} failed: {e}'}


def llm_chat(messages):
    headers = {'Content-Type': 'application/json'}
    if LLM_KEY:
        headers['Authorization'] = f'Bearer {LLM_KEY}'
    r = httpx.post(f'{LLM_BASE}/chat/completions', headers=headers, timeout=300,
                   json={'model': LLM_MODEL, 'messages': messages, 'tools': TOOLS})
    r.raise_for_status()
    return r.json()


def answer(question):
    messages = [{'role': 'system', 'content': SYSTEM},
                {'role': 'user', 'content': question}]
    trace = []
    for _ in range(MAX_ROUNDS):
        msg = llm_chat(messages)['choices'][0]['message']
        tcs = msg.get('tool_calls')
        if not tcs:
            return msg.get('content') or '', trace
        messages.append(msg)
        for tc in tcs:
            name = tc['function']['name']
            args = json.loads(tc['function'].arguments or '{}')
            out = dispatch(name, args)
            trace.append({'tool': name, 'args': args, 'result': out})
            log.info('tool %s %s -> %s', name, args, json.dumps(out)[:200])
            messages.append({'role': 'tool', 'tool_call_id': tc['id'],
                             'content': json.dumps(out)})
    return 'reached max tool rounds; no final answer', trace


# --- http -------------------------------------------------------------------
app = FastAPI(title='camera query agent')


class Q(BaseModel):
    question: str


@app.post('/query')
def query(q: Q):
    a, trace = answer(q.question)
    return {'question': q.question, 'answer': a, 'tools': trace}


@app.get('/healthz')
def healthz():
    return {'ok': True, 'llm': LLM_BASE, 'model': LLM_MODEL,
            'embedder': EMBED_URL, 'mediamtx': MEDIAMTX,
            'vision': bool(VISION_URL), 'max_rounds': MAX_ROUNDS}


if __name__ == '__main__':
    log.info('query agent on :%d (llm=%s model=%s)', PORT, LLM_BASE, LLM_MODEL)
    uvicorn.run(app, host='0.0.0.0', port=PORT)
