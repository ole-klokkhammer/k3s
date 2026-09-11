# go2rtc

## setup 

### storage
sudo zfs create ssd/appdata/go2rtc
 
### lxc 
- lxc profile create go2rtc
- lxc profile edit go2rtc
- lxc launch ubuntu:24.04 go2rtc -p default -p go2rtc
- lxc exec go2rtc -- bash 
 

### install

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


### access
http://go2rtc.homelan:1984