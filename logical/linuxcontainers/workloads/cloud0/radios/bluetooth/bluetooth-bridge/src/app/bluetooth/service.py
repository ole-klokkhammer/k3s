#!/usr/bin/python3

import asyncio
import logging
import struct
import uuid
from typing import Any, Optional, Dict, List
from bluetooth.models import (
    BLEDeviceResponse,
    Service,
    Characteristic,
    Descriptor,
    Value,
)
import utils
from bleak import BleakScanner, BleakClient
from bleak.exc import BleakError, BleakDBusError
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
import env 

async_lock = asyncio.Lock()


async def scan(timeout: float):
    async with async_lock:
        devices: Dict[
            str, tuple[BLEDevice, AdvertisementData]
        ] = await BleakScanner.discover(
            return_adv=True, timeout=timeout
        )  # type: ignore

        logging.info(f"Scan completed with {len(devices)} devices found.")

        return [
            {
                "name": device.name,
                "address": device.address,
                "rssi": ad_data.rssi,
                "manufacturer_data": {
                    k: utils.bytes_as_str(v)
                    for k, v in ad_data.manufacturer_data.items()
                },
                "service_data": {
                    k: utils.bytes_as_str(v)
                    for k, v in ad_data.service_data.items()
                },
            }
            for device, ad_data in devices.values()
        ]


async def connect(address: str, timeout: float) -> BLEDeviceResponse:
    async with async_lock:
        logging.info(f"Connecting to Bluetooth device {address}...")
        result = BLEDeviceResponse()
        try:
            async with BleakClient(address, timeout=timeout) as client:
                for service in client.services:
                    service_info = Service(description=service.description)
                    for characteristic in service.characteristics:
                        char_value = Characteristic(
                            description=characteristic.description,
                            properties=characteristic.properties,
                        )
                        try:
                            if "read" in characteristic.properties:
                                gatt_value = await client.read_gatt_char(
                                    characteristic.uuid
                                )
                                char_value.value = Value(
                                    hex=utils.bytes_as_str(gatt_value),
                                    utf8=gatt_value.decode("utf-8", errors="ignore"),
                                )
                            else:
                                char_value.value = None
                        except BleakError as e:
                            char_value.error = str(e)

                        for descriptor in characteristic.descriptors:
                            desc_value = Descriptor(description=descriptor.description)
                            try:
                                desc_data = await client.read_gatt_descriptor(
                                    descriptor.handle
                                )
                                desc_value.value = Value(
                                    hex=utils.bytes_as_str(desc_data),
                                    utf8=desc_data.decode("utf-8", errors="ignore"),
                                )
                            except BleakError as e:
                                desc_value.error = str(e)
                            char_value.descriptors[descriptor.uuid] = desc_value

                        service_info.characteristics[characteristic.uuid] = char_value

                    result.services[service.uuid] = service_info
        except BleakDBusError as e:
            raise
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            raise
        return result


async def send_command(
    address: str,
    characteristic: uuid.UUID,
    command: bytearray,
    format_type: str,
) -> Optional[bytearray]:
    async with async_lock:
        notification = NotificationReceiver(characteristic, format_type)
        async with BleakClient(address) as client:
            await client.start_notify(characteristic, notification)
            await client.write_gatt_char(characteristic, command)
            await notification.wait_for_message(env.command_timeout)
            await client.stop_notify(characteristic)
        return notification.message


class NotificationReceiver:
    message: Optional[bytearray]

    def __init__(self, characteristic: uuid.UUID, format_type: str):
        self.message: Optional[bytearray] = None
        self.characteristic = characteristic
        self.format_type = format_type
        self._message_size = struct.calcsize(self.format_type)
        self._loop = asyncio.get_running_loop()
        self._future: asyncio.Future[None] = self._loop.create_future()

    def _full_message_received(self) -> bool:
        return self.message is not None and len(self.message) >= self._message_size

    def __call__(self, _: Any, data: bytearray) -> None:
        if self.message is None:
            self.message = data
        elif not self._full_message_received():
            self.message += data

        if self._full_message_received():
            if not self._future.done():
                self._future.set_result(None)

    def _on_timeout(self) -> None:
        if not self._future.done():
            self._future.set_exception(
                asyncio.TimeoutError("Timeout waiting for message")
            )

    async def wait_for_message(self, timeout: float) -> None:
        if not self._full_message_received():
            timer_handle = self._loop.call_later(timeout, self._on_timeout)
            try:
                await self._future
            finally:
                timer_handle.cancel()
