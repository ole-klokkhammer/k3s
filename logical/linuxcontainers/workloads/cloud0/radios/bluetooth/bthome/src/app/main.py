"""
BTHome Processor - Decodes BTHome v2 sensor advertisements from bluetooth bridge scan results.

Subscribes to: bluetooth/state/scan/devices
Publishes to:  bthome/state/{address}/{measurement}
"""

import asyncio
import json
import logging
import os
from aiohttp import web
from aiomqtt import Client, Will
from logical.linuxcontainers.workloads.cloud0.radios.bluetooth.bthome.src.app.bthome import (
    decode,
)
from logical.linuxcontainers.workloads.cloud0.radios.bluetooth.bthome.src.app.constants import (
    BTHOME_UUID_SHORT,
)
from logical.linuxcontainers.workloads.cloud0.radios.bluetooth.bthome.src.app.integrations import (
    publish_discovery,
)

MQTT_BROKER = os.getenv("MQTT_BROKER", "hivemq.home.lan")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
HA_DISCOVERY = os.getenv("HA_DISCOVERY", "true").lower() == "true"
HEALTH_PORT = int(os.getenv("HEALTH_PORT", "8080"))

PREFIX = "bthome"
TOPIC_SCAN_DEVICES = "bluetooth/state/scan/devices"
STATE_PROCESSOR = f"{PREFIX}/state/processor"

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

mqtt_connected = False


async def health_handler(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "mqtt": mqtt_connected})


def find_service_data(device: dict, uuid_short: str) -> bytes | None:
    """Extract service data for a given UUID from device advertisement."""
    service_data = device.get("service_data", {})

    for uuid_str, data_hex in service_data.items():
        if uuid_short in uuid_str.lower():
            if isinstance(data_hex, str):
                return bytes.fromhex(data_hex)
            return data_hex

    return None


def decode_bthome_device(device: dict) -> dict | None:
    """
    Try to decode BTHome data from a device's advertisement.
    Returns decoded measurements or None if not a BTHome device.
    """
    service_data = find_service_data(device, BTHOME_UUID_SHORT)
    if not service_data:
        return None

    try:
        # Prepend UUID for decoder (service_data doesn't include it)
        full_data = bytes([0xD2, 0xFC]) + service_data
        measurements = decode(full_data)

        return {
            "protocol": "bthome",
            "name": device.get("name"),
            "address": device.get("address"),
            "rssi": device.get("rssi"),
            "measurements": [
                {"name": m.name, "value": m.value, "unit": m.unit} for m in measurements
            ],
        }
    except Exception as e:
        logger.debug(f"Failed to decode BTHome from {device.get('address')}: {e}")
        return None


async def publish_measurements(client, decoded: dict):
    """Publish each measurement to its own topic."""
    address = decoded["address"].replace(":", "_")
    base_topic = f"{PREFIX}/state/{address}"

    for measurement in decoded["measurements"]:
        name = measurement["name"].lower().replace(" ", "_")
        topic = f"{base_topic}/{name}"
        payload = {
            "value": measurement["value"],
            "unit": measurement["unit"],
            "address": decoded["address"],
            "name": decoded["name"],
            "rssi": decoded["rssi"],
        }
        await client.publish(topic, json.dumps(payload), retain=True)

    return base_topic


async def handle_scan_results(client, payload: str):
    """Process scan results and publish decoded sensor data."""
    try:
        devices = json.loads(payload)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in scan results: {e}")
        return

    logger.debug(f"Received {len(devices)} devices in scan results")

    count = 0
    for device in devices:
        decoded = decode_bthome_device(device)
        if decoded:
            count += 1
            base_topic = await publish_measurements(client, decoded)
            if HA_DISCOVERY:
                await publish_discovery(client, decoded, base_topic)
            logger.info(
                f"BTHome: {decoded['address']} - {len(decoded['measurements'])} measurements"
            )

    if count > 0:
        logger.info(f"Processed {count} BTHome devices from {len(devices)} total")
    else:
        logger.debug(f"No BTHome devices found in {len(devices)} devices")


async def run_processor():
    global mqtt_connected
    will = Will(STATE_PROCESSOR, payload="offline", retain=True)

    async with Client(MQTT_BROKER, will=will) as client:
        await client.publish(STATE_PROCESSOR, "online", retain=True)
        await client.subscribe(TOPIC_SCAN_DEVICES)
        mqtt_connected = True

        logger.info("BTHome Processor started...")
        logger.info(f"  Subscribed to: {TOPIC_SCAN_DEVICES}")
        logger.info(f"  HA Discovery: {HA_DISCOVERY}")

        try:
            async for message in client.messages:
                logger.debug(f"Received message on topic: {message.topic}")
                if message.topic.matches(TOPIC_SCAN_DEVICES):
                    payload = message.payload.decode() if message.payload else ""
                    asyncio.create_task(handle_scan_results(client, payload))
        finally:
            mqtt_connected = False


async def main():
    app = web.Application()
    app.router.add_get("/health", health_handler)
    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", HEALTH_PORT).start()
    logger.info(f"Health endpoint listening on 0.0.0.0:{HEALTH_PORT}")

    try:
        await run_processor()
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
