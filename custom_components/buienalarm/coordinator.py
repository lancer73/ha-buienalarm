"""DataUpdateCoordinator for the BuienAlarm integration."""

from __future__ import annotations

import asyncio
import logging
import socket
from datetime import datetime, timedelta
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    API_TIMEOUT,
    API_URL,
    ATTR_PRECIPITATION,
    ATTR_TIME,
    DATA_LEVEL_HEAVY,
    DATA_LEVEL_LIGHT,
    DATA_LEVEL_MODERATE,
    DATA_NEXT_PERIOD,
    DATA_NEXT_RAIN_TEXT,
    DATA_PERIOD_START_TEXT,
    DATA_PRECIPITATION,
    DATA_RAW,
    DATA_SHOWER_END,
    DATA_SHOWER_START,
    DEFAULT_LANGUAGE,
    DOMAIN,
    LANGUAGE_STRINGS,
    PERIOD_DRY,
    PERIOD_NONE,
    PERIOD_WET,
    RAIN_THRESHOLD,
)

_LOGGER = logging.getLogger(__name__)


class BuienAlarmDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch and process BuienAlarm forecast data."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        latitude: float,
        longitude: float,
        scan_interval: int,
        language: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialise the coordinator."""
        self.latitude = latitude
        self.longitude = longitude
        self.language = language
        self.strings = LANGUAGE_STRINGS.get(language, LANGUAGE_STRINGS[DEFAULT_LANGUAGE])
        self._session = session

        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=scan_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch and process data from the BuienAlarm API."""
        params = {
            "lat": self.latitude,
            "lon": self.longitude,
            "region": "nl",
            "unit": "mm/u",
        }

        try:
            async with asyncio.timeout(API_TIMEOUT):
                async with self._session.get(API_URL, params=params) as response:
                    if response.status != 200:
                        raise UpdateFailed(
                            f"BuienAlarm API returned HTTP {response.status}"
                        )
                    data = await response.json(content_type=None)
        except asyncio.TimeoutError as err:
            raise UpdateFailed("Timeout while fetching BuienAlarm data") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error connecting to BuienAlarm: {err}") from err
        except ValueError as err:  # JSON decode errors
            raise UpdateFailed(f"Invalid JSON from BuienAlarm: {err}") from err

        # Defensive: a 200 OK with a non-dict body is a server-side regression.
        if not isinstance(data, dict):
            raise UpdateFailed(
                f"BuienAlarm returned unexpected payload type: {type(data).__name__}"
            )

        try:
            return self._process(data)
        except (TypeError, ValueError, KeyError, AttributeError) as err:
            # Anything thrown while interpreting a 200 OK payload should be
            # turned into a clean UpdateFailed so the coordinator marks the
            # data stale and entities go 'unavailable', instead of bubbling
            # up as a generic exception.
            raise UpdateFailed(
                f"Failed to interpret BuienAlarm response: {err}"
            ) from err

    def _process(self, data: dict[str, Any]) -> dict[str, Any]:
        """Turn the raw API payload into the structure the entities consume."""
        precip_list = data.get("precip")
        start = data.get("start")
        delta = data.get("delta")
        levels = self._extract_levels(data)

        # Validate the shape of the response. A malformed-but-200 response
        # falls through to the 'no usable data' branch instead of crashing.
        usable = (
            isinstance(precip_list, list)
            and precip_list
            and isinstance(start, (int, float))
            and isinstance(delta, (int, float))
            and delta > 0
        )
        if usable:
            # Coerce all precipitation values to float; drop anything that
            # can't be coerced rather than crash. Indices stay aligned with
            # the timestamps, so a None replaces a bad value.
            cleaned: list[float | None] = []
            for value in precip_list:  # type: ignore[union-attr]
                try:
                    cleaned.append(float(value))
                except (TypeError, ValueError):
                    cleaned.append(None)
            # If every value is unusable we treat the response as no-data.
            if not any(v is not None for v in cleaned):
                usable = False
            else:
                precip_list = cleaned

        # No usable forecast data: surface a clean 'no rain' result with
        # both timestamp sensors set to None (-> 'unknown' in HA).
        if not usable:
            return {
                DATA_NEXT_RAIN_TEXT: self.strings["no_rain"],
                DATA_NEXT_PERIOD: PERIOD_NONE,
                DATA_PERIOD_START_TEXT: "-",
                DATA_PRECIPITATION: [],
                DATA_RAW: data,
                DATA_SHOWER_START: None,
                DATA_SHOWER_END: None,
                DATA_LEVEL_LIGHT: levels[DATA_LEVEL_LIGHT],
                DATA_LEVEL_MODERATE: levels[DATA_LEVEL_MODERATE],
                DATA_LEVEL_HEAVY: levels[DATA_LEVEL_HEAVY],
            }

        # From here on precip_list is a list[float | None], start/delta are
        # numeric. None precipitation values are treated as 'no rain at this
        # forecast point' for transition detection.
        forecast = [
            {ATTR_PRECIPITATION: precip if precip is not None else 0.0,
             ATTR_TIME: start + i * delta}
            for i, precip in enumerate(precip_list)  # type: ignore[arg-type]
        ]

        now_ts = dt_util.utcnow().timestamp()

        # Determine "currently raining" from the forecast point that
        # corresponds to *now*, not blindly from forecast[0]. forecast[0]
        # may be in the past (when the API's 'start' precedes our poll
        # time) or in the future (when 'start' lies ahead), so it can
        # disagree with the actual present-time precipitation level.
        # We walk the forecast once: the last past-or-equal point gives
        # us the present, and future points give us upcoming transitions.
        shower_start_ts: float | None = None
        shower_end_ts: float | None = None

        # prev_wet starts at None; the first past point we see seeds it.
        # If the entire forecast is in the future (no past points), we
        # treat 'before the forecast began' as dry.
        prev_wet: bool | None = None
        currently_raining = False  # final value set during the loop

        for item in forecast:
            ts = item[ATTR_TIME]
            is_wet = item[ATTR_PRECIPITATION] >= RAIN_THRESHOLD

            if ts <= now_ts:
                # Past or present point: just track running 'wet' state.
                prev_wet = is_wet
                # The most recent past-or-equal point IS "currently
                # raining" — keep updating until we cross into the future.
                currently_raining = is_wet
                continue

            # First future iteration: if we never saw a past point,
            # initialise prev_wet from the assumption the period before
            # the forecast started was dry. This only triggers when the
            # whole forecast lies ahead of us, which is unusual but
            # possible for a freshly-started integration.
            if prev_wet is None:
                prev_wet = False

            # Transition from dry -> wet = a shower starts at this point.
            if is_wet and not prev_wet and shower_start_ts is None:
                shower_start_ts = ts

            # Transition from wet -> dry = a shower ends at this point.
            if not is_wet and prev_wet and shower_end_ts is None:
                shower_end_ts = ts

            prev_wet = is_wet

            # Stop early once we've found both.
            if shower_start_ts is not None and shower_end_ts is not None:
                break

        # Decide which timestamp drives the legacy 'next_rain' state text.
        # Mirrors the original behaviour: if it's already raining, we
        # surface when it will stop; otherwise when it will start.
        if currently_raining:
            next_event_ts = shower_end_ts
            next_period = PERIOD_DRY if next_event_ts else PERIOD_NONE
        else:
            next_event_ts = shower_start_ts
            next_period = PERIOD_WET if next_event_ts else PERIOD_NONE

        if next_event_ts is not None:
            next_event_local = dt_util.as_local(
                dt_util.utc_from_timestamp(next_event_ts)
            )
            period_start_text = next_event_local.strftime("%H:%M")
            relative = self._relative_time(next_event_local)
            next_rain_text = f"{period_start_text} ({relative})"
        else:
            period_start_text = "-"
            next_rain_text = self.strings["no_rain"]

        shower_start_dt: datetime | None = (
            dt_util.utc_from_timestamp(shower_start_ts)
            if shower_start_ts is not None
            else None
        )
        shower_end_dt: datetime | None = (
            dt_util.utc_from_timestamp(shower_end_ts)
            if shower_end_ts is not None
            else None
        )

        return {
            DATA_NEXT_RAIN_TEXT: next_rain_text,
            DATA_NEXT_PERIOD: next_period,
            DATA_PERIOD_START_TEXT: period_start_text,
            DATA_PRECIPITATION: forecast,
            DATA_RAW: data,
            DATA_SHOWER_START: shower_start_dt,
            DATA_SHOWER_END: shower_end_dt,
            DATA_LEVEL_LIGHT: levels[DATA_LEVEL_LIGHT],
            DATA_LEVEL_MODERATE: levels[DATA_LEVEL_MODERATE],
            DATA_LEVEL_HEAVY: levels[DATA_LEVEL_HEAVY],
        }

    @staticmethod
    def _extract_levels(data: dict[str, Any]) -> dict[str, float | None]:
        """Pull the light/moderate/heavy thresholds out of the API payload.

        BuienAlarm returns a 'levels' object containing the mm/h thresholds
        used for rain-intensity classification. Any missing key — or a
        non-dict 'levels' field — returns None so the corresponding sensor
        reports 'unknown'.
        """
        raw_levels = data.get("levels")
        levels: dict[str, Any] = raw_levels if isinstance(raw_levels, dict) else {}

        def _coerce(key: str) -> float | None:
            raw = levels.get(key)
            if raw is None:
                return None
            try:
                return float(raw)
            except (TypeError, ValueError):
                return None

        return {
            DATA_LEVEL_LIGHT: _coerce("light"),
            DATA_LEVEL_MODERATE: _coerce("moderate"),
            DATA_LEVEL_HEAVY: _coerce("heavy"),
        }

    def _relative_time(self, target: datetime) -> str:
        """Format a relative time string in the configured language."""
        diff = target - dt_util.now()
        minutes = max(0, int(diff.total_seconds() // 60))

        if minutes < 60:
            return self.strings["next_rain_minutes"].format(minutes=minutes)

        hours, remaining = divmod(minutes, 60)
        if remaining == 0:
            return self.strings["next_rain_hour"].format(hours=hours)
        return self.strings["next_rain_hour_minutes"].format(
            hours=hours, minutes=remaining
        )


def create_session(use_ipv4_only: bool = True) -> aiohttp.ClientSession:
    """Create a dedicated aiohttp session.

    BuienAlarm's CDN has had IPv6 reachability issues; forcing IPv4 avoids
    long timeouts on dual-stack hosts. The session is owned by the
    integration and closed in async_unload_entry.
    """
    if use_ipv4_only:
        connector = aiohttp.TCPConnector(family=socket.AF_INET)
    else:
        connector = aiohttp.TCPConnector()
    return aiohttp.ClientSession(connector=connector)
