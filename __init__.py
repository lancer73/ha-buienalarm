"""
De BuienAlarm integratie voor Home Assistant.
"""

DOMAIN = "buienalarm"

async def async_setup(hass, config):
    """Stel de BuienAlarm component in."""
    return True

async def async_setup_entry(hass, entry):
    """Stel een BuienAlarm config entry in."""
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, "sensor")
    )
    return True

async def async_unload_entry(hass, entry):
    """Verwijder een BuienAlarm config entry."""
    return await hass.config_entries.async_forward_entry_unload(entry, "sensor")
