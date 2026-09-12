"""
Home Assistant MQTT Auto-Discovery support.

Publishes discovery messages to homeassistant/sensor/... so HA automatically
creates entities for each measurement.

Reference: https://www.home-assistant.io/integrations/mqtt/#mqtt-discovery
"""
import json
import logging

logger = logging.getLogger(__name__)

# Map measurement names to HA device classes and icons
MEASUREMENT_CONFIG = {
    "temperature": {
        "device_class": "temperature",
        "unit_of_measurement": "°C",
        "icon": None,
    },
    "humidity": {
        "device_class": "humidity",
        "unit_of_measurement": "%",
        "icon": None,
    },
    "battery": {
        "device_class": "battery",
        "unit_of_measurement": "%",
        "icon": None,
    },
    "pressure": {
        "device_class": "pressure",
        "unit_of_measurement": "hPa",
        "icon": None,
    },
    "co2": {
        "device_class": "carbon_dioxide",
        "unit_of_measurement": "ppm",
        "icon": None,
    },
    "voc": {
        "device_class": "volatile_organic_compounds_parts",
        "unit_of_measurement": "ppb",
        "icon": "mdi:molecule",
    },
    "illuminance": {
        "device_class": "illuminance",
        "unit_of_measurement": "lx",
        "icon": None,
    },
    "moisture": {
        "device_class": "moisture",
        "unit_of_measurement": "%",
        "icon": None,
    },
    "radon_1day_avg": {
        "device_class": None,
        "unit_of_measurement": "Bq/m³",
        "icon": "mdi:radioactive",
    },
    "radon_longterm_avg": {
        "device_class": None,
        "unit_of_measurement": "Bq/m³",
        "icon": "mdi:radioactive",
    },
    "motion": {
        "device_class": "motion",
        "unit_of_measurement": None,
        "icon": None,
    },
    "door": {
        "device_class": "door",
        "unit_of_measurement": None,
        "icon": None,
    },
    "window": {
        "device_class": "window",
        "unit_of_measurement": None,
        "icon": None,
    },
}


def get_device_info(decoded: dict) -> dict:
    """Generate HA device info block."""
    address = decoded["address"]
    name = decoded.get("name") or address
    protocol = decoded.get("protocol", "unknown")
    
    return {
        "identifiers": [f"bthome_{address.replace(':', '')}"],
        "name": name,
        "manufacturer": protocol.capitalize(),
        "model": f"{protocol.upper()} Sensor",
        "via_device": "bthome_processor",
    }


def generate_discovery_payload(
    decoded: dict,
    measurement: dict,
    base_topic: str,
) -> tuple[str, dict]:
    """
    Generate MQTT discovery topic and payload for a measurement.
    
    Args:
        decoded: The decoded device data
        measurement: The measurement dict with name, value, unit
        base_topic: Base topic like bthome/state/xiaomi/A4_C1_38_XX_XX_XX
    
    Returns:
        Tuple of (discovery_topic, payload_dict)
    """
    address = decoded["address"].replace(":", "").lower()
    name = decoded.get("name") or decoded["address"]
    measurement_name = measurement["name"]
    measurement_key = measurement_name.lower().replace(" ", "_")
    
    # Unique ID for this sensor
    unique_id = f"bthome_{address}_{measurement_key}"
    
    # Get measurement config
    config = MEASUREMENT_CONFIG.get(measurement_name, {})
    
    # Discovery topic
    discovery_topic = f"homeassistant/sensor/{unique_id}/config"
    
    # State topic for this specific measurement
    state_topic = f"{base_topic}/{measurement_key}"
    
    # Build payload
    payload = {
        "name": f"{measurement_name.replace('_', ' ').title()}",
        "unique_id": unique_id,
        "state_topic": state_topic,
        "value_template": "{{ value_json.value }}",
        "device": get_device_info(decoded),
        "state_class": "measurement",
    }
    
    # Add device class if known
    if config.get("device_class"):
        payload["device_class"] = config["device_class"]
    
    # Add unit if known (prefer from measurement, fallback to config)
    unit = measurement.get("unit") or config.get("unit_of_measurement")
    if unit:
        payload["unit_of_measurement"] = unit
    
    # Add icon if specified
    if config.get("icon"):
        payload["icon"] = config["icon"]
    
    return discovery_topic, payload


async def publish_discovery(client, decoded: dict, state_topic: str):
    """Publish Home Assistant MQTT discovery messages for all measurements."""
    for measurement in decoded.get("measurements", []):
        try:
            discovery_topic, payload = generate_discovery_payload(
                decoded, measurement, state_topic
            )
            await client.publish(discovery_topic, json.dumps(payload), retain=True)
            logger.debug(f"Published HA discovery: {discovery_topic}")
        except Exception as e:
            logger.warning(f"Failed to publish discovery for {measurement}: {e}")
