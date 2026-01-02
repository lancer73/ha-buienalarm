"""
Platform voor de BuienAlarm regen voorspelling sensor.
"""
import asyncio
import datetime
import logging
from datetime import timedelta
import json
from typing import Any, Dict, Optional

import aiohttp
import async_timeout
import voluptuous as vol

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    API_URL,
    ATTR_NEXT_RAIN_FORECAST,
    ATTR_RAIN_FORECAST,
    ATTR_NEXT_PERIOD,
    ATTR_PERIOD_START,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_SCAN_INTERVAL,
    CONF_LANGUAGE,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_LANGUAGE,
    DOMAIN,
    ATTR_PRECIPITATION,
    ATTR_TIME,
    LANGUAGE_STRINGS,
)

_LOGGER = logging.getLogger(__name__)

RAIN_THRESHOLD = 0.1  # Threshold in mm/h to consider as rain


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Stel de BuienAlarm sensor in vanaf een config entry."""
    latitude = entry.data[CONF_LATITUDE]
    longitude = entry.data[CONF_LONGITUDE]
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)
    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )
    language = entry.options.get(
        CONF_LANGUAGE, entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
    )

    coordinator = BuienAlarmDataUpdateCoordinator(
        hass, latitude, longitude, scan_interval, language
    )

    # Doe de eerste update
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([BuienAlarmSensor(coordinator, name, language)], True)


class BuienAlarmDataUpdateCoordinator(DataUpdateCoordinator):
    """Klasse voor het ophalen van BuienAlarm data."""

    def __init__(
        self, hass: HomeAssistant, latitude: float, longitude: float, 
        scan_interval: int, language: str
    ) -> None:
        """Initialize."""
        self.latitude = latitude
        self.longitude = longitude
        self.language = language
        self.session = async_get_clientsession(hass)
        self.strings = LANGUAGE_STRINGS.get(language, LANGUAGE_STRINGS[DEFAULT_LANGUAGE])

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=scan_interval),
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from BuienAlarm API."""
        try:
            with async_timeout.timeout(10):
                url = API_URL.format(lat=self.latitude, lon=self.longitude)
                async with self.session.get(url) as response:
                    if response.status != 200:
                        raise UpdateFailed(
                            f"Error fetching data: {response.status} - {response.reason}"
                        )
                    data = await response.json()
                    
                    if not data.get("precip", []):
                        return {
                            "next_rain": self.strings["no_rain"],
                            "next_period": "nan",
                            "period_start": "-",
                            "precipitation": [],
                            "raw_data": data, 
                        }
                    
                    # Verwerk de voorspellingsdata
                    forecast = []
                    for i, precip in enumerate(data["precip"]):
                        forecast.append({
                            ATTR_PRECIPITATION: precip,
                            ATTR_TIME: data["start"] + i * data["delta"]
                        })
                    
                    # Vind het volgende regenmoment (boven drempelwaarde)
                    next_rain_time = None
                    next_period = 'nan'
                    now_timestamp = datetime.datetime.now().timestamp()
                    
                    if forecast[0][ATTR_PRECIPITATION] >= RAIN_THRESHOLD:
                        for item in forecast:                                                                 
                            if item[ATTR_PRECIPITATION] == 0 and item[ATTR_TIME] > now_timestamp:
                                next_rain_time = item[ATTR_TIME]
                                next_period = 'dry'                                              
                                break
                    else:
                        for item in forecast:
                            if item[ATTR_PRECIPITATION] >= RAIN_THRESHOLD and item[ATTR_TIME] > now_timestamp:
                                next_rain_time = item[ATTR_TIME]
                                next_period = 'wet'
                                break
                    
                    next_rain_formatted = "-"
                    if next_rain_time:
                        # Converteer timestamp naar leesbare tijd
                        next_rain_datetime = datetime.datetime.fromtimestamp(next_rain_time)
                        next_rain_formatted = next_rain_datetime.strftime("%H:%M")
                        next_rain_relative = self._get_relative_time(next_rain_datetime)
                        next_rain_value = f"{next_rain_formatted} ({next_rain_relative})"
                    else:
                        next_rain_value = self.strings["no_rain"]
                    
                    return {
                        "next_rain": next_rain_value,
                        "next_period": next_period,
                        "period_start": next_rain_formatted,
                        "precipitation": forecast,
                        "raw_data": data,
                    }
                    
        except asyncio.TimeoutError:
            raise UpdateFailed("Timeout fetching BuienAlarm data")
        except (aiohttp.ClientError, json.JSONDecodeError) as err:
            raise UpdateFailed(f"Error fetching BuienAlarm data: {err}")

    def _get_relative_time(self, target_time: datetime.datetime) -> str:
        """Bereken relatieve tijdsaanduiding in de juiste taal."""
        now = datetime.datetime.now()
        diff = target_time - now
        minutes = int(diff.total_seconds() / 60)
        
        if minutes < 60:
            return self.strings["next_rain_minutes"].format(minutes=minutes)
        else:
            hours = minutes // 60
            remaining_mins = minutes % 60
            if remaining_mins == 0:
                return self.strings["next_rain_hour"].format(hours=hours)
            else:
                return self.strings["next_rain_hour_minutes"].format(
                    hours=hours, minutes=remaining_mins
                )


class BuienAlarmSensor(CoordinatorEntity, SensorEntity):
    """Implementatie van een BuienAlarm sensor."""

    def __init__(self, coordinator: BuienAlarmDataUpdateCoordinator, name: str, language: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._name = name
        self._language = language
        self._strings = LANGUAGE_STRINGS.get(language, LANGUAGE_STRINGS[DEFAULT_LANGUAGE])
        self._attr_unique_id = f"buienalarm_next_rain_{coordinator.latitude}_{coordinator.longitude}"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{self._name} {self._strings['sensor_name']}"

    @property
    def native_value(self) -> str:
        """Return the state of the device."""
        if self.coordinator.data:
            return self.coordinator.data["next_rain"]
        return "Onbekend"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        if not self.coordinator.data:
            return {}
            
        return {
            ATTR_NEXT_RAIN_FORECAST: self.coordinator.data["next_rain"],
            ATTR_RAIN_FORECAST: self.coordinator.data["precipitation"],
            ATTR_NEXT_PERIOD: self.coordinator.data["next_period"],
            ATTR_PERIOD_START: self.coordinator.data["period_start"],
            "raw_data": self.coordinator.data.get("raw_data", {}),
        }

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        if self.native_value == self._strings["no_rain"]:
            return "mdi:weather-sunny"
        return "mdi:weather-rainy"
