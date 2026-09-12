# camagent LXC (core:camagent)

GPU LXC (RTX 5060 Ti, CDI passthrough) running the detection + query
stack as podman quadlets. Existing LXC: rename `core:surveillance` -> `core:camagent` (`pct set <id> hostname camagent` on PVE + DNS) so the name matches this folder.
mediamtx moved out to the mediamtx LXC, everything else stays here.

## services

| folder              | what                                                       | unit       |
|---------------------|------------------------------------------------------------|------------|
| `movement/`         | YOLO cat detection on the re-served stream -> events + stills | detector |
| `embedder/`         | CLIP stills -> pgvector + NATS (the "ai-utils" role; LXC = camagent)       | embedder   |
| `nats/`             | NATS server, the surveillance event bus                     | nats       |
| `query/`            | camera query agent: POST /query, tools + LLM (on the 5090) | query      |
| `podman-registry/`  | in-LXC registry + login helper                              | -          |

## data flow

    camera -> mediamtx LXC (ingest + record + re-serve)
              -> movement: YOLO events + stills (/media/detector/events)
                 -> embedder: stills -> CLIP vectors -> postgres (pgvector) + NATS pub
                    -> query: NL question -> tools (postgres / embedder / mediamtx
                     playback / optional ai-utils vision) -> LLM (gemma on 5090) -> answer

the LLM never runs in this LXC: query calls the OpenAI-compatible
endpoint on the 5090 llm LXC. VRAM budget on the shared 5060 Ti:
YOLO ~1GB + CLIP ~1.5GB - leave headroom (the ai-utils LXC also shares
this card).

## storage (on core, shared with the mediamtx LXC)

    ssd/appdata/surveillance  -> /config   (config/<svc> per service)
    hdd/surveillance          -> /media    (media/detector/events, ...)
    ssd/appdata/env           -> /env      (surveillance/<svc>.env secrets, never in git)

## setup (new build - the LXC likely already has these)

### podman

sudo apt update && sudo apt install -y podman systemd-container gettext-base
systemctl enable --now podman-auto-update.timer

### nvidia container toolkit (CDI)

https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/cdi-support.html

sudo apt-get update && sudo apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg2

curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#' \
    | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo sed -i -e '/experimental/ s/^#//g' /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update

export NVIDIA_CONTAINER_TOOLKIT_VERSION=1.20.0-1
sudo apt-get install -y \
    nvidia-container-toolkit=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
    nvidia-container-toolkit-base=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
    libnvidia-container-tools=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
    libnvidia-container1=${NVIDIA_CONTAINER_TOOLKIT_VERSION}

sudo systemctl enable --now nvidia-cdi-refresh.path nvidia-cdi-refresh.service
sudo nvidia-ctk cdi generate --output=/var/run/cdi/nvidia.yaml

test:

    podman run --rm --device nvidia.com/gpu=all \
        docker.io/nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi -L

### ufw

    ufw default deny incoming
    ufw allow from <MGMT_IP> to any port 8100 proto tcp   # query agent
    # 8101 (embedder) and 4222 (nats) are consumed on 127.0.0.1 only - stay closed
    ufw enable

## deploy order

    sql:        psql -d surveillance -f sql/schema.sql      (postgres LXC)
    movement:   cd movement/podman && make image && make deploy
    nats:       cd nats/podman && make deploy
    embedder:   cd embedder/podman && make image && make deploy
    query:      cd query/podman && make image && make deploy

then: `lxc exec core:camagent -- systemctl enable detector nats embedder query`

## notes

- quadlets: /etc/containers/systemd/<svc>.container, deployed by each
  service's Makefile; images build inside the LXC and push to
  registry.linole.org
- movement details: movement/README.md; per-service notes in each folder's README
- image names are fully qualified: the LXC's registries.conf has no
  unqualified-search registries
