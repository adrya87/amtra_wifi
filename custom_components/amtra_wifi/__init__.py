"""AMTRA WiFi integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AmtraWifiApiClient
from .const import CONF_CORP_ID, CONF_HOST, DEFAULT_CORP_ID, DEFAULT_HOST, DOMAIN, PLATFORMS
from .coordinator import AmtraWifiCoordinator


async def _async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload AMTRA WiFi when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AMTRA WiFi from a config entry."""
    entry.async_on_unload(entry.add_update_listener(_async_update_options))

    client = AmtraWifiApiClient(
        async_get_clientsession(hass),
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        entry.data.get(CONF_HOST, DEFAULT_HOST),
        entry.data.get(CONF_CORP_ID, DEFAULT_CORP_ID),
    )
    await client.login()

    coordinator = AmtraWifiCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
