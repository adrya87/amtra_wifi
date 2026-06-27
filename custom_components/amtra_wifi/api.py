"""Async client for the AMTRA WiFi cloud API."""

from __future__ import annotations

import json
from typing import Any

from aiohttp import ClientResponseError, ClientSession

from .const import DEFAULT_CORP_ID, DEFAULT_GRANT_TYPE, DEFAULT_HOST


class AmtraWifiError(Exception):
    """Base AMTRA WiFi API error."""


class AmtraWifiAuthError(AmtraWifiError):
    """Authentication failed."""


class AmtraWifiApiClient:
    """Small client for the AMTRA WiFi cloud backend."""

    def __init__(
        self,
        session: ClientSession,
        username: str,
        password: str,
        host: str = DEFAULT_HOST,
        corp_id: str = DEFAULT_CORP_ID,
    ) -> None:
        self._session = session
        self._username = username
        self._principal = _format_principal(username)
        self._password = password
        self._host = host.rstrip("/")
        self._corp_id = corp_id
        self._access_token: str | None = None
        self.user_id: str | None = None

    async def login(self) -> None:
        """Authenticate and store the bearer token."""
        data = await self._request(
            "post",
            "/login",
            authenticated=False,
            params={"corpid": self._corp_id, "grant_type": DEFAULT_GRANT_TYPE},
            json={"principal": self._principal, "credentials": self._password},
        )

        token = data.get("access_token")
        if not token or data.get("code") not in (None, 0):
            raise AmtraWifiAuthError(data.get("msg") or "Login failed")

        self._access_token = token
        self.user_id = data.get("userid")

    async def async_get_devices(self) -> list[dict[str, Any]]:
        """Return devices associated with the account."""
        data = await self._request("get", "/groups_and_subscribed_devices")
        payload = data.get("data") or {}
        return list(payload.get("subscribed_devices") or [])

    async def async_get_properties(
        self, product_key: str, device_name: str
    ) -> dict[str, Any]:
        """Return properties for a device as an identifier-to-value mapping."""
        path = f"/product/{product_key}/device/{device_name}/get_properties"
        data = await self._request("get", path)
        properties: dict[str, Any] = {}

        for item in data.get("data") or []:
            identifier = item.get("identifier")
            if not identifier:
                continue
            properties[identifier] = _parse_property_value(item.get("value"))

        return properties

    async def async_set_properties(
        self, product_key: str, device_name: str, properties: dict[str, Any]
    ) -> None:
        """Set one or more device properties."""
        path = f"/product/{product_key}/device/{device_name}/set_properties"
        await self._request("post", path, json={"items": json.dumps(properties)})

    async def async_rename_device(
        self, product_key: str, device_name: str, name: str
    ) -> None:
        """Rename a device."""
        path = f"/product/{product_key}/device/{device_name}"
        await self._request("put", path, json={"name": name})

    async def _request(
        self,
        method: str,
        path: str,
        *,
        authenticated: bool = True,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make an API request."""
        headers = dict(kwargs.pop("headers", {}))
        if authenticated:
            if not self._access_token:
                await self.login()
            headers["Authorization"] = f"bearer {self._access_token}"

        try:
            response = await self._session.request(
                method, f"{self._host}{path}", headers=headers, **kwargs
            )
            response.raise_for_status()
            data = await response.json(content_type=None)
        except ClientResponseError as err:
            if err.status in (401, 403) and authenticated:
                self._access_token = None
                raise AmtraWifiAuthError("Authentication expired") from err
            raise AmtraWifiError(str(err)) from err
        except Exception as err:  # noqa: BLE001
            raise AmtraWifiError(str(err)) from err

        if isinstance(data, dict) and data.get("code") not in (None, 0):
            message = data.get("msg") or "AMTRA WiFi API error"
            if path == "/login" or "auth" in message.lower() or "token" in message.lower():
                raise AmtraWifiAuthError(message)
            raise AmtraWifiError(message)

        return data


def _format_principal(username: str) -> str:
    """Return the principal format used by the AMTRA app."""
    username = username.strip()
    if username.startswith("password@"):
        return username
    return f"password@{username}"


def _parse_property_value(value: Any) -> Any:
    """Parse values returned as strings by the cloud API."""
    if not isinstance(value, str):
        return value

    value = value.strip()
    if value == "":
        return value

    try:
        return json.loads(value)
    except json.JSONDecodeError:
        pass

    if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
        return int(value)

    return value
