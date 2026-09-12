"""BTHome v2 encoder - convert sensor values to BTHome format."""
import struct
from .types import ObjectId, OBJECT_SPECS


BTHOME_UUID = 0xFCD2
BTHOME_VERSION = 2


def encode_measurement(object_id: ObjectId | int, value: float | int | bool) -> bytes:
    """Encode a single measurement to BTHome format."""
    obj_id = int(object_id)
    spec = OBJECT_SPECS.get(obj_id)
    
    if spec is None:
        raise ValueError(f"Unknown object ID: {obj_id:#x}")
    
    scaled = int(round(value / spec.factor))
    data_type = spec.data_type
    
    if data_type == "uint8":
        encoded = struct.pack("<B", scaled & 0xFF)
    elif data_type == "sint8":
        encoded = struct.pack("<b", scaled)
    elif data_type == "uint16":
        encoded = struct.pack("<H", scaled & 0xFFFF)
    elif data_type == "sint16":
        encoded = struct.pack("<h", scaled)
    elif data_type == "uint24":
        encoded = struct.pack("<I", scaled & 0xFFFFFF)[:3]
    elif data_type == "sint24":
        if scaled < 0:
            scaled = (1 << 24) + scaled
        encoded = struct.pack("<I", scaled & 0xFFFFFF)[:3]
    elif data_type == "uint32":
        encoded = struct.pack("<I", scaled & 0xFFFFFFFF)
    elif data_type == "sint32":
        encoded = struct.pack("<i", scaled)
    else:
        raise ValueError(f"Unknown data type: {data_type}")
    
    return bytes([obj_id]) + encoded


def encode(measurements: list[tuple[ObjectId | int, float | int | bool]], 
           encrypted: bool = False,
           trigger_based: bool = False,
           packet_id: int | None = None) -> bytes:
    """Encode multiple measurements to BTHome service data format."""
    sorted_measurements = sorted(measurements, key=lambda x: int(x[0]))
    
    device_info = (BTHOME_VERSION << 5)
    if encrypted:
        device_info |= 0x01
    if trigger_based:
        device_info |= 0x04
    
    result = struct.pack("<H", BTHOME_UUID) + bytes([device_info])
    
    if packet_id is not None:
        result += encode_measurement(ObjectId.PACKET_ID, packet_id)
    
    for obj_id, value in sorted_measurements:
        result += encode_measurement(obj_id, value)
    
    return result


def encode_advertisement(measurements: list[tuple[ObjectId | int, float | int | bool]],
                         local_name: str | None = None,
                         **kwargs) -> bytes:
    """Encode a complete BTHome BLE advertisement payload."""
    result = bytearray()
    
    result.extend([0x02, 0x01, 0x06])
    
    if local_name:
        name_bytes = local_name.encode("utf-8")
        result.append(len(name_bytes) + 1)
        result.append(0x09)
        result.extend(name_bytes)
    
    service_data = encode(measurements, **kwargs)
    result.append(len(service_data) + 1)
    result.append(0x16)
    result.extend(service_data)
    
    return bytes(result)
