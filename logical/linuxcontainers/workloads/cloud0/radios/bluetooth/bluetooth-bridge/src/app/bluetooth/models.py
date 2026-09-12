from dataclasses import field, dataclass
from typing import Optional, Dict, List

@dataclass
class Value:
    hex: str
    utf8: str

@dataclass
class Descriptor:
    description: str
    value: Optional[Value] = None
    error: Optional[str] = None

@dataclass
class Characteristic:
    description: str
    properties: List[str]
    value: Optional[Value] = None
    error: Optional[str] = None
    descriptors: Dict[str, 'Descriptor'] = field(default_factory=dict)

@dataclass
class Service:
    description: str
    characteristics: Dict[str, 'Characteristic'] = field(default_factory=dict)

@dataclass
class BLEDeviceResponse:
    services: Dict[str, 'Service'] = field(default_factory=dict)