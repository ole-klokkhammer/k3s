# surveillance

camera NVR stack, split across two LXCs + external services:

| folder                 | what                                          | where                    |
|------------------------|-----------------------------------------------|--------------------------|
| `mediamtx/`            | mediamtx: camera ingest, recording, playback  | `core:mediamtx` - new, unprivileged, CPU-only |
| `camagent/`        | movement (YOLO cat detection) + embedder + nats + query agent | `core:camagent` - 5060 Ti, GPU/CDI |
| `sql/`                 | postgres schema: events + pgvector            | `core:postgres` LXC      |
| `agent/podman-registry/` | in-LXC registry + login helper              | both LXCs                |

## data flow

    camera -> mediamtx LXC (ingest + record + re-serve)
               -> camagent LXC:
                    movement  YOLO cat events + stills (/media/detector/events)
                    embedder  stills -> CLIP vectors -> postgres (pgvector) + NATS
                    query     POST /query "how many cats today?"
                              -> tools (postgres / embedder / mediamtx playback /
                                 optional ai-utils vision) -> LLM (gemma on 5090) -> answer

## conventions

quadlets at /etc/containers/systemd/<name>.container, config in /config/<name>
(SSD pool), data in /media/<name> (HDD pool), secrets in
/env/surveillance/<name>.env (never in git).

see `mediamtx/README.md` and `camagent/README.md` for LXC setup.
