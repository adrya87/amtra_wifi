"""Light platform for AMTRA WiFi."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGBWW_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CHANNEL_ORDER, DOMAIN, MODE_MANUAL
from .coordinator import AmtraWifiCoordinator, AmtraWifiDevice


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AMTRA WiFi lights."""
    coordinator: AmtraWifiCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AmtraWifiLight(coordinator, device)
        for device in coordinator.data.devices.values()
    )


class AmtraWifiLight(CoordinatorEntity[AmtraWifiCoordinator], LightEntity):
    """AMTRA WiFi five-channel light."""

    _attr_color_mode = ColorMode.RGBWW
    _attr_supported_color_modes = {ColorMode.RGBWW}

    def __init__(self, coordinator: AmtraWifiCoordinator, device: AmtraWifiDevice) -> None:
        """Initialize the light."""
        super().__init__(coordinator)
        self._device = device
        self._attr_name = device.name
        self._attr_unique_id = f"{device.unique_id}_light"
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
    def is_on(self) -> bool:
        """Return true if the light is on."""
        return self._properties.get("Power") == 1

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        values = self._channel_values_255
        if not values:
            return None
        return max(values)

    @property
    def rgbww_color(self) -> tuple[int, int, int, int, int] | None:
        """Return the RGBWW color."""
        values = self._channel_values_255
        if len(values) != 5:
            return None
        return tuple(values)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        mode = self._properties.get("Mode")
        return {
            "mode": "easy" if mode == 2 else "manual" if mode == 0 else mode,
            "cloud_state": "online" if self.available else STATE_UNAVAILABLE,
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        payload: dict[str, Any] = {"Power": 1}

        if ATTR_RGBWW_COLOR in kwargs:
            payload["Mode"] = MODE_MANUAL
            for channel, value in zip(CHANNEL_ORDER, kwargs[ATTR_RGBWW_COLOR], strict=True):
                payload[channel] = _scale_255_to_1000(value)
        elif ATTR_BRIGHTNESS in kwargs:
            payload["Mode"] = MODE_MANUAL
            current = self._channel_values_1000 or [1000, 1000, 1000, 1000, 1000]
            scaled = _scale_channels_to_brightness(current, kwargs[ATTR_BRIGHTNESS])
            for channel, value in zip(CHANNEL_ORDER, scaled, strict=True):
                payload[channel] = value

        await self.coordinator.async_set_device_properties(self._device, payload)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        await self.coordinator.async_set_device_properties(self._device, {"Power": 0})

    @property
    def _properties(self) -> dict[str, Any]:
        """Return latest properties for this device."""
        return self.coordinator.data.properties.get(self._device.unique_id, {})

    @property
    def _channel_values_1000(self) -> list[int]:
        """Return API channel values in RGBWW order."""
        values = []
        for channel in CHANNEL_ORDER:
            value = self._properties.get(channel)
            if isinstance(value, int):
                values.append(max(0, min(1000, value)))
        return values

    @property
    def _channel_values_255(self) -> list[int]:
        """Return channel values scaled to Home Assistant range."""
        return [_scale_1000_to_255(value) for value in self._channel_values_1000]


def _scale_1000_to_255(value: int) -> int:
    """Scale AMTRA 0..1000 values to Home Assistant 0..255 values."""
    return round(max(0, min(1000, value)) * 255 / 1000)


def _scale_255_to_1000(value: int) -> int:
    """Scale Home Assistant 0..255 values to AMTRA 0..1000 values."""
    return round(max(0, min(255, value)) * 1000 / 255)


def _scale_channels_to_brightness(channels: list[int], brightness: int) -> list[int]:
    """Scale channel values while preserving their ratio."""
    current_max = max(channels)
    target = _scale_255_to_1000(brightness)
    if current_max == 0:
        return [target] * 5
    return [round(value * target / current_max) for value in channels]
