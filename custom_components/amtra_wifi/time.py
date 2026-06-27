"""Time platform for AMTRA WiFi."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from typing import Any

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AmtraWifiCoordinator, AmtraWifiDevice


@dataclass(frozen=True, kw_only=True)
class AmtraWifiTimeDescription:
    """AMTRA WiFi time description."""

    key: str
    name: str


TIMES: tuple[AmtraWifiTimeDescription, ...] = (
    AmtraWifiTimeDescription(key="Sunrise", name="Alba"),
    AmtraWifiTimeDescription(key="Sunset", name="Tramonto"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AMTRA WiFi time entities."""
    coordinator: AmtraWifiCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AmtraWifiTime(coordinator, device, description)
        for device in coordinator.data.devices.values()
        for description in TIMES
    )


class AmtraWifiTime(CoordinatorEntity[AmtraWifiCoordinator], TimeEntity):
    """AMTRA WiFi time entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AmtraWifiCoordinator,
        device: AmtraWifiDevice,
        description: AmtraWifiTimeDescription,
    ) -> None:
        """Initialize the time entity."""
        super().__init__(coordinator)
        self._device = device
        self._description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{device.unique_id}_time_{description.key}"
        self._attr_device_info = _device_info(device)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.data.devices.get(self._device.unique_id)
        return bool(device and device.is_online)

    @property
    def native_value(self) -> time | None:
        """Return the time value."""
        value = self._properties.get(self._description.key)
        if not isinstance(value, int):
            return None
        return _minutes_to_time(value)

    async def async_set_value(self, value: time) -> None:
        """Set the time value."""
        await self.coordinator.async_set_device_properties(
            self._device, {self._description.key: _time_to_minutes(value)}
        )

    @property
    def _properties(self) -> dict[str, Any]:
        """Return latest properties for this device."""
        return self.coordinator.data.properties.get(self._device.unique_id, {})


def _minutes_to_time(value: int) -> time:
    """Convert minutes from midnight to a time."""
    value = max(0, min(1439, value))
    return time(hour=value // 60, minute=value % 60)


def _time_to_minutes(value: time) -> int:
    """Convert a time to minutes from midnight."""
    return value.hour * 60 + value.minute


def _device_info(device: AmtraWifiDevice) -> dict[str, Any]:
    """Return Home Assistant device info."""
    return {
        "identifiers": {(DOMAIN, device.unique_id)},
        "manufacturer": "AMTRA",
        "model": "LED System Fresh Wi-Fi",
        "name": device.name,
    }
