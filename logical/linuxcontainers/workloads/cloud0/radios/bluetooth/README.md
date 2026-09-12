# Bluetooth Workloads

Feature-oriented grouping for Bluetooth-related workloads.

- `bluetooth-bridge` handles Bluetooth scanning and publishes scan state to MQTT.
- `bthome` consumes Bluetooth scan state and decodes BTHome sensor payloads.

This keeps Bluetooth bridge and Bluetooth-derived processing in one place instead of splitting them across `bridges/` and `processors/`.