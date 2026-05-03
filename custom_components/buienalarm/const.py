"""Constants for the BuienAlarm integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "buienalarm"

# Config keys
CONF_LATITUDE: Final = "latitude"
CONF_LONGITUDE: Final = "longitude"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_LANGUAGE: Final = "language"

# Defaults
DEFAULT_NAME: Final = "BuienAlarm"
DEFAULT_SCAN_INTERVAL: Final = 5  # minutes
DEFAULT_LANGUAGE: Final = "nl"
MIN_SCAN_INTERVAL: Final = 3
MAX_SCAN_INTERVAL: Final = 60

# Languages supported in the UI text
LANGUAGES: Final = ["nl", "en"]

# Attribute keys exposed on the main sensor
ATTR_NEXT_RAIN_FORECAST: Final = "next_rain_forecast"
ATTR_RAIN_FORECAST: Final = "rain_forecast"
ATTR_PRECIPITATION: Final = "precip"
ATTR_NEXT_PERIOD: Final = "period_type"
ATTR_PERIOD_START: Final = "period_start"
ATTR_TIME: Final = "attime"

# Coordinator data dict keys
DATA_NEXT_RAIN_TEXT: Final = "next_rain_text"
DATA_NEXT_PERIOD: Final = "next_period"
DATA_PERIOD_START_TEXT: Final = "period_start_text"
DATA_PRECIPITATION: Final = "precipitation"
DATA_RAW: Final = "raw_data"
DATA_SHOWER_START: Final = "shower_start"  # datetime | None
DATA_SHOWER_END: Final = "shower_end"      # datetime | None
DATA_LEVEL_LIGHT: Final = "level_light"        # float | None (mm/h)
DATA_LEVEL_MODERATE: Final = "level_moderate"  # float | None (mm/h)
DATA_LEVEL_HEAVY: Final = "level_heavy"        # float | None (mm/h)

# Period type values
PERIOD_DRY: Final = "dry"
PERIOD_WET: Final = "wet"
PERIOD_NONE: Final = "nan"

# API
API_URL: Final = "https://cdn-secure.buienalarm.nl/api/3.4/forecast.php"
API_TIMEOUT: Final = 30  # seconds
RAIN_THRESHOLD: Final = 0.1  # mm/h

# Localised UI strings used for the main sensor's human-readable state.
LANGUAGE_STRINGS: Final[dict[str, dict[str, str]]] = {
    "nl": {
        "no_rain": "Geen regen verwacht",
        "raining_now": "Het regent",
        "next_rain_minutes": "over {minutes} minuten",
        "next_rain_hour": "over {hours} uur",
        "next_rain_hour_minutes": "over {hours} uur en {minutes} minuten",
        "sensor_name": "Volgende bui",
        "shower_start_name": "Start volgende bui",
        "shower_end_name": "Einde huidige bui",
        "level_light_name": "Drempel licht",
        "level_moderate_name": "Drempel gemiddeld",
        "level_heavy_name": "Drempel zwaar",
    },
    "en": {
        "no_rain": "No rain expected",
        "raining_now": "Raining now",
        "next_rain_minutes": "in {minutes} minutes",
        "next_rain_hour": "in {hours} hour",
        "next_rain_hour_minutes": "in {hours} hour and {minutes} minutes",
        "sensor_name": "Next shower",
        "shower_start_name": "Next shower start",
        "shower_end_name": "Current shower end",
        "level_light_name": "Light threshold",
        "level_moderate_name": "Moderate threshold",
        "level_heavy_name": "Heavy threshold",
    },
}
