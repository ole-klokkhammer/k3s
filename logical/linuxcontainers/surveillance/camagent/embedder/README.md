# embedder

The "ai-utils" role inside the camagent LXC: embeds movement stills
(CLIP ViT-B/32, fp16 on the 5060 Ti) into postgres
(`surveillance.events.embedding`, pgvector) and publishes one NATS message
per still. Also serves `POST /embed {text}` so the query agent can embed
search text into the same space.

- polls `/media/detector/events` (read-only mount) every 5s
- seen-state in `/config/embedder/state.db`; stills stay unmarked until
  the postgres write succeeds, so a DB outage never drops events
- model baked into the image (no runtime internet); swapping to another
  CLIP requires a matching `vector(N)` column + ivfflat rebuild
  (sql/schema.sql)
- VRAM budget: ~1.5GB next to the detector's YOLO (~1GB) on the shared
  5060 Ti - leave headroom for the ai-utils LXC which shares the card
- port 8101 is consumed on 127.0.0.1 only (query agent lives in this LXC);
  ufw keeps it closed to the WAN

deploy:

    cd podman && make image && make deploy
    lxc exec core:camagent -- journalctl -u embedder -f
