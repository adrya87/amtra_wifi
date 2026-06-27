"""Select platform for AMTRA WiFi."""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MODE_EASY, MODE_MANUAL
from .coordinator import AmtraWifiCoordinator, AmtraWifiDevice

MODE_OPTIONS = {
    "Manuale": MODE_MANUAL,
    "Easy": MODE_EASY,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AMTRA WiFi selects."""
    coordinator: AmtraWifiCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AmtraWifiModeSelect(coordinator, device)
        for device in coordinator.data.devices.values()
    )


class AmtraWifiModeSelect(CoordinatorEntity[AmtraWifiCoordinator], SelectEntity):
    """AMTRA WiFi mode select."""

    _attr_has_entity_name = True
    _attr_name = "Modalità"
    _attr_options = list(MODE_OPTIONS)

    def __init__(self, coordinator: AmtraWifiCoordinator, device: AmtraWifiDevice) -> None:
        """Initialize the select."""
        super().__init__(coordinator)
        self._device = device
        self._attr_unique_id = f"{device.unique_id}_select_mode"
        self._attr_device_info = _device_info(device)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.data.devices.get(self._device.unique_id)
        return bool(device and device.is_online)

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        mode = self._properties.get("Mode")
        for option, value in MODE_OPTIONS.items():
            if mode == value:
                return option
        return None

    async def async_select_option(self, option: str) -> None:
        """Select a mode."""
        await self.coordinator.async_set_device_properties(
            self._device, {"Mode": MODE_OPTIONS[option]}
        )

    @property
    def _properties(self) -> dict[str, Any]:
        """Return latest properties for this device."""
        return self.coordinator.data.properties.get(self._device.unique_id, {})


def _device_info(device: AmtraWifiDevice) -> dict[str, Any]:
    """Return Home Assistant device info."""
    return {
        "identifiers": {(DOMAIN, device.unique_id)},
        "manufacturer": "AMTRA",
        "model": "LED System Fresh Wi-Fi",
        "name": device.name,
    }
