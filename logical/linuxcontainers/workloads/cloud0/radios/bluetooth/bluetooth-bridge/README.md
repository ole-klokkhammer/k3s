# Bluetooth Bridge

## Run with Nomad

If you keep Bluetooth isolated in its own LXC but run a Nomad client inside that LXC, the bridge can run as a normal Nomad service pinned to Bluetooth-capable nodes.

The Nomad path in this directory is:

- `Dockerfile`
- `job.hcl`
- `make build`
- `make push`
- `make deploy-nomad`
- `make status`
- `make logs`

The job is constrained to nodes with `meta.bluetooth = "true"` and mounts the host DBus socket so the container can talk to BlueZ inside the Bluetooth LXC.

That is the cleaner long-term option if you want Nomad to own lifecycle and health checks while still keeping Bluetooth isolated from Zigbee and other hardware domains.

## Functional health

The bridge application already publishes MQTT lifecycle state on `bluetooth/state/bridge` using a retained message and MQTT last will. That gives you a second signal beyond systemd:

- `online` when the bridge starts successfully
- `offline` when the MQTT session drops unexpectedly

That topic is useful for alerting, but it still does not prove scans are succeeding. If you want stronger health checking, add one of these next:

1. A local HTTP `/health` endpoint.
2. A periodic heartbeat topic with a timestamp.
3. A last-successful-scan timestamp and stale-data alert.

The bridge now exposes a basic `/health` endpoint that reports MQTT connectivity so Nomad or any other monitor can probe it directly.

## Useful commands

```bash
make status
make logs
make stop
```