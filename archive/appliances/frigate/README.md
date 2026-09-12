# frigate

## setup

### disk

sudo zfs create -o compression=lz4 -o atime=off -o xattr=sa -o acltype=posixacl -o recordsize=1M ssd/appdata/frigate

### lxc

lxc profile create frigate
lxc profile edit frigate
lxc launch ubuntu:24.04 frigate -p default -p frigate
lxc exec frigate -- bash

#### install podman

https://podman.io/docs/installation

sudo apt update && sudo apt install -y podman systemd-container 

enable auto update
systemctl enable --now podman-auto-update.timer
systemctl list-timers | grep podman-auto-update

#### nvidia container toolkit 
https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/cdi-support.html

sudo apt-get update && sudo apt-get install -y --no-install-recommends \
   ca-certificates \
   curl \
   gnupg2
  
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo sed -i -e '/experimental/ s/^#//g' /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update

export NVIDIA_CONTAINER_TOOLKIT_VERSION=1.20.0-1
  sudo apt-get install -y \
      nvidia-container-toolkit=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
      nvidia-container-toolkit-base=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
      libnvidia-container-tools=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
      libnvidia-container1=${NVIDIA_CONTAINER_TOOLKIT_VERSION}

sudo nvidia-ctk config --set nvidia-container-runtime.log-level=debug
sudo nvidia-ctk config --in-place \
    --set nvidia-container-runtime.log-level=debug
sudo nvidia-ctk config --in-place \
    --set nvidia-container-runtime.log-level=debug \
    --set nvidia-container-runtime.debug=/var/log/nvidia-container-runtime.log
sudo nvidia-ctk config --in-place \
    --set nvidia-container-runtime.runtimes=crun:runc


#### podman
https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/cdi-support.html
sudo systemctl enable --now nvidia-cdi-refresh.path
sudo systemctl enable --now nvidia-cdi-refresh.service
sudo nvidia-ctk cdi generate --output=/var/run/cdi/nvidia.yaml

##### clean up
rm /etc/cdi/.yaml
sudo nvidia-ctk cdi generate --output=/var/run/cdi/nvidia.yaml

##### test
podman run --rm --device nvidia.com/gpu=all \
  ghcr.io/blakeblackshear/frigate:stable-tensorrt \
  nvidia-smi -L

podman run --rm --device nvidia.com/gpu=all \
  ghcr.io/blakeblackshear/frigate:stable-tensorrt \
  python3 -c "
    import onnxruntime as ort
    print('providers:', ort.get_available_providers())
    import pycuda.autoinit  # or use torch if available
"

#### Fix DNS
  raw.lxc: |
    lxc.apparmor.profile = unconfined
    lxc.cap.drop =
  security.nesting: "true"

#### detector model
https://docs.frigate.video/configuration/object_detectors/#onnx-supported-models

podman build . --build-arg MODEL_SIZE=Medium --rm --output . -f- <<'EOF'
FROM python:3.12 AS build
RUN apt-get update && apt-get install --no-install-recommends -y libgl1 && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.10.4 /uv /bin/
WORKDIR /rfdetr
RUN uv pip install --system rfdetr[onnxexport] torch==2.8.0 onnx==1.19.1 transformers==4.57.6 onnxscript
ARG MODEL_SIZE
RUN python3 -c "from rfdetr import RFDETR${MODEL_SIZE}; x = RFDETR${MODEL_SIZE}(resolution=320); x.export(simplify=True)"
FROM scratch
ARG MODEL_SIZE
COPY --from=build /rfdetr/output/inference_model.onnx /rfdetr-${MODEL_SIZE}.onnx
EOF