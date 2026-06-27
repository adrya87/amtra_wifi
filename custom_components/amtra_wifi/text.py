"""Text platform for AMTRA WiFi."""

from __future__ import annotations

from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AmtraWifiCoordinator, AmtraWifiDevice


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AMTRA WiFi text entities."""
    coordinator: AmtraWifiCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AmtraWifiNameText(coordinator, device)
        for device in coordinator.data.devices.values()
    )


class AmtraWifiNameText(CoordinatorEntity[AmtraWifiCoordinator], TextEntity):
    """AMTRA WiFi cloud name text entity."""

    _attr_has_entity_name = True
    _attr_name = "Nome cloud"
    _attr_native_max = 64

    def __init__(self, coordinator: AmtraWifiCoordinator, device: AmtraWifiDevice) -> None:
        """Initialize the text entity."""
        super().__init__(coordinator)
        self._device = device
        self._attr_unique_id = f"{device.unique_id}_text_cloud_name"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device.unique_id)},
            "manufacturer": "AMTRA",
            "model": "LED System Fresh Wi-Fi",
            "name": device.name,
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.data.devices.get(self._device.unique_id)
        return bool(device and device.is_online)

    @property
    def native_value(self) -> str | None:
        """Return current cloud name."""
        device = self.coordinator.data.devices.get(self._device.unique_id)
        return device.name if device else None

    async def async_set_value(self, value: str) -> None:
        """Set cloud name."""
        value = value.strip()
        if not value:
            return
        await self.coordinator.async_rename_device(self._device, value)
