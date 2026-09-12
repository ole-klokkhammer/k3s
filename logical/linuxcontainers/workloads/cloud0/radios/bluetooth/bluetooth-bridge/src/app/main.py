import asyncio
import dataclasses
import json
import logging
import os
from datetime import datetime, UTC
from aiohttp import web
from aiomqtt import Client, Will
from bluetooth import service as bt_service
import env

MQTT_BROKER = os.getenv("MQTT_BROKER", "hivemq.home.lan")

# Topic structure:
#   bluetooth/command/...  - Commands (subscribe)
#   bluetooth/event/...    - Events (publish, not retained)
#   bluetooth/state/...    - State (publish, retained)
#   bluetooth/error/...    - Errors (publish)
#
# Full tree:
#   bluetooth/
#   ├── command/
#   │   ├── scan
#   │   ├── {address}/connect
#   │   └── {address}/read/{characteristic}
#   ├── event/
#   │   ├── scan/complete
#   │   ├── connect/{address}
#   │   └── read/{address}/{characteristic}
#   ├── state/
#   │   ├── bridge                          # "online"/"offline" (LWT)
#   │   ├── scan/devices                    # Last scan results
#   │   ├── connect/{address}               # Last connect result (services/chars)
#   │   └── read/{address}/{characteristic} # Last read result
#   └── error/
#       ├── scan
#       ├── connect/{address}
#       └── read/{address}/{characteristic}

PREFIX = "bluetooth"

# Commands (subscribe to these)
CMD_SCAN = f"{PREFIX}/command/scan"
CMD_CONNECT = f"{PREFIX}/command/+/connect"
CMD_READ = f"{PREFIX}/command/+/read/+"

# State (retained)
STATE_BRIDGE = f"{PREFIX}/state/bridge"
STATE_SCAN_DEVICES = f"{PREFIX}/state/scan/devices"

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

HEALTH_PORT = int(os.getenv("HEALTH_PORT", "8080"))

mqtt_connected = False
last_message_at: str | None = None
last_scan_success_at: str | None = None


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


async def health_handler(request: web.Request) -> web.Response:
    status = "ok" if mqtt_connected else "degraded"
    return web.json_response(
        {
            "status": status,
            "mqtt": mqtt_connected,
            "last_message_at": last_message_at,
            "last_scan_success_at": last_scan_success_at,
        },
        status=200 if mqtt_connected else 503,
    )


async def handle_scan(client):
    """Handle scan command - publishes to state/scan/devices"""
    global last_scan_success_at
    logger.info("Scanning...")
    try:
        devices = await bt_service.scan(env.scan_timeout)
        await client.publish(STATE_SCAN_DEVICES, json.dumps(devices), retain=True)
        await client.publish(f"{PREFIX}/event/scan/complete", json.dumps({"count": len(devices)}))
        last_scan_success_at = utc_now()
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        await client.publish(f"{PREFIX}/error/scan", json.dumps({"error": str(e)}))


async def handle_connect(client, address):
    """Handle connect command - publishes device info to state/connect/{address}"""
    logger.info(f"Connecting to {address}...")
    state_topic = f"{PREFIX}/state/connect/{address}"
    event_topic = f"{PREFIX}/event/connect/{address}"
    error_topic = f"{PREFIX}/error/connect/{address}"
    try:
        response = await bt_service.connect(address, env.connect_timeout)
        if not response:
            logging.warning(f"No response received from {address}.")
            await client.publish(error_topic, json.dumps({"error": "No response"}))
        else:
            logging.info(f"Connected to {address} successfully.")
            device_info = dataclasses.asdict(response)
            await client.publish(state_topic, json.dumps(device_info), retain=True)
            await client.publish(event_topic, json.dumps({"status": "connected"}))
    except Exception as e:
        logger.error(f"Connect to {address} failed: {e}")
        await client.publish(error_topic, json.dumps({"error": str(e)}))


async def handle_read(client, address, characteristic, payload):
    """
    Handle read command - writes command to characteristic and reads notification response
    Expected payload:
    {
        "command": "01020304",  # hex string to write (required)
        "format_type": "<BBBB"  # struct format for expected response (optional)
    }
    """
    if not payload or not payload.get("command"):
        error_topic = f"{PREFIX}/error/read/{address}/{characteristic}"
        await client.publish(error_topic, json.dumps({
            "characteristic": characteristic,
            "error": "Missing 'command' in payload"
        }))
        return
        
    command_hex = payload.get("command")
    format_type = payload.get("format_type", "<B")
    state_topic = f"{PREFIX}/state/read/{address}/{characteristic}"
    event_topic = f"{PREFIX}/event/read/{address}/{characteristic}"
    error_topic = f"{PREFIX}/error/read/{address}/{characteristic}"
    
    try:
        import uuid
        char_uuid = uuid.UUID(characteristic)
        command_bytes = bytearray.fromhex(command_hex)
        
        result = await bt_service.send_command(
            address, char_uuid, command_bytes, format_type
        )
        
        response = {
            "address": address,
            "characteristic": characteristic,
            "data": result.hex() if result else None,
        }
        await client.publish(state_topic, json.dumps(response), retain=True)
        await client.publish(event_topic, json.dumps(response))
    except Exception as e:
        logger.error(f"Read from {address}/{characteristic} failed: {e}")
        await client.publish(error_topic, json.dumps({
            "characteristic": characteristic,
            "error": str(e)
        }))


async def main():
    global mqtt_connected
    global last_message_at
    # Last Will Testament - published when connection is lost unexpectedly
    will = Will(STATE_BRIDGE, payload="offline", retain=True)

    app = web.Application()
    app.router.add_get("/health", health_handler)
    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", HEALTH_PORT).start()
    logger.info(f"Health endpoint listening on 0.0.0.0:{HEALTH_PORT}")

    try:
        async with Client(MQTT_BROKER, will=will) as client:
            await client.publish(STATE_BRIDGE, "online", retain=True)
            await client.subscribe(CMD_SCAN)
            await client.subscribe(CMD_CONNECT)
            await client.subscribe(CMD_READ)
            mqtt_connected = True

            logger.info("Bluetooth MQTT Bridge started...")
            logger.info(f"  Listening on: {CMD_SCAN}, {CMD_CONNECT}, {CMD_READ}")

            async for message in client.messages:
                topic_str = str(message.topic)
                last_message_at = utc_now()
                logger.info(f"Received message on topic: {topic_str}")
                topic_parts = topic_str.split("/")

                if message.topic.matches(CMD_SCAN):
                    asyncio.create_task(handle_scan(client))

                elif message.topic.matches(CMD_CONNECT):
                    address = topic_parts[2]
                    asyncio.create_task(handle_connect(client, address))

                elif message.topic.matches(CMD_READ):
                    address = topic_parts[2]
                    characteristic = topic_parts[4]
                    payload = json.loads(message.payload.decode()) if message.payload else {}
                    asyncio.create_task(handle_read(client, address, characteristic, payload))
    finally:
        mqtt_connected = False
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
