"""Config flow for AMTRA WiFi."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AmtraWifiApiClient, AmtraWifiAuthError, AmtraWifiError
from .const import CONF_CORP_ID, CONF_HOST, DEFAULT_CORP_ID, DEFAULT_HOST, DOMAIN


class AmtraWifiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle an AMTRA WiFi config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            client = AmtraWifiApiClient(
                async_get_clientsession(self.hass),
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
                user_input.get(CONF_HOST, DEFAULT_HOST),
                user_input.get(CONF_CORP_ID, DEFAULT_CORP_ID),
            )

            try:
                await client.login()
            except AmtraWifiAuthError:
                errors["base"] = "invalid_auth"
            except AmtraWifiError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(client.user_id or user_input[CONF_USERNAME])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME], data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(CONF_HOST, default=DEFAULT_HOST): str,
                    vol.Optional(CONF_CORP_ID, default=DEFAULT_CORP_ID): str,
                }
            ),
            errors=errors,
        )
