# mediamtx

RTSP/SRT/WebRTC ingest + recording for all cameras. Pulls RTSP straight
from the cameras (go2rtc is not in this chain) and is the single source
of truth for the detector. CPU-only: no GPU here, the GPU is left for
the detector.

## ports

| proto   | port | what                       |
| ------- | ---- | -------------------------- |
| rtsp     | 8554 | camera ingest / stream out |
| hls      | 8888 | hls re-serve               |
| rtmp     | 1935 | rtmp                       |
| srt      | 8890 | srt                        |
| webrtc   | 8889 | live viewing               |
| api      | 9997 | REST                       |
| metrics  | 9998 | prometheus                 |
| playback | 9996 | recorded segments (http)   |

## setup

### storage (on core)

two datasets, both wired into the LXC profile (see profile.yaml):

    # config data (SSD) -> LXC /config
    sudo zfs create -o compression=lz4 -o atime=off -o xattr=sa -o acltype=posixacl -o recordsize=1M ssd/appdata/surveillance
    # recordings (HDD)   -> LXC /media
    sudo zfs create -o compression=lz4 -o atime=off -o xattr=sa -o acltype=posixacl -o recordsize=1M hdd/surveillance

the profile already maps both (config -> /config, media -> /media).
services keep their own subdirs: /config/mediamtx, /media/mediamtx
(recordings), /config/detector, ...

### quadlet

    # one time: create the recordings dir the quadlet mounts
    lxc exec surveillance -- mkdir -p /media/mediamtx

    # copy the camera credentials into place and deploy
    cd podman
    cp mediamtx.env.example mediamtx.env   # fill in the password (not committed)
    make deploy                             # renders config.yaml from mediamtx.env
    lxc exec surveillance -- systemctl enable mediamtx

    # or by hand inside the LXC:
    cp mediamtx.container /etc/containers/systemd/
    envsubst < config.yaml.tmpl > /config/mediamtx/config.yaml
    systemctl daemon-reload
    systemctl enable --now mediamtx

`make config` (and thus `make deploy`) is idempotent: it re-renders the
template every time, so after changing mediamtx.env or config.yaml just
run it and restart. (LXC needs `gettext-base` for envsubst:
`apt install -y gettext-base`.)

## smoke test (no camera needed)

add a throwaway path first (the config only serves the paths under
`paths:` - pushes to undefined paths are rejected):

    # in config.yaml, under paths:
    #   test: {}
    # then make deploy, and:
    ffmpeg -re -f lavfi -i testsrc2 -f rtsp rtsp://localhost:8554/test
    ffplay rtsp://localhost:8554/test

## playback (recorded footage)

playback: true in mediamtx.yml enables the built-in VOD server on :9996
(it is OFF by default in v1.x). It reads the recorded segments on disk,
seeks to the requested time, and re-muxes them on the fly:

    # list segments for a path (JSON: start/duration + download URL per entry)
    curl 'http://surveillance.homelan:9996/list?path=entrance_roof'
    curl 'http://surveillance.homelan:9996/list?path=entrance_roof&start=2026-09-12T15:00:00Z'

    # play a time range (RFC3339 start + duration in seconds).
    # format=mp4 -> one seekable MP4 (browser <video> / VLC / ffplay)
    ffplay 'http://surveillance.homelan:9996/get?path=entrance_roof&start=2026-09-12T15:00:00Z&duration=600&format=mp4'
    curl -o clip.mp4 'http://surveillance.homelan:9996/get?path=entrance_roof&start=2026-09-12T15:00:00Z&duration=600&format=mp4'

if the api auth is on, use the same credentials as :9997 (curl -u user:pass).
segments also live on disk, unmanaged: /media/mediamtx/recordings/<path>/
inside the LXC (host: /hdd/surveillance/mediamtx/recordings/<path>/) -
1s fmp4 parts, 1h segments, 7d retention (pathDefaults above).

## cameras

mediamtx pulls RTSP directly from each camera - one key per stream under
`paths:` in podman/config.yaml, sources are env-substituted from
mediamtx.env (see above). entrance_roof speaks the Reolink `Preview_01_*`
scheme (no /h264/1-style paths on that model):

    entrance_roof:      rtsp://...@192.168.10.28/Preview_01_main   (2560x2560 h264)
    entrance_roof_sub:  rtsp://...@192.168.10.28/Preview_01_sub   (1024x1024, for the detector)

main is VFR (Reolink drops to ~1-2 fps when the scene is static, ramps to
10 on motion) - recordings are sparse when nothing moves; that's normal.

the detector consumes mediamtx's re-served streams
(`rtsp://surveillance.homelan:8554/entrance_roof_sub`), NOT the camera -
Reolink allows only a handful of concurrent RTSP sessions.

add a camera: new CAMERA_* vars in mediamtx.env + a new key under
`paths:`, then `make deploy`.

## notes

- config is re-read on restart only; the committed config.yaml is a
  TEMPLATE - camera credentials come from mediamtx.env at deploy time
  (envsubst), never from git
- recordings land in /media/mediamtx (HDD pool) as 1h rolling chunks
- api/metrics are explicitly enabled (`api: true`, `metrics: true`) -
  they are OFF by default in mediamtx v1.x; the README's 9997/9998 ports
  only work because of those two lines
- the quadlet mounts /media/mediamtx (recordings) and /config/mediamtx
  (state) - neither path exists in the container without those lines
- open the RTSP/HTTP ports in ufw on the LXC if cameras/detector live elsewhere
- config validated against bluenviron/mediamtx v1.21 (current `latest`):
  recording keys live under `pathDefaults`, `recordPath` is a template
  that must contain %path + strftime fields, and `api`/`metrics` are
  off by default. If the image tag moves on, re-check these keys
  (consider pinning, e.g. bluenviron/mediamtx:1.21.0, if the
  auto-update timer ever bumps major schema changes)
