"""Constants for the AMTRA WiFi integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "amtra_wifi"

DEFAULT_HOST = "http://47.89.235.158:8086"
DEFAULT_CORP_ID = "a3MAuNKJuLP"
DEFAULT_GRANT_TYPE = "app"
DEFAULT_SCAN_INTERVAL = timedelta(seconds=60)

CONF_CORP_ID = "corp_id"
CONF_HOST = "host"

PLATFORMS = ["light", "sensor"]

CHANNELS = {
    "Chn1Bright": "green",
    "Chn2Bright": "red",
    "Chn3Bright": "blue",
    "Chn4Bright": "cold_white",
    "Chn5Bright": "warm_white",
}

CHANNEL_ORDER = (
    "Chn2Bright",
    "Chn1Bright",
    "Chn3Bright",
    "Chn4Bright",
    "Chn5Bright",
)

MODE_MANUAL = 0
MODE_EASY = 2
