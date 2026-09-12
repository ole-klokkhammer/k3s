# query - camera query agent (in the camagent LXC)

`POST /query {question}` -> natural-language answer about the camera
system. The LLM (Gemma on the 5090 llm LXC, OpenAI-compatible endpoint)
understands the question and picks tools; this service executes them
locally and feeds results back (up to 4 tool rounds):

| tool            | answers                                    | backend                     |
|-----------------|--------------------------------------------|-----------------------------|
| count_events    | "how many times did the cat walk by?"      | postgres (surveillance.events) |
| recent_events   | "what's the latest activity?"               | postgres                    |
| search_stills   | "find frames of a cat at the door"         | embedder /embed -> pgvector |
| get_clip        | "play the clip from 15:00"                 | mediamtx LXC :9996          |
| list_recordings | "what's recorded today?"                   | mediamtx LXC :9996/list     |
| vision_check    | "is anyone in the livingroom right now?"   | ai-utils LXC VL model (optional) |

examples:

    curl -s localhost:8100/query -H 'content-type: application/json' \
         -d '{"question": "how many times did the cat walk by today?"}'
    curl -s localhost:8100/query -H 'content-type: application/json' \
         -d '{"question": "is anyone in the livingroom right now?"}'

the "how many cats" path is a plain SQL COUNT (fast, no LLM inference for
the math - the LLM just phrases it). "anyone in the livingroom" routes to
vision_check: latest still -> VL model on the ai-utils LXC. (Adding a
`person` class to the detector would give the same answer from events
alone, without the vision call.)

## requirements

- LLM server with OpenAI tool-calling enabled (see query.env.example)
- embedder running in this LXC (8101), mediamtx LXC reachable (:9996)
- postgres schema deployed (../../sql/schema.sql)
- port 8100: LAN/mgmt only (ufw)

deploy:

    cd podman && make image && make deploy
