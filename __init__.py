"""
De BuienAlarm integratie voor Home Assistant.
"""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant

DOMAIN = "buienalarm"

# List of platforms to set up
PLATFORMS = [Platform.SENSOR]

async def async_setup(hass, config):
    """Stel de BuienAlarm component in."""
    return True

async def async_setup_entry(hass, entry):
    """Stel een BuienAlarm config entry in."""
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    )
    return True

async def async_unload_entry(hass, entry):
    """Verwijder een BuienAlarm config entry."""
    return await hass.config_entries.async_forward_entry_unload(entry, PLATFORMS)
