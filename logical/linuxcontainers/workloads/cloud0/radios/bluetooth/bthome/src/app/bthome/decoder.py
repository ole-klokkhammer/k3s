"""BTHome v2 decoder - parse BTHome advertisements."""
import struct
from typing import Optional
from .types import ObjectId, Measurement, OBJECT_SPECS, DATA_TYPE_SIZES


BTHOME_UUID = 0xFCD2


def decode(data: bytes) -> list[Measurement]:
    """
    Decode BTHome service data to measurements.
    
    Args:
        data: BTHome service data bytes (starting with UUID)
        
    Returns:
        List of Measurement objects
    """
    if len(data) < 3:
        raise ValueError("BTHome data too short")
    
    uuid = struct.unpack("<H", data[0:2])[0]
    if uuid != BTHOME_UUID:
        raise ValueError(f"Invalid BTHome UUID: {uuid:#x}, expected {BTHOME_UUID:#x}")
    
    device_info = data[2]
    version = (device_info >> 5) & 0x07
    encrypted = bool(device_info & 0x01)
    
    if version not in (1, 2):
        raise ValueError(f"Unsupported BTHome version: {version}")
    
    if encrypted:
        raise ValueError("Encrypted BTHome data not supported")
    
    measurements = []
    pos = 3
    
    while pos < len(data):
        obj_id = data[pos]
        pos += 1
        
        spec = OBJECT_SPECS.get(obj_id)
        if spec is None:
            break
        
        if obj_id in (ObjectId.TEXT, ObjectId.RAW):
            if pos >= len(data):
                break
            length = data[pos]
            pos += 1
            if pos + length > len(data):
                break
            raw_bytes = data[pos:pos + length]
            pos += length
            
            if obj_id == ObjectId.TEXT:
                value = raw_bytes.decode("utf-8", errors="replace")
            else:
                value = raw_bytes.hex()
            
            measurements.append(Measurement(
                object_id=obj_id,
                name=spec.name,
                value=value,
                unit=spec.unit
            ))
            continue
        
        size = DATA_TYPE_SIZES.get(spec.data_type, 0)
        if size == 0 or pos + size > len(data):
            break
        
        raw_bytes = data[pos:pos + size]
        pos += size
        
        data_type = spec.data_type
        if data_type == "uint8":
            raw_value = struct.unpack("<B", raw_bytes)[0]
        elif data_type == "sint8":
            raw_value = struct.unpack("<b", raw_bytes)[0]
        elif data_type == "uint16":
            raw_value = struct.unpack("<H", raw_bytes)[0]
        elif data_type == "sint16":
            raw_value = struct.unpack("<h", raw_bytes)[0]
        elif data_type == "uint24":
            raw_value = struct.unpack("<I", raw_bytes + b'\x00')[0]
        elif data_type == "sint24":
            raw_value = struct.unpack("<I", raw_bytes + b'\x00')[0]
            if raw_value >= (1 << 23):
                raw_value -= (1 << 24)
        elif data_type == "uint32":
            raw_value = struct.unpack("<I", raw_bytes)[0]
        elif data_type == "sint32":
            raw_value = struct.unpack("<i", raw_bytes)[0]
        else:
            continue
        
        value = raw_value * spec.factor
        
        if spec.factor < 1:
            decimals = len(str(spec.factor).split('.')[-1])
            value = round(value, decimals)
        
        measurements.append(Measurement(
            object_id=obj_id,
            name=spec.name,
            value=value,
            unit=spec.unit
        ))
    
    return measurements


def parse_advertisement(payload: bytes) -> tuple[Optional[str], list[Measurement]]:
    """Parse a complete BTHome BLE advertisement payload."""
    local_name = None
    measurements = []
    pos = 0
    
    while pos < len(payload):
        if pos + 2 > len(payload):
            break
            
        length = payload[pos]
        ad_type = payload[pos + 1]
        pos += 2
        
        if pos + length - 1 > len(payload):
            break
        
        ad_data = payload[pos:pos + length - 1]
        pos += length - 1
        
        if ad_type == 0x01:
            continue
        elif ad_type in (0x08, 0x09):
            local_name = ad_data.decode("utf-8", errors="replace")
        elif ad_type == 0x16:
            if len(ad_data) >= 3:
                uuid = struct.unpack("<H", ad_data[0:2])[0]
                if uuid == BTHOME_UUID:
                    measurements = decode(ad_data)
    
    return local_name, measurements


def is_bthome_device(manufacturer_data: dict[int, bytes] | None = None,
                     service_data: dict[str, bytes] | None = None) -> bool:
    """Check if advertisement data indicates a BTHome device."""
    if service_data:
        bthome_uuid_str = f"0000{BTHOME_UUID:04x}-0000-1000-8000-00805f9b34fb"
        if bthome_uuid_str in service_data:
            return True
        if f"{BTHOME_UUID:04x}" in str(service_data).lower():
            return True
    return False
