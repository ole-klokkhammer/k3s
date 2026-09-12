# mediamtx (core:mediamtx)

CPU-only, unprivileged LXC running mediamtx as a podman quadlet: camera
ingest + recording + playback API. No GPU - the 5060 Ti stays with the camagent LXC. No nesting/apparmor overrides: an unprivileged LXC is enough
for podman.

## services

| folder      | what                                                                              |
| ----------- | --------------------------------------------------------------------------------- |
| `mediamtx/` | RTSP/SRT/WebRTC ingest, recording, playback (:9996), API (:9997), metrics (:9998) |

## ports

| proto    | port | what                       |
| -------- | ---- | -------------------------- |
| rtsp     | 8554 | camera ingest / stream out |
| hls      | 8888 | hls re-serve               |
| rtmp     | 1935 | rtmp                       |
| srt      | 8890 | srt                        |
| webrtc   | 8889 | live viewing               |
| api      | 9997 | REST                       |
| metrics  | 9998 | prometheus                 |
| playback | 9996 | recorded segments (http)   |

## setup

### disk (on core)

    # config data (SSD) -> LXC /config (new dataset for this LXC)
    sudo zfs create -o compression=lz4 -o atime=off -o xattr=sa -o acltype=posixacl -o recordsize=1M ssd/appdata/mediamtx
    # recordings share the HDD pool with the camagent LXC (already created)
    # hdd/surveillance -> both LXCs' /media, per-service subdirs

### lxc

lxc profile import mediamtx/profile.yaml # or: lxc profile create mediamtx + edit
lxc launch ubuntu:24.04 mediamtx -p default -p mediamtx
lxc exec mediamtx -- bash

#### install podman

sudo apt update && sudo apt install -y podman systemd-container gettext-base
systemctl enable --now podman-auto-update.timer

no nvidia container toolkit - there is no GPU here.

## playback (recorded footage)

playback: true in mediamtx.yml enables the built-in VOD server on :9996
(OFF by default in v1.x). It reads the recorded segments on disk, seeks
to the requested time, and re-muxes them on the fly:

    # list segments for a path (JSON: start/duration + download URL per entry)
    curl 'http://mediamtx.homelan:9996/list?path=entrance_roof'
    curl 'http://mediamtx.homelan:9996/list?path=entrance_roof&start=2026-09-12T15:00:00Z'

    # play a time range (RFC3339 start + duration in seconds)
    ffplay 'http://mediamtx.homelan:9996/get?path=entrance_roof&start=2026-09-12T15:00:00Z&duration=600&format=mp4'
    curl -o clip.mp4 'http://mediamtx.homelan:9996/get?path=entrance_roof&start=2026-09-12T15:00:00Z&duration=600&format=mp4'

segments live on disk, unmanaged: /media/mediamtx/recordings/<path>/
inside the LXC (host: /hdd/surveillance/mediamtx/recordings/<path>/) -
1s fmp4 parts, 1h segments, 7d retention (pathDefaults in the config).

## cameras

mediamtx pulls RTSP directly from each camera - one key per stream under
`paths:`, sources env-substituted from mediamtx.env at deploy time.
entrance*roof speaks the Reolink `Preview_01*\*` scheme:

    entrance_roof:      rtsp://...@192.168.10.28/Preview_01_main   (2560x2560 h264)
    entrance_roof_sub:  rtsp://...@192.168.10.28/Preview_01_sub   (1024x1024, for the detector)

main is VFR (Reolink drops to ~1-2 fps when static, ramps to 10 on
motion) - recordings are sparse when nothing moves; that's normal.

add a camera: new CAMERA\_\* vars in mediamtx.env + a new key under
`paths:`, then `make deploy`.

## notes

- config is re-read on restart only; the committed config is a TEMPLATE -
  camera credentials come from mediamtx.env at deploy time (envsubst),
  never from git
- api/metrics are explicitly enabled (`api: true`, `metrics: true`) -
  they are OFF by default in mediamtx v1.x
- config validated against bluenviron/mediamtx v1.21: recording keys live
  under `pathDefaults`, `recordPath` is a template needing %path +
  strftime fields. Pin the image (e.g. bluenviron/mediamtx:1.21.0) if
  the auto-update timer may bump major schema changes
- the camagent LXC's movement detector consumes our re-served streams
  (`rtsp://mediamtx.homelan:8554/...`), NOT the cameras - Reolink allows
  only a handful of concurrent RTSP sessions
