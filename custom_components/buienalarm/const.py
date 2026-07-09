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
DEFAULT_NAME: Final = "Buien-Alarm"  # user-visible name; domain stays "buienalarm"
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
ATTR_ATTRIBUTION: Final = "attribution"

# Coordinator data dict keys
DATA_NEXT_RAIN_TEXT: Final = "next_rain_text"
DATA_NEXT_PERIOD: Final = "next_period"
DATA_PERIOD_START_TEXT: Final = "period_start_text"
DATA_PRECIPITATION: Final = "precipitation"
DATA_RAW: Final = "raw_data"
DATA_SHOWER_START: Final = "shower_start"  # datetime | None
DATA_SHOWER_END: Final = "shower_end"      # datetime | None
DATA_LEVEL_LIGHT: Final = "level_light"        # float (mm/h, fixed)
DATA_LEVEL_MODERATE: Final = "level_moderate"  # float (mm/h, fixed)
DATA_LEVEL_HEAVY: Final = "level_heavy"        # float (mm/h, fixed)

# Period type values
PERIOD_DRY: Final = "dry"
PERIOD_WET: Final = "wet"
PERIOD_NONE: Final = "nan"

# API
# API — Buienradar
#
# The original Buienalarm endpoint (cdn-secure.buienalarm.nl) was retired
# when the Buienalarm site was rebuilt; no public replacement is available.
# Forecast data is now sourced from Buienradar's free, keyless "raintext"
# nowcast, which provides the same data class: point precipitation in
# 5-minute steps over the next two hours.
#
# Buienradar's terms of use require attribution. See ATTRIBUTION below; it
# is surfaced in the README, the integration's device entry, and the
# `attribution` state attribute on the status sensor. Do not remove it.
API_URL: Final = "https://gpsgadget.buienradar.nl/data/raintext"
API_TIMEOUT: Final = 30  # seconds
RAIN_THRESHOLD: Final = 0.1  # mm/h

ATTRIBUTION: Final = "Weather forecast data provided by Buienradar.nl"
ATTRIBUTION_URL: Final = "https://www.buienradar.nl/"

# Buienradar encodes precipitation as a 0-255 byte value, not mm/h.
# The documented conversion is:  mm/h = 10 ** ((value - BASE) / SCALE)
# Reference points: 0 -> ~0.0004 mm/h, 77 -> 0.1 mm/h, 109 -> 1.0 mm/h,
# 141 -> 10.0 mm/h. Note 77 lands exactly on RAIN_THRESHOLD above.
RAINTEXT_BASE: Final = 109
RAINTEXT_SCALE: Final = 32

# Intensities below this are rounded down to a clean 0.0 mm/h. A raw value
# of 0 converts to ~0.0004 mm/h, which is noise, not drizzle.
RAINTEXT_NOISE_FLOOR: Final = 0.01  # mm/h

# Buienradar reports wall-clock times (HH:MM) with no date and no timezone.
# They are anchored to this zone before being converted to UTC.
RAINTEXT_TIMEZONE: Final = "Europe/Amsterdam"

# Rain-intensity thresholds (mm/h).
#
# The former Buienalarm payload carried these as a `levels` object that
# could in principle change server-side. Buienradar has no equivalent
# concept, so they are now fixed constants. Because they never vary, the
# entities that expose them are diagnostic-only and are NOT recorded as
# measurement statistics — they describe configuration, not observation.
LEVEL_LIGHT: Final = 0.1  # mm/h — matches RAIN_THRESHOLD
LEVEL_MODERATE: Final = 1.0  # mm/h
LEVEL_HEAVY: Final = 10.0  # mm/h

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
