"""DataUpdateCoordinator for the BuienAlarm integration.

Forecast data is sourced from Buienradar's free "raintext" nowcast.
See const.ATTRIBUTION — Buienradar's terms require attribution.
"""

from __future__ import annotations

import asyncio
import logging
import socket
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

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
    DOMAIN,
    LEVEL_HEAVY,
    LEVEL_LIGHT,
    LEVEL_MODERATE,
    PERIOD_DRY,
    PERIOD_NONE,
    PERIOD_WET,
    RAINTEXT_BASE,
    RAINTEXT_NOISE_FLOOR,
    RAINTEXT_SCALE,
    RAINTEXT_TIMEZONE,
    RAIN_THRESHOLD,
    resolve_language,
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
        self.strings = resolve_language(language)
        self._session = session

        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=scan_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch and process the Buienradar raintext nowcast."""
        params = {
            "lat": f"{self.latitude:.4f}",
            "lon": f"{self.longitude:.4f}",
        }

        try:
            async with asyncio.timeout(API_TIMEOUT):
                async with self._session.get(API_URL, params=params) as response:
                    if response.status != 200:
                        raise UpdateFailed(
                            f"Buienradar API returned HTTP {response.status}"
                        )
                    # The endpoint serves text/plain, not JSON.
                    raw_text = await response.text()
        except asyncio.TimeoutError as err:
            raise UpdateFailed("Timeout while fetching Buienradar data") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error connecting to Buienradar: {err}") from err

        try:
            data = self._parse_raintext(raw_text)
            return self._process(data)
        except (TypeError, ValueError, KeyError, AttributeError) as err:
            # Anything thrown while interpreting a 200 OK payload should be
            # turned into a clean UpdateFailed so the coordinator marks the
            # data stale and entities go 'unavailable', instead of bubbling
            # up as a generic exception.
            raise UpdateFailed(
                f"Failed to interpret Buienradar response: {err}"
            ) from err

    @staticmethod
    def _parse_raintext(text: str) -> dict[str, Any]:
        """Convert Buienradar's raintext body into the internal payload shape.

        The endpoint returns one ``value|HH:MM`` line per 5-minute step, e.g.::

            000|08:05
            077|08:10

        ``value`` is a 0-255 byte, not mm/h; it is converted with
        ``10 ** ((value - BASE) / SCALE)``. Times are local wall-clock with no
        date, so they are anchored to today in RAINTEXT_TIMEZONE and rolled
        forward across midnight (the series is strictly increasing in time).

        Returns the same ``{start, delta, precip}`` structure the previous
        Buienalarm API produced, so ``_process`` is unchanged. Malformed
        lines are skipped rather than fatal; if fewer than two usable points
        remain, an empty ``precip`` list is returned and ``_process`` takes
        its existing 'no usable data' branch.
        """
        tz = ZoneInfo(RAINTEXT_TIMEZONE)
        now_local = dt_util.utcnow().astimezone(tz)

        stamps: list[datetime] = []
        values: list[float] = []
        previous: datetime | None = None
        day_offset = 0

        for line in text.splitlines():
            line = line.strip()
            if not line or "|" not in line:
                continue
            value_str, _, time_str = line.partition("|")
            try:
                raw_value = int(value_str)
                hour_str, _, minute_str = time_str.partition(":")
                hour, minute = int(hour_str), int(minute_str)
                anchored = now_local.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )
            except (TypeError, ValueError):
                # A single malformed line must not sink the whole forecast.
                continue

            # The series runs forward in time. A timestamp that would land
            # before its predecessor has wrapped past midnight.
            candidate = anchored + timedelta(days=day_offset)
            if previous is not None and candidate < previous:
                day_offset += 1
                candidate = anchored + timedelta(days=day_offset)
            previous = candidate

            intensity = 10 ** ((raw_value - RAINTEXT_BASE) / RAINTEXT_SCALE)
            if intensity < RAINTEXT_NOISE_FLOOR:
                # A raw 0 maps to ~0.0004 mm/h. That is noise, not drizzle.
                intensity = 0.0

            stamps.append(candidate)
            values.append(round(intensity, 3))

        # Two points are the minimum needed to derive the step interval.
        if len(stamps) < 2:
            return {"precip": [], "start": None, "delta": None, "raw": text}

        start = stamps[0].timestamp()
        delta = (stamps[1] - stamps[0]).total_seconds()

        return {"precip": values, "start": start, "delta": delta, "raw": text}

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
        # may be in the past, present, or near-future depending on how
        # the API's 'start' aligns with our poll time.
        #
        # We walk the forecast once:
        #   - The last past-or-equal point IS "currently". Track it.
        #   - Future points reveal upcoming dry<->wet transitions.
        #
        # When the API rounds 'start' forward (so every sample is in
        # the future), there is no past-or-equal point to consult. In
        # that case we use the very first forecast point as a proxy for
        # "now", because that's what the API itself considers current.
        # Without this fallback, an all-future, all-wet forecast would
        # have currently_raining=False and the headline would report
        # the first future sample as a "next shower start" — which is
        # wrong: it's not a transition, it's the present state.
        shower_start_ts: float | None = None
        shower_end_ts: float | None = None

        prev_wet: bool | None = None
        seen_past = False
        currently_raining = False

        for item in forecast:
            ts = item[ATTR_TIME]
            is_wet = item[ATTR_PRECIPITATION] >= RAIN_THRESHOLD

            if ts <= now_ts:
                # Past or present point: track running 'wet' state and
                # record it as the current value.
                prev_wet = is_wet
                currently_raining = is_wet
                seen_past = True
                continue

            # First future iteration after no past points: this is the
            # API's "now-ish" point, so use it to set currently_raining.
            # Seed prev_wet to is_wet (not False!) so we don't synthesise
            # a fake dry->wet transition at this very same point — there's
            # no actual edge here, just the start of the visible forecast.
            if not seen_past and prev_wet is None:
                currently_raining = is_wet
                prev_wet = is_wet
                seen_past = True  # only do this once
                # No transition can have happened yet at the very first
                # data point, so skip ahead to the next iteration.
                continue

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
        elif currently_raining:
            # It's raining right now and the forecast window contains no
            # wet -> dry transition (e.g. all-wet forecast). Reflect the
            # present state instead of falling through to "no rain".
            period_start_text = "-"
            next_rain_text = self.strings["raining_now"]
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
    def _extract_levels(data: dict[str, Any]) -> dict[str, float]:
        """Return the light/moderate/heavy rain-intensity thresholds (mm/h).

        The former Buienalarm payload supplied these; Buienradar's raintext
        nowcast has no equivalent field, so they are now fixed constants from
        const.py. The ``data`` argument is retained for signature stability
        and is deliberately unused.

        Because these values never change, the entities exposing them are
        diagnostic-only and carry no state_class — they are configuration,
        not measurement, and must not be recorded as statistics.
        """
        del data  # unused; kept so the call sites in _process stay identical
        return {
            DATA_LEVEL_LIGHT: LEVEL_LIGHT,
            DATA_LEVEL_MODERATE: LEVEL_MODERATE,
            DATA_LEVEL_HEAVY: LEVEL_HEAVY,
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

    Forcing IPv4 avoids long timeouts on dual-stack hosts, a problem seen
    with the previous Buienalarm CDN. It is retained for Buienradar as a
    conservative default; pass use_ipv4_only=False to allow IPv6. The
    session is owned by the integration and closed in async_unload_entry.
    """
    if use_ipv4_only:
        connector = aiohttp.TCPConnector(family=socket.AF_INET)
    else:
        connector = aiohttp.TCPConnector()
    return aiohttp.ClientSession(connector=connector)
