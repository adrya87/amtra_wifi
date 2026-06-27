"""Number platform for AMTRA WiFi."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, EASY_CHANNEL_NAMES
from .coordinator import AmtraWifiCoordinator, AmtraWifiDevice


@dataclass(frozen=True, kw_only=True)
class AmtraWifiNumberDescription:
    """AMTRA WiFi number description."""

    key: str
    name: str
    minimum: float
    maximum: float
    step: float
    unit: str | None = None
    array_key: str | None = None
    array_index: int | None = None


TIME_NUMBERS: tuple[AmtraWifiNumberDescription, ...] = (
    AmtraWifiNumberDescription(
        key="Sunrise",
        name="Alba",
        minimum=0,
        maximum=1439,
        step=1,
        unit="min",
    ),
    AmtraWifiNumberDescription(
        key="SunriseRamp",
        name="Durata alba",
        minimum=0,
        maximum=1440,
        step=1,
        unit="min",
    ),
    AmtraWifiNumberDescription(
        key="Sunset",
        name="Tramonto",
        minimum=0,
        maximum=1439,
        step=1,
        unit="min",
    ),
    AmtraWifiNumberDescription(
        key="SunsetRamp",
        name="Durata tramonto",
        minimum=0,
        maximum=1440,
        step=1,
        unit="min",
    ),
)

ARRAY_NUMBERS = tuple(
    AmtraWifiNumberDescription(
        key=f"{array_key}_{index}",
        name=f"{label} {channel}",
        minimum=0,
        maximum=100,
        step=1,
        unit="%",
        array_key=array_key,
        array_index=index,
    )
    for array_key, label in (("DayBrights", "Giorno"), ("NightBrights", "Notte"))
    for index, channel in enumerate(EASY_CHANNEL_NAMES)
)

NUMBERS = TIME_NUMBERS + ARRAY_NUMBERS


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AMTRA WiFi numbers."""
    coordinator: AmtraWifiCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AmtraWifiNumber(coordinator, device, description)
        for device in coordinator.data.devices.values()
        for description in NUMBERS
    )


class AmtraWifiNumber(CoordinatorEntity[AmtraWifiCoordinator], NumberEntity):
    """AMTRA WiFi number entity."""

    _attr_has_entity_name = True
    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        coordinator: AmtraWifiCoordinator,
        device: AmtraWifiDevice,
        description: AmtraWifiNumberDescription,
    ) -> None:
        """Initialize the number."""
        super().__init__(coordinator)
        self._device = device
        self._description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{device.unique_id}_number_{description.key}"
        self._attr_native_min_value = description.minimum
        self._attr_native_max_value = description.maximum
        self._attr_native_step = description.step
        self._attr_native_unit_of_measurement = description.unit
        self._attr_device_info = _device_info(device)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        device = self.coordinator.data.devices.get(self._device.unique_id)
        return bool(device and device.is_online)

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if self._description.array_key is not None:
            values = self._array_values(self._description.array_key)
            index = self._description.array_index
            if index is None or index >= len(values):
                return None
            return values[index]

        value = self._properties.get(self._description.key)
        return value if isinstance(value, (int, float)) else None

    async def async_set_native_value(self, value: float) -> None:
        """Set the number value."""
        int_value = int(round(value))
        if self._description.array_key is not None:
            array_key = self._description.array_key
            index = self._description.array_index
            if index is None:
                return
            values = self._array_values(array_key)
            while len(values) < len(EASY_CHANNEL_NAMES):
                values.append(0)
            values[index] = int_value
            await self.coordinator.async_set_device_properties(
                self._device, {array_key: values}
            )
            return

        await self.coordinator.async_set_device_properties(
            self._device, {self._description.key: int_value}
        )

    @property
    def _properties(self) -> dict[str, Any]:
        """Return latest properties for this device."""
        return self.coordinator.data.properties.get(self._device.unique_id, {})

    def _array_values(self, key: str) -> list[int]:
        """Return a mutable brightness array."""
        value = self._properties.get(key)
        if isinstance(value, list):
            return [int(item) for item in value]
        return [0] * len(EASY_CHANNEL_NAMES)


def _device_info(device: AmtraWifiDevice) -> dict[str, Any]:
    """Return Home Assistant device info."""
    return {
        "identifiers": {(DOMAIN, device.unique_id)},
        "manufacturer": "AMTRA",
        "model": "LED System Fresh Wi-Fi",
        "name": device.name,
    }
