"""Sensor platform for AMTRA WiFi."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AmtraWifiCoordinator, AmtraWifiDevice


@dataclass(frozen=True, kw_only=True)
class AmtraWifiSensorDescription(SensorEntityDescription):
    """AMTRA WiFi sensor description."""

    name: str
    value_fn: Callable[[AmtraWifiDevice, dict[str, Any]], Any]


SENSORS: tuple[AmtraWifiSensorDescription, ...] = (
    AmtraWifiSensorDescription(
        key="firmware_version",
        name="Versione firmware",
        translation_key="firmware_version",
        value_fn=lambda device, props: props.get("FirmwareVersion"),
    ),
    AmtraWifiSensorDescription(
        key="wifi_rssi",
        name="RSSI Wi-Fi",
        translation_key="wifi_rssi",
        native_unit_of_measurement="dBm",
        value_fn=lambda device, props: _device_info(props).get("rssi"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AMTRA WiFi sensors."""
    coordinator: AmtraWifiCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AmtraWifiSensor(coordinator, device, description)
        for device in coordinator.data.devices.values()
        for description in SENSORS
    )


class AmtraWifiSensor(CoordinatorEntity[AmtraWifiCoordinator], SensorEntity):
    """AMTRA WiFi sensor."""

    _attr_has_entity_name = True

    entity_description: AmtraWifiSensorDescription

    def __init__(
        self,
        coordinator: AmtraWifiCoordinator,
        device: AmtraWifiDevice,
        description: AmtraWifiSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device = device
        self.entity_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{device.unique_id}_sensor_{description.key}"
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
    def native_value(self) -> Any:
        """Return the sensor value."""
        properties = self.coordinator.data.properties.get(self._device.unique_id, {})
        return self.entity_description.value_fn(self._device, properties)


def _device_info(properties: dict[str, Any]) -> dict[str, Any]:
    """Return parsed DeviceInfo."""
    value = properties.get("DeviceInfo")
    if isinstance(value, dict):
        return value
    return {}
