"""BTHome v2 data types and object IDs."""
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional


class ObjectId(IntEnum):
    """BTHome v2 Object IDs - sensors and binary sensors."""
    
    # Misc
    PACKET_ID = 0x00
    
    # Sensors
    BATTERY = 0x01
    TEMPERATURE_PRECISE = 0x02
    HUMIDITY_PRECISE = 0x03
    PRESSURE = 0x04
    ILLUMINANCE = 0x05
    MASS_KG = 0x06
    MASS_LB = 0x07
    DEWPOINT = 0x08
    COUNT_UINT8 = 0x09
    ENERGY = 0x0A
    POWER = 0x0B
    VOLTAGE = 0x0C
    PM25 = 0x0D
    PM10 = 0x0E
    CO2 = 0x12
    TVOC = 0x13
    MOISTURE_PRECISE = 0x14
    HUMIDITY = 0x2E
    MOISTURE = 0x2F
    COUNT_UINT16 = 0x3D
    COUNT_UINT32 = 0x3E
    ROTATION = 0x3F
    DISTANCE_MM = 0x40
    DISTANCE_M = 0x41
    DURATION = 0x42
    CURRENT = 0x43
    SPEED = 0x44
    TEMPERATURE = 0x45
    UV_INDEX = 0x46
    VOLUME_L = 0x47
    VOLUME_ML = 0x48
    VOLUME_FLOW_RATE = 0x49
    VOLTAGE_01 = 0x4A
    GAS = 0x4B
    GAS_UINT32 = 0x4C
    ENERGY_UINT32 = 0x4D
    VOLUME_UINT32 = 0x4E
    WATER = 0x4F
    TIMESTAMP = 0x50
    ACCELERATION = 0x51
    GYROSCOPE = 0x52
    TEXT = 0x53
    RAW = 0x54
    VOLUME_STORAGE = 0x55
    CONDUCTIVITY = 0x56
    TEMPERATURE_INT8 = 0x57
    TEMPERATURE_035 = 0x58
    COUNT_SINT8 = 0x59
    COUNT_SINT16 = 0x5A
    COUNT_SINT32 = 0x5B
    POWER_SINT32 = 0x5C
    CURRENT_SIGNED = 0x5D
    DIRECTION = 0x5E
    PRECIPITATION = 0x5F
    CHANNEL = 0x60
    ROTATIONAL_SPEED = 0x61
    SPEED_SIGNED = 0x62
    ACCELERATION_SIGNED = 0x63
    
    # Binary sensors
    GENERIC_BOOLEAN = 0x0F
    POWER_BINARY = 0x10
    OPENING = 0x11
    BATTERY_LOW = 0x15
    BATTERY_CHARGING = 0x16
    CO = 0x17
    COLD = 0x18
    CONNECTIVITY = 0x19
    DOOR = 0x1A
    GARAGE_DOOR = 0x1B
    GAS_BINARY = 0x1C
    HEAT = 0x1D
    LIGHT = 0x1E
    LOCK = 0x1F
    MOISTURE_BINARY = 0x20
    MOTION = 0x21
    MOVING = 0x22
    OCCUPANCY = 0x23
    PLUG = 0x24
    PRESENCE = 0x25
    PROBLEM = 0x26
    RUNNING = 0x27
    SAFETY = 0x28
    SMOKE = 0x29
    SOUND = 0x2A
    TAMPER = 0x2B
    VIBRATION = 0x2C
    WINDOW = 0x2D
    
    # Events
    BUTTON = 0x3A
    DIMMER = 0x3C
    
    # Device info
    DEVICE_TYPE_ID = 0xF0
    FIRMWARE_VERSION = 0xF1
    FIRMWARE_VERSION_24 = 0xF2


@dataclass
class ObjectSpec:
    """Specification for a BTHome object type."""
    name: str
    data_type: str
    factor: float = 1.0
    unit: Optional[str] = None


OBJECT_SPECS: dict[int, ObjectSpec] = {
    ObjectId.PACKET_ID: ObjectSpec("packet_id", "uint8"),
    ObjectId.BATTERY: ObjectSpec("battery", "uint8", 1, "%"),
    ObjectId.TEMPERATURE_PRECISE: ObjectSpec("temperature", "sint16", 0.01, "°C"),
    ObjectId.HUMIDITY_PRECISE: ObjectSpec("humidity", "uint16", 0.01, "%"),
    ObjectId.PRESSURE: ObjectSpec("pressure", "uint24", 0.01, "hPa"),
    ObjectId.ILLUMINANCE: ObjectSpec("illuminance", "uint24", 0.01, "lx"),
    ObjectId.MASS_KG: ObjectSpec("mass", "uint16", 0.01, "kg"),
    ObjectId.MASS_LB: ObjectSpec("mass", "uint16", 0.01, "lb"),
    ObjectId.DEWPOINT: ObjectSpec("dewpoint", "sint16", 0.01, "°C"),
    ObjectId.COUNT_UINT8: ObjectSpec("count", "uint8"),
    ObjectId.ENERGY: ObjectSpec("energy", "uint24", 0.001, "kWh"),
    ObjectId.POWER: ObjectSpec("power", "uint24", 0.01, "W"),
    ObjectId.VOLTAGE: ObjectSpec("voltage", "uint16", 0.001, "V"),
    ObjectId.PM25: ObjectSpec("pm25", "uint16", 1, "µg/m³"),
    ObjectId.PM10: ObjectSpec("pm10", "uint16", 1, "µg/m³"),
    ObjectId.CO2: ObjectSpec("co2", "uint16", 1, "ppm"),
    ObjectId.TVOC: ObjectSpec("tvoc", "uint16", 1, "µg/m³"),
    ObjectId.MOISTURE_PRECISE: ObjectSpec("moisture", "uint16", 0.01, "%"),
    ObjectId.HUMIDITY: ObjectSpec("humidity", "uint8", 1, "%"),
    ObjectId.MOISTURE: ObjectSpec("moisture", "uint8", 1, "%"),
    ObjectId.COUNT_UINT16: ObjectSpec("count", "uint16"),
    ObjectId.COUNT_UINT32: ObjectSpec("count", "uint32"),
    ObjectId.ROTATION: ObjectSpec("rotation", "sint16", 0.1, "°"),
    ObjectId.DISTANCE_MM: ObjectSpec("distance", "uint16", 1, "mm"),
    ObjectId.DISTANCE_M: ObjectSpec("distance", "uint16", 0.1, "m"),
    ObjectId.DURATION: ObjectSpec("duration", "uint24", 0.001, "s"),
    ObjectId.CURRENT: ObjectSpec("current", "uint16", 0.001, "A"),
    ObjectId.SPEED: ObjectSpec("speed", "uint16", 0.01, "m/s"),
    ObjectId.TEMPERATURE: ObjectSpec("temperature", "sint16", 0.1, "°C"),
    ObjectId.UV_INDEX: ObjectSpec("uv_index", "uint8", 0.1),
    ObjectId.VOLUME_L: ObjectSpec("volume", "uint16", 0.1, "L"),
    ObjectId.VOLUME_ML: ObjectSpec("volume", "uint16", 1, "mL"),
    ObjectId.VOLUME_FLOW_RATE: ObjectSpec("volume_flow_rate", "uint16", 0.001, "m³/hr"),
    ObjectId.VOLTAGE_01: ObjectSpec("voltage", "uint16", 0.1, "V"),
    ObjectId.GAS: ObjectSpec("gas", "uint24", 0.001, "m³"),
    ObjectId.GAS_UINT32: ObjectSpec("gas", "uint32", 0.001, "m³"),
    ObjectId.ENERGY_UINT32: ObjectSpec("energy", "uint32", 0.001, "kWh"),
    ObjectId.VOLUME_UINT32: ObjectSpec("volume", "uint32", 0.001, "L"),
    ObjectId.WATER: ObjectSpec("water", "uint32", 0.001, "L"),
    ObjectId.TIMESTAMP: ObjectSpec("timestamp", "uint32"),
    ObjectId.ACCELERATION: ObjectSpec("acceleration", "uint16", 0.001, "m/s²"),
    ObjectId.GYROSCOPE: ObjectSpec("gyroscope", "uint16", 0.001, "°/s"),
    ObjectId.CONDUCTIVITY: ObjectSpec("conductivity", "uint16", 1, "µS/cm"),
    ObjectId.TEMPERATURE_INT8: ObjectSpec("temperature", "sint8", 1, "°C"),
    ObjectId.TEMPERATURE_035: ObjectSpec("temperature", "sint8", 0.35, "°C"),
    ObjectId.COUNT_SINT8: ObjectSpec("count", "sint8"),
    ObjectId.COUNT_SINT16: ObjectSpec("count", "sint16"),
    ObjectId.COUNT_SINT32: ObjectSpec("count", "sint32"),
    ObjectId.POWER_SINT32: ObjectSpec("power", "sint32", 0.01, "W"),
    ObjectId.CURRENT_SIGNED: ObjectSpec("current", "sint16", 0.001, "A"),
    ObjectId.DIRECTION: ObjectSpec("direction", "uint16", 0.01, "°"),
    ObjectId.PRECIPITATION: ObjectSpec("precipitation", "uint16", 0.1, "mm"),
    ObjectId.CHANNEL: ObjectSpec("channel", "uint8"),
    ObjectId.ROTATIONAL_SPEED: ObjectSpec("rotational_speed", "uint16", 1, "rpm"),
    ObjectId.SPEED_SIGNED: ObjectSpec("speed", "sint32", 0.000001, "m/s"),
    ObjectId.ACCELERATION_SIGNED: ObjectSpec("acceleration", "sint32", 0.000001, "m/s²"),
    
    # Binary sensors
    ObjectId.GENERIC_BOOLEAN: ObjectSpec("generic_boolean", "uint8"),
    ObjectId.POWER_BINARY: ObjectSpec("power", "uint8"),
    ObjectId.OPENING: ObjectSpec("opening", "uint8"),
    ObjectId.BATTERY_LOW: ObjectSpec("battery_low", "uint8"),
    ObjectId.BATTERY_CHARGING: ObjectSpec("battery_charging", "uint8"),
    ObjectId.CO: ObjectSpec("carbon_monoxide", "uint8"),
    ObjectId.COLD: ObjectSpec("cold", "uint8"),
    ObjectId.CONNECTIVITY: ObjectSpec("connectivity", "uint8"),
    ObjectId.DOOR: ObjectSpec("door", "uint8"),
    ObjectId.GARAGE_DOOR: ObjectSpec("garage_door", "uint8"),
    ObjectId.GAS_BINARY: ObjectSpec("gas", "uint8"),
    ObjectId.HEAT: ObjectSpec("heat", "uint8"),
    ObjectId.LIGHT: ObjectSpec("light", "uint8"),
    ObjectId.LOCK: ObjectSpec("lock", "uint8"),
    ObjectId.MOISTURE_BINARY: ObjectSpec("moisture", "uint8"),
    ObjectId.MOTION: ObjectSpec("motion", "uint8"),
    ObjectId.MOVING: ObjectSpec("moving", "uint8"),
    ObjectId.OCCUPANCY: ObjectSpec("occupancy", "uint8"),
    ObjectId.PLUG: ObjectSpec("plug", "uint8"),
    ObjectId.PRESENCE: ObjectSpec("presence", "uint8"),
    ObjectId.PROBLEM: ObjectSpec("problem", "uint8"),
    ObjectId.RUNNING: ObjectSpec("running", "uint8"),
    ObjectId.SAFETY: ObjectSpec("safety", "uint8"),
    ObjectId.SMOKE: ObjectSpec("smoke", "uint8"),
    ObjectId.SOUND: ObjectSpec("sound", "uint8"),
    ObjectId.TAMPER: ObjectSpec("tamper", "uint8"),
    ObjectId.VIBRATION: ObjectSpec("vibration", "uint8"),
    ObjectId.WINDOW: ObjectSpec("window", "uint8"),
}

DATA_TYPE_SIZES = {
    "uint8": 1,
    "sint8": 1,
    "uint16": 2,
    "sint16": 2,
    "uint24": 3,
    "sint24": 3,
    "uint32": 4,
    "sint32": 4,
}


@dataclass
class Measurement:
    """A decoded BTHome measurement."""
    object_id: int
    name: str
    value: float | int | bool | str
    unit: Optional[str] = None
