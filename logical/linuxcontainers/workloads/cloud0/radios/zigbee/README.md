# Zigbee Workloads

Feature-oriented grouping for Zigbee-related workloads.

This bucket holds Zigbee services and processors that run under Nomad while the dedicated Zigbee LXC keeps hardware isolation.

Current workloads:

- `zigbee2mqtt/` - Nomad-managed Zigbee2MQTT running inside the Zigbee LXC

The Zigbee appliance definitions still live under `logical/appliances/bridges/zigbee/` and remain responsible for USB passthrough, storage, and the Nomad client itself.