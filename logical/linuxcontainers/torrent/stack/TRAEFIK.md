# traefik

traefik runs as a docker service inside the torrent stack (`docker-compose.yaml`),
not as a quadlet - the torrent VM has docker, not podman. it is `network_mode: host`
so it binds :80 and :8081 directly on the VM (192.168.10.146).

the docker provider watches the VM docker socket and picks up the
`traefik.http.*` labels on each web UI container. backends point at the
host-published ports (gluetun publishes them to the VM).

## urls

| url | service | backend |
| --- | --- | --- |
| http://qbittorrent.torrent.homelan | qbittorrent | 127.0.0.1:8080 |
| http://radarr.torrent.homelan | radarr | 127.0.0.1:7878 |
| http://sonarr.torrent.homelan | sonarr | 127.0.0.1:8989 |
| http://lidarr.torrent.homelan | lidarr | 127.0.0.1:8686 |
| http://jackett.torrent.homelan | jackett | 127.0.0.1:9117 |
| http://jellyseerr.torrent.homelan | jellyseerr | 127.0.0.1:5055 |
| http://dashboard.torrent.homelan:8081 | traefik dashboard | 127.0.0.1:8081 |

notes:
- plain http, lan only - `.homelan` is not public, so no letsencrypt.
  (add a self-signed cert + 443 entrypoint later if you want tls, cf. auto.crt)
- dashboard port is 8081, because 8080 is already taken by the gluetun
  published qbittorrent webui port on the vm.
- flaresolverr is intentionally not proxied - the *arrs talk to it directly
  inside the shared gluetun netns.
- `exposedByDefault=false`: only labeled containers are exposed. gluetun itself
  stays hidden.

## deploy

from `logical/linuxcontainers/torrent/stack/`:

    make sync up   # push compose files to the vm, then recreate changed containers

`docker compose up -d` only recreates the containers whose config/labels
changed, so gluetun-vpn (and the vpn session) is left alone.

## pfsense dns (unbound custom options)

services - dns-resolver - custom options. `redirect` + a single apex record is
enough: it makes unbound answer any name under the zone with that record, so
all the `*.torrent.homelan` web uis resolve without per-host entries - same
form the core-cloud block uses:

local-zone: "torrent.homelan." redirect
local-data: "torrent.homelan. A 192.168.10.146"

(ip = the torrent vm's address; match it to whatever the vm actually has)

## ops

    make status        # service + containers
    make logs-traefik # traefik logs
