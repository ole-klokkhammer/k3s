# nats

NATS server for the surveillance event bus (podman quadlet in the camagent LXC,
host networking).

- subjects today: `surveillance.still` - published by the embedder, one
  message per embedded still: {still, ts, camera, class}. Later: the
  movement detector can publish `surveillance.event` for live (non-DB)
  consumers.
- client port 4222 (host network): consumed on 127.0.0.1 by this LXC's
  services; ufw default-deny keeps it off the WAN. monitor 8222 stays closed.

deploy: `cd podman && make deploy`

test (in the LXC):

    podman run --rm --network host docker.io/natsio/nats-box:latest \
        nats sub 'surveillance.still.*' -nats nats://127.0.0.1:4222
