"""Config flow for the BuienAlarm integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv

from .const import (
    API_TIMEOUT,
    API_URL,
    CONF_LANGUAGE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_SCAN_INTERVAL,
    DEFAULT_LANGUAGE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    LANGUAGES,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from .coordinator import create_session

_LOGGER = logging.getLogger(__name__)

USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_LATITUDE): cv.latitude,
        vol.Required(CONF_LONGITUDE): cv.longitude,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
        ),
        vol.Optional(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): vol.In(LANGUAGES),
    }
)


async def _validate_api(latitude: float, longitude: float) -> None:
    """Hit the API once to confirm coordinates and connectivity work.

    Raises aiohttp.ClientError, asyncio.TimeoutError or ValueError on failure.
    """
    session = create_session(use_ipv4_only=True)
    try:
        async with asyncio.timeout(API_TIMEOUT):
            async with session.get(
                API_URL,
                params={
                    "lat": latitude,
                    "lon": longitude,
                    "region": "nl",
                    "unit": "mm/u",
                },
            ) as response:
                if response.status != 200:
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                    )
                # Validate it's actually JSON; an HTML error page would slip past
                # the status check.
                payload = await response.json(content_type=None)
        # A 200 OK that isn't a JSON object means we're talking to the wrong
        # endpoint or the API has changed shape; flag as invalid_response.
        if not isinstance(payload, dict):
            raise ValueError(
                f"unexpected payload type: {type(payload).__name__}"
            )
    finally:
        await session.close()


class BuienAlarmConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BuienAlarm."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Round coordinates to 3 decimals for the unique_id (~110 m).
            # Avoids exposing exact home location in the registry while
            # remaining specific enough to prevent duplicate entries.
            unique_id = (
                f"{round(user_input[CONF_LATITUDE], 3)}_"
                f"{round(user_input[CONF_LONGITUDE], 3)}"
            )
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            try:
                await _validate_api(
                    user_input[CONF_LATITUDE], user_input[CONF_LONGITUDE]
                )
            except (aiohttp.ClientError, asyncio.TimeoutError):
                errors["base"] = "cannot_connect"
            except ValueError:
                errors["base"] = "invalid_response"
            except Exception:  # pragma: no cover - defensive
                _LOGGER.exception("Unexpected error validating BuienAlarm API")
                errors["base"] = "unknown"
            else:
                # Title rounded to 2 decimals (~1.1 km) for the same reason.
                title = (
                    f"BuienAlarm ({round(user_input[CONF_LATITUDE], 2)}, "
                    f"{round(user_input[CONF_LONGITUDE], 2)})"
                )
                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow handler."""
        return BuienAlarmOptionsFlowHandler()


class BuienAlarmOptionsFlowHandler(OptionsFlow):
    """Handle BuienAlarm options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_scan_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        current_language = self.config_entry.options.get(
            CONF_LANGUAGE,
            self.config_entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
        )

        options_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=current_scan_interval
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                ),
                vol.Optional(CONF_LANGUAGE, default=current_language): vol.In(
                    LANGUAGES
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=options_schema)
