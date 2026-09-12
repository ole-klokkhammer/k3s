# torrent

## setup

### Disk
sudo zfs create -V 20G \
  -o volblocksize=16K \
  -o compression=lz4 \
  ssd/vm/torrent-zvol
sudo zfs set sync=disabled ssd/vm/torrent-zvol

### lxc 
lxc profile create torrent-vm
lxc profile edit torrent-vm
lxc launch ubuntu:24.04 torrent --vm -p default -p torrent-vm

lxc exec torrent -- sudo --login --user ubuntu
lsblk
sudo mkfs.ext4 /dev/sdb
sudo mkdir -p /torrent
sudo mount /dev/sdb /torrent

sudo blkid /dev/sdb
sudo nano /etc/fstab
UUID=<uuid-from-blkid> /torrent ext4 defaults 0 2

sudo umount /torrent
sudo mount -a
df -h /torrent

### installation
lxc exec unifi -- sudo --login --user ubuntu

#### wireguard
https://github.com/qdm12/gluetun-wiki/blob/main/setup/providers/protonvpn.md

https://github.com/qdm12/gluetun-wiki/blob/main/setup/advanced/wireguard.md

- VPN_PORT_FORWARDING_UP_COMMAND=/bin/sh -c 'wget -O- --post-data "json={\"listen_port\":{{PORT}},\"upnp\":false}" http://127.0.0.1:8080/api/v2/app/setPreferences'

#### apparmor
sudo apt update
sudo apt install apparmor apparmor-utils
sudo systemctl enable --now apparmor
sudo systemctl restart docker

#### nfs on media files

// on the host
sudo apt update
sudo apt install nfs-kernel-server
sudo systemctl enable nfs-server
sudo systemctl start nfs-server
 
sudo zfs set sharenfs="rw=@192.168.10.0/24,sync,no_subtree_check,anonuid=1000,anongid=1000" hdd/music
sudo zfs set sharenfs="rw=@192.168.10.0/24,sync,no_subtree_check,anonuid=1000,anongid=1000" hdd/media


// apply
sudo exportfs -ra
sudo systemctl restart nfs-kernel-server

// in the vm
sudo apt update
sudo apt install nfs-common

sudo mkdir -p /hdd/music
sudo mkdir -p /hdd/media

sudo nano /etc/fstab
---
core.home.lan:/hdd/media      /hdd/media      nfs  vers=4,hard,timeo=30,_netdev  0  0
core.home.lan:/hdd/music  /hdd/music  nfs  vers=4,hard,timeo=30,_netdev  0  0
---

#### qbittorrent
In qBittorrent WebUI, check these settings:

Tools -> Options -> Advanced -> Network Interface
Set it to Any interface.

Tools -> Options -> Advanced -> Optional IP address to bind to
Set it to All addresses.

Tools -> Options -> Connection -> Proxy Server
Set it to None.

Tools -> Options -> BitTorrent
For public torrents, make sure DHT, PeX, and Local Peer Discovery are enabled.

Tools -> Options -> Connection -> Listening Port
You can keep this equal to the forwarded port, but this is secondary to the bind/proxy settings.

#### traefik
traefik runs inside the docker stack (see `stack/TRAEFIK.md`). it proxies the web uis:

- http://qbittorrent.torrent.homelan
- http://radarr.torrent.homelan
- http://sonarr.torrent.homelan
- http://lidarr.torrent.homelan
- http://jackett.torrent.homelan
- http://jellyseerr.torrent.homelan

deploy with `make sync up` from `stack/`. dns in `stack/TRAEFIK.md`.
