"""
Constanten voor de BuienAlarm integratie.
"""

DOMAIN = "buienalarm"

CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_LANGUAGE = "language"

DEFAULT_NAME = "BuienAlarm"
DEFAULT_SCAN_INTERVAL = 5
DEFAULT_LANGUAGE = "nl"

ATTR_NEXT_RAIN_FORECAST = "next_rain_forecast"
ATTR_RAIN_FORECAST = "rain_forecast"
ATTR_PRECIPITATION = "precip"
ATTR_NEXT_PERIOD = "period_type"
ATTR_PERIOD_START = "period_start"
ATTR_TIME = "attime"

# Buienalarm API URL
API_URL = "https://cdn-secure.buienalarm.nl/api/3.4/forecast.php?lat={lat}&lon={lon}&region=nl&unit=mm/u"

# Taalspecifieke constanten
LANGUAGE_STRINGS = {
    "nl": {
        "no_rain": "Geen regen verwacht",
        "next_rain_minutes": "over {minutes} minuten",
        "next_rain_hour": "over {hours} uur",
        "next_rain_hour_minutes": "over {hours} uur en {minutes} minuten",
        "sensor_name": "Volgende Bui"
    },
    "en": {
        "no_rain": "No rain expected",
        "next_rain_minutes": "in {minutes} minutes",
        "next_rain_hour": "in {hours} hour",
        "next_rain_hour_minutes": "in {hours} hour and {minutes} minutes",
        "sensor_name": "Next Rain"
    }
}
