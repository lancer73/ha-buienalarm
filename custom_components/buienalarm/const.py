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

# Languages supported for the state-text strings. The user picks one of
# these in the config flow (independent from their HA UI locale).
LANGUAGES: Final = [
    "nl", "en", "fr", "es", "pt", "pt-br", "fy", "tr", "ar", "de", "de-ch",
]

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

# State-text strings for the next-shower sensor.
#
# These are the *state value* of the sensor (e.g. what shows on a card or
# in templates), and they follow the `language` config option chosen by
# the user — not the Home Assistant UI locale. A user can run their HA
# in English while keeping the state text in Dutch (or vice-versa).
#
# Entity *names* (the labels shown in the UI for each sensor) live in
# translations/{en,nl,...}.json and follow the HA UI locale. Don't add
# entity-name strings here — they belong in the translation files.
#
# Translations marked "machine-quality" were generated as starting points
# and have not been reviewed by a native speaker. Native speakers are
# warmly invited to open a PR with corrections (see CHANGES.md).
LANGUAGE_STRINGS: Final[dict[str, dict[str, str]]] = {
    "nl": {
        "no_rain": "Geen regen verwacht",
        "raining_now": "Het regent",
        "next_rain_minutes": "over {minutes} minuten",
        "next_rain_hour": "over {hours} uur",
        "next_rain_hour_minutes": "over {hours} uur en {minutes} minuten",
    },
    "en": {
        "no_rain": "No rain expected",
        "raining_now": "Raining now",
        "next_rain_minutes": "in {minutes} minutes",
        "next_rain_hour": "in {hours} hour",
        "next_rain_hour_minutes": "in {hours} hour and {minutes} minutes",
    },
    # --- machine-quality translations below; native-speaker PRs welcome ---
    "fr": {
        "no_rain": "Pas de pluie prévue",
        "raining_now": "Il pleut",
        "next_rain_minutes": "dans {minutes} minutes",
        "next_rain_hour": "dans {hours} heure",
        "next_rain_hour_minutes": "dans {hours} heure et {minutes} minutes",
    },
    "es": {
        "no_rain": "No se espera lluvia",
        "raining_now": "Está lloviendo",
        "next_rain_minutes": "en {minutes} minutos",
        "next_rain_hour": "en {hours} hora",
        "next_rain_hour_minutes": "en {hours} hora y {minutes} minutos",
    },
    "pt": {
        "no_rain": "Não se prevê chuva",
        "raining_now": "Está a chover",
        "next_rain_minutes": "daqui a {minutes} minutos",
        "next_rain_hour": "daqui a {hours} hora",
        "next_rain_hour_minutes": "daqui a {hours} hora e {minutes} minutos",
    },
    "pt-br": {
        "no_rain": "Sem previsão de chuva",
        "raining_now": "Está chovendo",
        "next_rain_minutes": "em {minutes} minutos",
        "next_rain_hour": "em {hours} hora",
        "next_rain_hour_minutes": "em {hours} hora e {minutes} minutos",
    },
    "fy": {
        "no_rain": "Gjin rein ferwachte",
        "raining_now": "It reint",
        "next_rain_minutes": "oer {minutes} minuten",
        "next_rain_hour": "oer {hours} oere",
        "next_rain_hour_minutes": "oer {hours} oere en {minutes} minuten",
    },
    "tr": {
        "no_rain": "Yağmur beklenmiyor",
        "raining_now": "Yağmur yağıyor",
        "next_rain_minutes": "{minutes} dakika içinde",
        "next_rain_hour": "{hours} saat içinde",
        "next_rain_hour_minutes": "{hours} saat {minutes} dakika içinde",
    },
    "ar": {
        "no_rain": "لا يُتوقع هطول مطر",
        "raining_now": "تمطر الآن",
        "next_rain_minutes": "خلال {minutes} دقيقة",
        "next_rain_hour": "خلال {hours} ساعة",
        "next_rain_hour_minutes": "خلال {hours} ساعة و{minutes} دقيقة",
    },
    "de": {
        "no_rain": "Kein Regen erwartet",
        "raining_now": "Es regnet",
        "next_rain_minutes": "in {minutes} Minuten",
        "next_rain_hour": "in {hours} Stunde",
        "next_rain_hour_minutes": "in {hours} Stunde und {minutes} Minuten",
    },
    "de-ch": {
        # Swiss German uses 'ss' instead of 'ß' and a few different words.
        "no_rain": "Kein Regen erwartet",
        "raining_now": "Es regnet",
        "next_rain_minutes": "in {minutes} Minuten",
        "next_rain_hour": "in {hours} Stunde",
        "next_rain_hour_minutes": "in {hours} Stunde und {minutes} Minuten",
    },
}


def resolve_language(language: str | None) -> dict[str, str]:
    """Return the LANGUAGE_STRINGS bundle for a language code.

    Lookup is case-insensitive. If the exact code is missing, fall back
    to the base language (the part before any '-'). If neither is
    present, fall back to English so the sensor never crashes on a
    KeyError. This keeps the integration robust against typos and
    unfamiliar locale codes.
    """
    if not language:
        return LANGUAGE_STRINGS["en"]
    code = language.lower()
    if code in LANGUAGE_STRINGS:
        return LANGUAGE_STRINGS[code]
    base = code.split("-", 1)[0]
    if base in LANGUAGE_STRINGS:
        return LANGUAGE_STRINGS[base]
    return LANGUAGE_STRINGS["en"]
