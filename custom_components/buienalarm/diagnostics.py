"""Diagnostics support for the BuienAlarm integration."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import BuienAlarmConfigEntry
from .const import CONF_LATITUDE, CONF_LONGITUDE

# Lat/lon point at the user's home, so we redact them.
TO_REDACT: set[str] = {CONF_LATITUDE, CONF_LONGITUDE}


def _serialise(value: Any) -> Any:
    """Make values JSON-serialisable for the diagnostics download.

    The coordinator stores datetime objects for the shower start/end
    sensors; convert those to ISO 8601 strings so the diagnostics file
    is a clean JSON document.
    """
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _serialise(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialise(v) for v in value]
    return value


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: BuienAlarmConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data

    # Coordinator data is None until the first refresh; tolerate that.
    raw_coordinator_data = coordinator.data or {}

    return {
        "entry": {
            "title": entry.title,
            "version": entry.version,
            "domain": entry.domain,
            "source": entry.source,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": async_redact_data(dict(entry.options), TO_REDACT),
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "update_interval_seconds": (
                coordinator.update_interval.total_seconds()
                if coordinator.update_interval
                else None
            ),
            "language": coordinator.language,
            "data": _serialise(raw_coordinator_data),
        },
    }
