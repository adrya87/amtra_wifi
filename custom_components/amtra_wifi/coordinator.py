"""Data update coordinator for AMTRA WiFi."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AmtraWifiApiClient, AmtraWifiAuthError, AmtraWifiError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class AmtraWifiDevice:
    """AMTRA WiFi device metadata."""

    product_key: str
    device_name: str
    name: str
    mac: str | None
    iot_id: str | None
    is_online: bool

    @property
    def unique_id(self) -> str:
        """Return a stable device unique id."""
        return self.iot_id or f"{self.product_key}_{self.device_name}"


@dataclass(slots=True)
class AmtraWifiData:
    """Coordinator data."""

    devices: dict[str, AmtraWifiDevice]
    properties: dict[str, dict[str, Any]]


class AmtraWifiCoordinator(DataUpdateCoordinator[AmtraWifiData]):
    """Fetch AMTRA WiFi device data."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: AmtraWifiApiClient,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.config_entry = entry
        self.client = client

    async def _async_update_data(self) -> AmtraWifiData:
        """Fetch device list and properties."""
        try:
            raw_devices = await self.client.async_get_devices()
            devices: dict[str, AmtraWifiDevice] = {}
            properties: dict[str, dict[str, Any]] = {}

            for raw_device in raw_devices:
                device = _device_from_payload(raw_device)
                devices[device.unique_id] = device
                if device.is_online:
                    properties[device.unique_id] = await self.client.async_get_properties(
                        device.product_key, device.device_name
                    )
                else:
                    properties[device.unique_id] = {}

            return AmtraWifiData(devices=devices, properties=properties)
        except AmtraWifiAuthError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except AmtraWifiError as err:
            raise UpdateFailed(str(err)) from err

    async def async_set_device_properties(
        self, device: AmtraWifiDevice, properties: dict[str, Any]
    ) -> None:
        """Set properties and refresh coordinator data."""
        await self.client.async_set_properties(
            device.product_key, device.device_name, properties
        )
        await self.async_request_refresh()


def _device_from_payload(payload: dict[str, Any]) -> AmtraWifiDevice:
    """Build a device model from API payload."""
    product_key = str(payload["product_key"])
    device_name = str(payload["device_name"])
    return AmtraWifiDevice(
        product_key=product_key,
        device_name=device_name,
        name=payload.get("name") or device_name,
        mac=payload.get("mac"),
        iot_id=payload.get("iotid"),
        is_online=payload.get("is_online") == "online",
    )
