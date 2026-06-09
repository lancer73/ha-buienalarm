# CLAUDE.md

Guidance for AI assistants (Claude and others) working in this repository.
Read this before proposing changes. It documents how the integration is
structured, the conventions it follows, and the mistakes that are easy to
make here.

## What this is

A custom Home Assistant integration that exposes [BuienAlarm](https://www.buienalarm.nl/)
rain-forecast data as sensors. It is `cloud_polling`, has no external
dependencies (`requirements: []`), and ships via HACS as a custom repository.

There is no camera/radar-image feature; this is forecast data only.

## Repository layout

```
custom_components/buienalarm/
  __init__.py        # setup/unload, options-reload listener, config-entry migration
  config_flow.py     # user setup + options flow; has its OWN API connectivity check
  const.py           # all constants, LANGUAGE_STRINGS, resolve_language(), API header builder
  coordinator.py     # DataUpdateCoordinator: the main API fetch + forecast processing
  diagnostics.py     # redacted diagnostics download (no re-fetch; reads coordinator data)
  sensor.py          # entity definitions only; reads coordinator.data, makes NO requests
  manifest.json      # integration_type=service, iot_class=cloud_polling, version lives here
  strings.json       # config-flow strings
  translations/      # per-locale UI strings (entity names, config-flow labels)
  brand/             # integration card / device-page icons
CHANGES.md           # Keep a Changelog format; every release gets an entry + a link
README.md            # user-facing docs incl. an ApexCharts dashboard example
hacs.json            # HACS metadata (min HA version, country)
LICENSE              # MIT
```

## Architecture, in one paragraph

`__init__.async_setup_entry` creates a dedicated aiohttp session
(`create_session`, IPv4-only by default), builds the coordinator, does a
first refresh, stashes the coordinator on `entry.runtime_data`, and registers
both an options-update reload listener and a session-close callback via
`entry.async_on_unload`. The coordinator fetches from the BuienAlarm CDN,
validates the payload defensively, and turns it into a dict the entities
consume. `sensor.py` is purely declarative — it never calls the network.

## The single most important gotcha: the API is called from TWO places

1. `coordinator.py` → `_async_update_data` — the ongoing polling fetch.
2. `config_flow.py` → `_validate_api` — a one-shot connectivity check run
   when the user adds the integration. **This is a completely separate
   request** with its own session and its own copy of the request arguments.

Any change to how requests are made — headers, params, timeouts, the
endpoint, the session/connector — usually has to be applied in **both**
places or behaviour will diverge between "adding the integration" and
"running it". A real example: the fix for the CDN's HTTP 403 (browser-like
headers via `build_api_headers`) was first applied only to the coordinator,
and setup kept failing with "Failed to connect" because the config-flow
check still sent the default User-Agent. Always grep for the other caller:

```
grep -rn "session.get\|API_URL\|build_api_headers" custom_components/buienalarm/
```

`diagnostics.py` does NOT call the API — it serialises the last-known
coordinator data. Don't add a fetch there.

## Conventions to follow

- **Constants live in `const.py`.** Don't hard-code endpoints, timeouts,
  thresholds, header values, or data-dict keys in other modules. The data
  the coordinator passes to entities is keyed by the `DATA_*` constants; the
  state-attribute names exposed on entities are the `ATTR_*` constants.
- **Two separate string systems, do not merge them:**
  - `LANGUAGE_STRINGS` in `const.py` is the *state value* of the next-shower
    text sensor (e.g. "in 30 minutes"). The user picks this language in the
    config flow; it is independent of the HA UI locale. Look up via
    `resolve_language()`, which is case-insensitive and falls back
    exact → base language → English. Never index `LANGUAGE_STRINGS` directly
    with a raw user value (it will `KeyError`).
  - `translations/*.json` is for entity *names* and config-flow labels, and
    follows the HA UI locale. Entities set `_attr_has_entity_name = True` and
    a `translation_key`; they do NOT read names from `LANGUAGE_STRINGS`.
    (A historical bug read `strings["sensor_name"]`, which no longer exists —
    don't reintroduce name keys into `LANGUAGE_STRINGS`.)
- **Timezone-aware datetimes only.** Use `homeassistant.util.dt` (`dt_util`)
  for all time handling, never naive `datetime.now()`.
- **A 200 OK is not trusted blindly.** The coordinator coerces precipitation
  values defensively, validates payload shape, and turns any interpretation
  error into `UpdateFailed` so entities go unavailable instead of crashing.
  Preserve that posture when editing `_process`.
- **Async style:** `asyncio.timeout(...)` (not the deprecated
  `async_timeout`), `async with` for responses.

## Privacy / security posture (the maintainer cares about this — keep it)

- Latitude/longitude are the user's home. They are:
  - redacted from diagnostics (`TO_REDACT` in `diagnostics.py`),
  - rounded to 3 decimals (~110 m) in the config-entry `unique_id`,
  - rounded to 2 decimals (~1.1 km) in the entry title.
  Don't undo any of this, and don't log raw coordinates. Note the existing
  error messages deliberately avoid echoing the request URL/params.
- HTTPS only, default certificate verification. No credentials are handled.
- The browser-like headers in `build_api_headers()` are a workaround for the
  CDN's User-Agent filtering, not a security feature. `secrets.choice` is
  used over `random.choice` only to satisfy Ruff S311 — there is no
  cryptographic requirement.
- When adding any new user-input field, sanitise/validate it. Coordinates
  are cleaned by `_clean_coordinate` before `cv.latitude/longitude` to absorb
  pasted whitespace, newlines, comma decimals, and quotes.

## Versioning & releasing

- SemVer. Bug fix with no API/entity/breaking change → patch bump.
- The version string lives ONLY in `manifest.json`. (The "1.1.0" near the top
  of `CHANGES.md` is the Keep-a-Changelog format version, not the project
  version — leave it.)
- Every release: add a dated `CHANGES.md` entry in the existing style
  (`### Added/Changed/Fixed/Notes/Security`), and add the matching
  `[x.y.z]: .../releases/tag/vx.y.z` reference link at the bottom.
- HACS needs a matching git tag (`vx.y.z`); a manifest bump alone does not
  push an update to existing users.
- Config-flow schema changes that affect stored data need a `VERSION` bump in
  `BuienAlarmConfigFlow` plus an `async_migrate_entry` path (see the 1→2
  migration in `__init__.py` for the pattern, including entity-registry
  unique_id rewrites).

## Before you hand back changes

- `python -m py_compile` the files you touched.
- `ruff check` them if available; this repo's style is Ruff-clean (it follows
  HA core conventions: import ordering with lowercase names after all-caps in
  `from .const import (...)`, two blank lines before module-level defs,
  `logging.exception`/`exc_info=True` rather than bare `logging.error` in
  except blocks).
- Show the user a real diff against the file on disk, not a description.
- If you can't see a file, ask for it or read it — do not reconstruct code
  from the GitHub web render (whitespace is not reliable there).
