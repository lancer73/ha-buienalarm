"""
Config flow voor BuienAlarm integratie.
"""
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN, 
    CONF_LATITUDE, 
    CONF_LONGITUDE, 
    CONF_SCAN_INTERVAL,
    CONF_LANGUAGE,
    DEFAULT_LANGUAGE
)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_LATITUDE): cv.latitude,
        vol.Required(CONF_LONGITUDE): cv.longitude,
        vol.Optional(CONF_SCAN_INTERVAL, default=5): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=60)
        ),
        vol.Optional(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): vol.In(["nl", "en"]),
    }
)


class BuienAlarmConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow voor BuienAlarm."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Valideren van de invoer en controleren op bestaande entries
            await self.async_set_unique_id(
                f"{user_input[CONF_LATITUDE]}_{user_input[CONF_LONGITUDE]}"
            )
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"BuienAlarm ({user_input[CONF_LATITUDE]}, {user_input[CONF_LONGITUDE]})",
                data=user_input,
            )

        # Toon het configuratieformulier
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return BuienAlarmOptionsFlowHandler(config_entry)


class BuienAlarmOptionsFlowHandler(config_entries.OptionsFlow):
    """BuienAlarm config flow options handler."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Beheer de opties."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        scan_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, 5),
        )
        
        language = self.config_entry.options.get(
            CONF_LANGUAGE,
            self.config_entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
        )

        options_schema = vol.Schema(
            {
                vol.Optional(CONF_SCAN_INTERVAL, default=scan_interval): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=60)
                ),
                vol.Optional(CONF_LANGUAGE, default=language): vol.In(["nl", "en"]),
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema)
