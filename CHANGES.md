# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-05-03

### Added

- **Nine new locales** for both the next-shower state text (`LANGUAGE_STRINGS`)
  and the Home Assistant UI translations (`translations/`):
  - `fr` — French
  - `es` — Spanish
  - `pt` — Portuguese (Portugal)
  - `pt-BR` — Portuguese (Brazil)
  - `fy` — West Frisian (Frysk)
  - `tr` — Turkish
  - `ar` — Arabic (Modern Standard)
  - `de` — German
  - `de-CH` — Swiss German

  > **Help wanted:** these translations were generated as machine-quality
  > starting points and have **not been reviewed by native speakers**.
  > Native speakers are warmly invited to open a pull request with
  > corrections — small fixes are very welcome.

- **`resolve_language()` helper** in `const.py` for robust state-text
  language lookup. Lookup is case-insensitive and falls back through:
  exact match → base language (e.g. `pt-PT` → `pt`) → English. This
  protects the integration from typos and unfamiliar locale codes.

### Changed

- The `language` config-flow option now offers 11 choices instead of 2.
  Existing entries with `language: nl` or `language: en` continue to work
  unchanged.

### Notes

- **`de-AT` (Austrian German) was deliberately not added as a separate
  locale.** Austria uses standard German, and the differences from `de-DE`
  are vocabulary (e.g. *Jänner* vs *Januar*) that don't appear in any of
  these strings. Users in Austria with HA UI set to `de-AT` will fall
  through to `de` automatically via `resolve_language`.
- **Moroccan Darija was deliberately not added.** Morocco's written
  language is Modern Standard Arabic (now available as `ar`); spoken
  Darija has no commonly-used locale code and no HA support.

## [1.0.4] - 2026-05-03

### Changed

- **Cleaned up the split between `LANGUAGE_STRINGS` (in `const.py`) and the
  HA translation files.** The two systems serve different purposes and
  were getting mixed up:
  - `LANGUAGE_STRINGS` is for the *state value* of the next-shower text
    sensor (e.g. `"in 30 minutes"` vs `"over 30 minuten"`). The user
    picks this language at config time and it can differ from the HA UI
    locale — useful when running an English UI but wanting Dutch state
    text on the dashboard, or vice-versa.
  - `translations/{en,nl}.json` is for entity *names* and config-flow
    labels. These follow the HA UI locale.
- Removed the entity-name fallback strings (`sensor_name`,
  `shower_start_name`, `shower_end_name`, `level_*_name`) from
  `LANGUAGE_STRINGS` — they duplicated the proper translation files and
  were never reached because every entity already declares a
  `translation_key`. Entity names now come exclusively from
  `translations/{en,nl}.json`.
- Simplified `sensor.py` accordingly: the `(description, name_key)`
  tuple wrapper for timestamp descriptions is gone, the `_LEVEL_NAME_KEYS`
  map is gone, and the `fallback_name` parameter on `BuienAlarmGenericSensor`
  is gone. Less code, single source of truth for entity names.

No user-visible changes are expected. Entity names continue to display
correctly in both locales.

## [1.0.3] - 2026-05-03

### Fixed

- **"Next shower" sensor reporting "no rain expected" while every forecast
  timeslot showed precipitation.** v1.0.2 correctly determined that
  `currently_raining` was `True`, but the headline-rendering branch only
  consulted the upcoming-transition timestamp; with no wet→dry transition
  in the window (an all-wet forecast), it fell through to the "no rain"
  string. The headline now distinguishes three cases:
  - A transition is upcoming → show its time (e.g. `14:25 (in 30 minutes)`)
  - No transition, currently raining → show the new "Raining now" /
    "Het regent" string
  - No transition, currently dry → show "No rain expected" /
    "Geen regen verwacht" as before

### Added

- New translation strings `raining_now` for the all-wet headline case:
  `"Raining now"` (English) / `"Het regent"` (Dutch). No new HA UI
  translation key is needed; this string is read from the language pack
  passed at config time.

## [1.0.2] - 2026-05-02

### Fixed

- **"Next shower" headline always showing the start of the next shower
  instead of the end of the current one.** Affected setups where the API's
  `start` field was rounded forward (so every forecast sample was strictly
  in the future relative to the integration's poll time). In that case the
  past-or-equal point loop never ran, `currently_raining` stayed at its
  default of `False`, and the headline always took the "next start" branch.
- **All-wet forecast windows reporting "no rain expected".** Same root
  cause: with no past-or-equal forecast point, `currently_raining` defaulted
  to `False`, and the all-wet window has no dry→wet transition for the
  "next start" path to latch onto either, so the headline fell through to
  "no rain expected" even though every forecast point showed precipitation.

  Both issues are fixed by inferring `currently_raining` from the first
  future forecast point when no past-or-equal point is available — the API
  treats the first forecast sample as "now-ish", and the integration now
  honours that. The transition detector also no longer synthesises a fake
  dry→wet edge at the seeded boundary, which would otherwise have caused
  an all-wet forecast to incorrectly report a "shower start" at the very
  first sample.

## [1.0.1] - 2026-04-25

### Fixed

- **Status sensor briefly reporting "no rain expected" while it was
  actually raining.** The "currently raining?" decision was based on
  `forecast[0]`, which can be in the past, present, or near-future
  depending on how the API's `start` aligns with the integration's
  poll time. When `forecast[0]` was a past dry sample, the past-points
  walk could correctly transition into "wet" state and capture an
  upcoming end-of-shower timestamp, while the headline path still
  thought it was dry — yielding the contradictory state of:
    - Status text: "no rain expected"
    - Current shower end: a real timestamp
    - Next shower start: unknown
  The two views are now derived from a single walk through the
  forecast: "currently raining" is taken from the most recent
  past-or-equal forecast point, never from `forecast[0]`. The
  contradictory transient state can no longer occur.

## [1.0.0] - 2026-04-25

First stable release. The integration has been restructured to follow current
Home Assistant integration conventions and the file layout HACS expects.

### ⚠️ Breaking changes

- **Repository layout moved to `custom_components/buienalarm/`.** Manual
  installations from previous versions should remove the old files from
  `custom_components/buienalarm/` and reinstall. HACS users will be migrated
  on update.
- **`raw_data` is no longer exposed as a state attribute** on the next-shower
  sensor. The full upstream payload is now available through the
  *Download diagnostics* button on the integration card. Dashboards that read
  `attributes.raw_data.levels.light` / `.moderate` / `.heavy` must switch to
  the new threshold sensors (see below).
- **Minimum scan interval raised from 1 minute to 3 minutes** to be a better
  citizen against the public BuienAlarm API. Existing entries with a value
  below 3 will be clamped on the next options-flow save.
- **`unique_id` for entries now uses coordinates rounded to 3 decimals**
  (≈110 m) instead of the raw values. This prevents leaking the exact home
  location through the registry. **Existing entries are migrated
  automatically** on first load: the config-entry version is bumped from 1
  to 2, the entry's `unique_id` is rewritten, and the legacy
  `buienalarm_next_rain_<lat>_<lon>` sensor entity is renamed to the new
  scheme so history is preserved.

### Added

- **New sensor: next shower start** (`sensor.<name>_next_shower_start`) with
  `device_class: timestamp`. Reports the time of the next dry→wet transition
  in the forecast window, or `unknown` if no shower is expected.
- **New sensor: current shower end** (`sensor.<name>_current_shower_end`) with
  `device_class: timestamp`. Reports when the ongoing or upcoming shower is
  expected to end, or `unknown` if no end transition is in the window.
- **New sensors for rain-intensity thresholds**: `level_light`,
  `level_moderate`, `level_heavy`, each with unit `mm/h` and
  `device_class: precipitation_intensity`. They return `unknown` if the API
  response does not include a `levels` object.
- **Diagnostics support.** The *Download diagnostics* button on the
  integration card returns a JSON file with the redacted entry data, the
  coordinator state, and the last-known raw API payload. Latitude and
  longitude are redacted automatically.
- **Brand icons** shipped in `custom_components/buienalarm/brand/`, picked up
  by Home Assistant 2026.3 and later for the integration card and device
  page.
- **Localised UI** through standard `translations/en.json` and
  `translations/nl.json`. The previous custom-language string mechanism is
  retained as a fallback only.
- **Connectivity check during configuration.** The config flow now performs a
  test API call and reports `cannot_connect` or `invalid_response` instead
  of silently creating a non-working entry.
- **Options changes apply without an HA restart.** Changing the scan
  interval or language now triggers an automatic entry reload.
- **MIT `LICENSE` file** added at the repository root.
- **`hacs.json`** added at the repository root with `homeassistant` minimum
  version and `country` metadata.
- **`CHANGES.md`** (this file).
- **Automatic config-entry migration** from version 1 to version 2 (see
  *Breaking changes* for the unique_id rewrite). Implemented via
  `async_migrate_entry` so users do not need to remove and re-add the
  integration to benefit from the privacy fix.

### Changed

- Restructured the integration into separate `coordinator.py`,
  `diagnostics.py`, and platform modules.
- All entities now use `_attr_has_entity_name = True`, share a common
  `DeviceInfo`, and use translation keys instead of hard-coded names.
- Sensor entities for shower start/end and the three intensity thresholds
  are marked `EntityCategory.DIAGNOSTIC` so they don't clutter the main
  device page.
- Datetime handling switched to `homeassistant.util.dt` so timezone-aware
  values are used everywhere; resolves edge cases around DST and HA's
  configured timezone differing from system time.
- The aiohttp `ClientSession` used to talk to BuienAlarm is now closed
  cleanly when the entry is unloaded.
- The entry title now rounds the displayed coordinates to two decimals
  (≈1.1 km) so screenshots and shared logs do not pinpoint home addresses.
- API URL parameters are passed via aiohttp's `params=` argument instead of
  string formatting.
- Bumped declared minimum Home Assistant version to 2024.12 (required for
  `entry.runtime_data` and the modern options flow pattern).

### Fixed

- **Double-pop on unload.** `async_unload_entry` no longer raises a
  `KeyError` on every reload of the entry. Coordinator lifetime is now
  managed via `entry.runtime_data` and `entry.async_on_unload()`.
- **Leaked `aiohttp.ClientSession` on every reload.** The session is now
  registered for cleanup with the config entry and closed during unload
  (and on first-refresh failure, to avoid leaking on setup errors).
- **Options flow had no effect until restart.** A reload listener has been
  added so changes apply immediately.
- Removed the deprecated `CONNECTION_CLASS` attribute from the config flow.
- Removed the unused `async_setup` boilerplate.

### Security / privacy

- Latitude and longitude are redacted automatically from diagnostics
  exports.
- Entry titles and unique IDs no longer expose exact coordinates (see
  *Breaking changes* and *Changed*).
- The integration uses HTTPS only, with default certificate verification.
  No credentials are handled, transmitted, or stored.

## [0.1.2] - earlier

Initial public versions. See git history for details.

[1.1.0]: https://github.com/lancer73/ha-buienalarm/releases/tag/v1.1.0
[1.0.4]: https://github.com/lancer73/ha-buienalarm/releases/tag/v1.0.4
[1.0.3]: https://github.com/lancer73/ha-buienalarm/releases/tag/v1.0.3
[1.0.2]: https://github.com/lancer73/ha-buienalarm/releases/tag/v1.0.2
[1.0.1]: https://github.com/lancer73/ha-buienalarm/releases/tag/v1.0.1
[1.0.0]: https://github.com/lancer73/ha-buienalarm/releases/tag/v1.0.0
[0.1.2]: https://github.com/lancer73/ha-buienalarm/commits/main/
