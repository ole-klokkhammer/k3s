# Zigbee2MQTT

Run Zigbee2MQTT as a Nomad-managed Docker workload inside the dedicated Zigbee LXC.

## Runtime model

- The Zigbee LXC owns USB passthrough and persistent storage.
- Docker runs inside the Zigbee LXC.
- Nomad runs inside the Zigbee LXC and manages the Zigbee2MQTT container.

## Job behavior

The Nomad job in this directory:

- pins the workload to nodes with `meta.zigbee = "true"`
- mounts `/opt/zigbee2mqtt/data` into `/app/data`
- passes through `/dev/ttyUSB0` as the coordinator device
- mounts `/run/udev` read-only
- exposes the frontend on port `8080`

## Commands

```bash
make deploy-nomad
make status
make logs
make stop
```

## Notes

If the coordinator path inside the Zigbee LXC is a stable `/dev/serial/by-id/...` path, prefer that over `/dev/ttyUSB0` and update `job.hcl` accordingly.

If the container starts but cannot talk to the adapter, the next place to adjust is Docker capabilities or privileged mode on the Zigbee Nomad client. Start with the minimal device mapping in this job before widening privileges.