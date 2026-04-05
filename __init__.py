"""
De BuienAlarm integratie voor Home Assistant.
"""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_LATITUDE, CONF_LONGITUDE, CONF_SCAN_INTERVAL, CONF_LANGUAGE,
    DEFAULT_SCAN_INTERVAL, DEFAULT_LANGUAGE, DOMAIN,
)

PLATFORMS = [Platform.SENSOR]

async def async_setup(hass, config):
    """Stel de BuienAlarm component in."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Stel een BuienAlarm config entry in."""
    from .sensor import BuienAlarmDataUpdateCoordinator

    latitude = entry.data[CONF_LATITUDE]
    longitude = entry.data[CONF_LONGITUDE]
    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )
    language = entry.options.get(
        CONF_LANGUAGE, entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
    )

    coordinator = BuienAlarmDataUpdateCoordinator(
        hass, latitude, longitude, scan_interval, language
    )

    # This will raise ConfigEntryNotReady if the first fetch fails — correct place!
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Verwijder een BuienAlarm config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
