# BTHome Processor

Decodes BTHome v2 sensor advertisements from Bluetooth scan results.

## Architecture

```
[bluetooth-bridge] → bluetooth/state/scan/devices
                            ↓
                    [bthome-processor] subscribes
                            ↓
                    bthome/state/{address}/{measurement}
```

## Topics

### Subscribed
- `bluetooth/state/scan/devices` - Scan results from bluetooth-bridge

### Published
- `bthome/state/processor` - "online"/"offline" (LWT)
- `bthome/state/{address}/{measurement}` - Individual measurement values (retained)
- `homeassistant/sensor/{unique_id}/config` - HA MQTT Discovery (when enabled)

## Output Format

Each measurement is published to its own topic:

```
bthome/state/A4_C1_38_AA_BB_CC/temperature
bthome/state/A4_C1_38_AA_BB_CC/humidity
bthome/state/A4_C1_38_AA_BB_CC/battery
```

Payload:
```json
{
  "value": 23.45,
  "unit": "°C",
  "address": "A4:C1:38:AA:BB:CC",
  "name": "ATC_AABBCC",
  "rssi": -65
}
```

## Supported Devices

Any device broadcasting BTHome v2 format (UUID: `fcd2`):
- Xiaomi sensors with PVVX/ATC firmware
- Shelly BLU sensors
- Custom ESP32 sensors
- DIY sensors

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MQTT_BROKER` | `hivemq.home.lan` | MQTT broker hostname |
| `LOG_LEVEL` | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR) |
| `HA_DISCOVERY` | `true` | Enable Home Assistant MQTT auto-discovery |

## Home Assistant Integration

When `HA_DISCOVERY=true`, the processor publishes MQTT discovery messages to `homeassistant/sensor/...`. 
Home Assistant will automatically create sensor entities for each measurement.

Entities appear under **Settings → Devices & Services → MQTT** with names like:
- `sensor.bthome_a4c138aabbcc_temperature`
- `sensor.bthome_a4c138aabbcc_humidity`

## Deployment

Can run anywhere with MQTT access - no Bluetooth required:
- Nomad job
- Docker container
- k3s pod

## Flashing Xiaomi LYWSD03MMC with PVVX Firmware

Stock Xiaomi firmware uses encrypted MiBeacon data. Flash PVVX custom firmware to broadcast unencrypted BTHome v2 data.

> **Note**: There are two custom firmwares - **ATC1441** (older) and **PVVX** (recommended). Use PVVX for better BTHome support.

### Requirements
- Chrome/Edge browser with Web Bluetooth support
- Linux: Enable Chrome flags:
  - `chrome://flags/#enable-web-bluetooth` - Required for Bluetooth access
  - `chrome://flags/#enable-experimental-web-platform-features` - Required to read device MAC address

### Important: Stock Firmware Compatibility

⚠️ **Some stock firmware versions don't support the activation exploit.**

If activation fails with "requires registration" or similar errors:

1. Install the **Xiaomi Home** app
2. Add the device to the app
3. Update to stock firmware `2.1.1_0159` via the app
4. Then retry the PVVX flash

> Note: Many devices work without this step. Only update stock firmware if activation fails.

### Steps

1. **Download PVVX firmware**:
   - Go to: https://github.com/pvvx/ATC_MiThermometer/releases
   - Download the latest release `.zip` file
   - Extract and find the `bin` folder
   - Select: `ATC_vXX_LYWSD03MMC.bin` (for your device with MAC `A4:C1:38:*`)

   **Firmware files by device:**
   | MAC Prefix | Device | Firmware |
   |------------|--------|----------|
   | `A4:C1:38` | LYWSD03MMC | `ATC_vXX_LYWSD03MMC.bin` |
   | `58:2D:34` | MJWSD05MMC | `ATC_vXX_MJWSD05MMC.bin` |
   | Other | Check device label | Match to firmware name |

2. **Open the web flasher** (Chrome/Edge only):
   ```bash
   google-chrome-stable --enable-features=WebBluetooth https://pvvx.github.io/ATC_MiThermometer/TelinkMiFlasher.html
   ```

3. **Connect to device**:
   - Click **"Connect"**
   - Select your `LYWSD03MMC` device
   - Click **"Pair"** if prompted

4. **Activate device** (first time only):
   - Click **"Do Activation"** - unlocks device for flashing
   - Wait for "Activation successful"

5. **Flash firmware**:
   - Click **"Open"** or **"Choose File"** button
   - Select the `.bin` file you downloaded (e.g., `ATC_v47_LYWSD03MMC.bin`)
   - Click **"Start Flashing"**
   - Wait 1-2 minutes for completion
   - Device LCD may flicker during flash

6. **Configure device** (after flashing):
   - https://pvvx.github.io/ATC_MiThermometer/TelinkMiFlasher.html
   - Click **"Connect"** again
   - Select the renamed device (`ATC_XXXXXX` or `PVVX_XXXXXX`)
   - Set the following options:
     - **Advertising Type**: `BTHome v2` ← Important!
     - **Advertising Interval**: `2500ms` (battery/responsiveness balance)
     - **RF TX Power**: `-3.7 dB` (saves battery)
   - Click **"Send Config"**

8. **Rename device** (optional):
   - Enter a friendly name (e.g., `TH_Living`)
   - Click **"Set Name"**

### Verify

Trigger a scan and check for BTHome data:
```bash
# Trigger scan
mosquitto_pub -h hivemq.home.lan -t "bluetooth/command/scan" -m ""

# Watch for decoded data
mosquitto_sub -h hivemq.home.lan -t "bthome/state/bthome/#" -v
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| "requestDevice" error | Use Chrome/Edge, not Firefox. Enable `chrome://flags/#enable-web-bluetooth` |
| Device not found | Ensure Bluetooth is on, device is nearby, battery is fresh |
| Activation fails | Update to stock firmware `2.1.1_0159` via Xiaomi Home app first |
| "Requires registration" error | Device needs stock firmware update before exploit works |
| Config options missing | Reconnect after flashing - device name changes to `ATC_*` |
| Flashing fails | Refresh page, try again. Keep device within 1m of computer |
| Wrong values (opening/power) | Wrong firmware variant. Re-flash with correct `*_LYWSD03MMC.bin` file |
| ATC1441 firmware issues | Flash PVVX firmware instead (download `.bin` manually) |
| No "Custom Firmware" button | Click "Open" or "Choose File" after connecting to load `.bin` manually |
| Connection fails | Go to `chrome://bluetooth-internals`, forget device, restart Chrome |

---

## Flashing Zigbee Firmware (Alternative)

For better battery life and reliability, you can flash Zigbee firmware instead of BLE/BTHome.

### Comparison

| Firmware | Battery Life | Requirements | Pros | Cons |
|----------|--------------|--------------|------|------|
| PVVX BLE (BTHome) | 6-12 months | bluetooth-bridge | Simple setup | Constant advertising drains battery |
| PVVX Zigbee | 1-2 years | Zigbee coordinator | Sleep mode, mesh network | Needs Zigbee2MQTT/ZHA |

### Requirements
- PVVX BLE firmware already installed (or stock firmware)
- Zigbee coordinator (Zigbee2MQTT, ZHA, deCONZ)

### Steps

1. **Download Zigbee firmware**:
   - Go to: https://github.com/pvvx/ZigbeeTLc/releases
   - Download the latest release
   - Find `Z03MMC` file in the `bin` folder (for LYWSD03MMC)

2. **Flash via OTA**:
   - Open: https://pvvx.github.io/ATC_MiThermometer/TelinkMiFlasher.html
   - Connect to your `ATC_*` device
   - Click **"Open"** and select the Zigbee `.bin` file
   - Click **"Start Flashing"**
   - Wait for completion

3. **Pair with Zigbee coordinator**:
   - Enable pairing mode on your coordinator
   - Device auto-joins after flashing
   - If not: hold reset contact for **7 seconds** to trigger pairing

### Button Actions (reset contact on LYWSD03MMC)

| Action | Result |
|--------|--------|
| Short press | Send temp/humidity/battery immediately |
| Hold 2 sec | Toggle °C / °F |
| Hold 7 sec | Reset bindings, wait for re-pairing |
| Hold 15 sec | Factory reset all settings |

### Reverting to BLE

Use Zigbee OTA with BLE firmware files from:
https://github.com/pvvx/ATC_MiThermometer/tree/master/zigbee_ota

---

### Flashed Devices

| Device ID | Location | Name |
|-----------|----------|------|
| ATC_F3C249 | main batroom | |
|  | main batroom | |