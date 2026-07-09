# Buien-Alarm Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Version](https://img.shields.io/github/v/release/lancer73/ha-buienalarm)](https://github.com/lancer73/ha-buienalarm/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Buien-Alarm is a Home Assistant integration that provides short-term rain
forecast data for any location in the Netherlands: precipitation intensity in
5-minute steps over the next two hours.

**Weather forecast data provided by [Buienradar.nl](https://www.buienradar.nl/).**

> **Data source changed in 1.2.0.** Buien-Alarm originally used the Buienalarm
> API. That endpoint (`cdn-secure.buienalarm.nl`) was retired when the
> Buienalarm website was rebuilt, and no public replacement was made
> available. Since 1.2.0 the integration sources its forecast from
> Buienradar's free, keyless `raintext` nowcast instead. No API key is
> required and no action is needed when upgrading — see
> [Upgrading to 1.2.0](#upgrading-to-120).

> **Disclaimer.** This is an unofficial community integration. It is not
> affiliated with or endorsed by Buienradar, Buienalarm, or Infoplaza. The
> brand icons shipped in `custom_components/buienalarm/brand/` are generic
> rain-cloud graphics, not anyone's trademark. The integration's domain
> remains `buienalarm` for backwards compatibility with existing installs.

## Features

- **Next shower** sensor with a human-readable status (Dutch or English)
- **Next shower start** sensor with `device_class: timestamp`
- **Current shower end** sensor with `device_class: timestamp`
- **Rain-intensity threshold** sensors (`level_light`, `level_moderate`,
  `level_heavy`) with unit `mm/h` — diagnostic entities reporting fixed
  threshold constants
- Configurable through the Home Assistant UI (config flow + options flow)
- Diagnostics support — download a JSON dump of the integration state for
  troubleshooting, with latitude/longitude redacted automatically
- Multilingual UI — see [Translations](#translations) below for the
  full list of supported languages and how to contribute
- Companion Lovelace card available as a separate HACS install — see
  [Dashboard card](#dashboard-card) below

For the Dutch version of this README, see [`installation.md`](installation.md).

## Requirements

- Home Assistant 2024.12 or newer

## Installation

### Method 1 — HACS (recommended)

1. Make sure [HACS](https://hacs.xyz/) is installed.
2. In HACS, open the menu (top right) → *Custom repositories*.
3. Add `https://github.com/lancer73/ha-buienalarm` with category
   *Integration*.
4. Search for *Buien-Alarm* in the HACS store and install it.
5. Restart Home Assistant.

### Method 2 — Manual

1. Copy the `custom_components/buienalarm/` directory from this repository
   into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

## Configuration

After installation:

1. Go to *Settings → Devices & services → Add integration*.
2. Search for *Buien-Alarm* and select it.
3. Provide:
   - **Latitude** and **Longitude** of the location to forecast for
   - **Scan interval** — how often to refresh data (3–60 minutes, default 5)
   - **Language** — Dutch or English

The integration validates the API call before creating the entry, so an
invalid location or a connectivity problem is reported immediately.

The scan interval and language can be changed afterwards via the integration
card's *Configure* button. Changes are applied immediately without an HA
restart.

## Entities

A single device is created per configured location, exposing six sensors:

| Sensor (English UI)      | Sensor (Dutch UI)        | Type      | Description                                                        |
|--------------------------|--------------------------|-----------|--------------------------------------------------------------------|
| Next shower              | Volgende bui             | text      | Human-readable status, e.g. "14:25 (in 30 minutes)"                |
| Next shower start        | Start volgende bui       | timestamp | When the next shower starts; `unknown` if none in window           |
| Current shower end       | Einde huidige bui        | timestamp | When the ongoing/upcoming shower ends; `unknown` if none in window |
| Light threshold          | Drempel licht            | mm/h      | Light-rain threshold — fixed at `0.1` (diagnostic)                 |
| Moderate threshold       | Drempel gemiddeld        | mm/h      | Moderate-rain threshold — fixed at `1.0` (diagnostic)              |
| Heavy threshold          | Drempel zwaar            | mm/h      | Heavy-rain threshold — fixed at `10.0` (diagnostic)                |

> The three threshold sensors report **fixed constants**, not measured
> values. The former Buienalarm API supplied them in its payload; Buienradar's
> nowcast has no equivalent field. They are marked as *diagnostic* entities
> and deliberately carry no `state_class`, so Home Assistant does not record
> them as measurement statistics. They exist so that existing entity IDs,
> automations, and history remain intact.

The next-shower sensor exposes these state attributes:

- `next_rain_forecast` — same value as the state, for templating
- `rain_forecast` — list of `{precip: mm/h, attime: unix_ts}` entries
  covering the full forecast window
- `period_type` — `wet` (next shower coming), `dry` (current shower will
  end), or `nan` (no transition in window)
- `period_start` — clock time string (`HH:MM`) of the upcoming transition
- `attribution` — required source credit for Buienradar

> The `raw_data` attribute that earlier versions exposed has been **removed
> in 1.0.0**. The full upstream payload is now available through the
> *Download diagnostics* button on the integration card.

### Finding your entity IDs

Entity IDs are derived from the device name and your locale, so the exact ID
depends on which language you picked. Examples:

- English: `sensor.buienalarm_next_shower`,
  `sensor.buienalarm_next_shower_start`,
  `sensor.buienalarm_current_shower_end`,
  `sensor.buienalarm_light_threshold`,
  `sensor.buienalarm_moderate_threshold`,
  `sensor.buienalarm_heavy_threshold`
- Dutch: `sensor.buienalarm_volgende_bui`,
  `sensor.buienalarm_start_volgende_bui`,
  `sensor.buienalarm_einde_huidige_bui`,
  `sensor.buienalarm_drempel_licht`,
  `sensor.buienalarm_drempel_gemiddeld`,
  `sensor.buienalarm_drempel_zwaar`

Open *Settings → Devices & services → Buien-Alarm* and click your device to
see the entity IDs that were actually created on your install. The YAML
examples below assume the English IDs — adjust them for your install.

## Example automation

```yaml
automation:
  - alias: "Rain warning"
    trigger:
      - platform: state
        entity_id: sensor.buienalarm_next_shower_start
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.state not in ['unknown', 'unavailable'] }}"
    action:
      - service: notify.mobile_app
        data:
          title: "Rain incoming"
          message: >
            Next shower starts at
            {{ as_timestamp(states('sensor.buienalarm_next_shower_start'))
               | timestamp_custom('%H:%M') }}.
```

The previous "trigger on every state change of the status sensor" pattern
still works, but the timestamp sensor is the cleaner trigger because it only
fires when an actual transition is detected and never on every text-format
update.

## Dashboard card

A companion Lovelace card is available as a separate HACS install:
[**lovelace-buienalarm-card**](https://github.com/lancer73/lovelace-buienalarm-card).
It pairs with this integration and reads its sensors directly — no
templating or `data_generator` needed.

![Buien-Alarm Card screenshot](https://raw.githubusercontent.com/lancer73/lovelace-buienalarm-card/main/images/screenshot.png)

Install it via HACS (*Custom repositories → category Dashboard*), then add
the card from the Lovelace card picker. Minimal YAML:

```yaml
type: custom:buienalarm-card
next_shower_sensor: sensor.buienalarm_next_shower
light: sensor.buienalarm_light_threshold
moderate: sensor.buienalarm_moderate_threshold
heavy: sensor.buienalarm_heavy_threshold
```

Full configuration options, screenshots, and YAML examples are in the
card's [README](https://github.com/lancer73/lovelace-buienalarm-card#readme).

### Without the companion card

If you'd rather not install another HACS package, the integration's
sensors work with any standard Lovelace card. A simple entities card:

```yaml
type: entities
title: Rain forecast
entities:
  - entity: sensor.buienalarm_next_shower
  - entity: sensor.buienalarm_next_shower_start
  - entity: sensor.buienalarm_current_shower_end
```

For a chart, the `apexcharts-card` community card works well too: configure
all series against the next-shower sensor, drive the time axis from its
`rain_forecast` attribute, and read each threshold value with
`hass.states['sensor.buienalarm_light_threshold'].state` (and similarly for
`moderate`/`heavy`) inside the series' `data_generator`. The companion card
above does this and more, with a visual editor — recommended unless you
specifically want the `apexcharts-card` look.

## Privacy and security

- All API calls are HTTPS with default certificate verification, to
  `gpsgadget.buienradar.nl`.
- No credentials or API keys are required, transmitted, or stored.
- Your coordinates are sent to Buienradar with each poll — this is inherent
  to requesting a location-specific forecast. They are rounded to four
  decimals (~11 m) in the request.
- Latitude and longitude are **redacted** from the diagnostics download.
- The config-entry `unique_id` and entry title are based on coordinates
  rounded to ~110 m and ~1.1 km respectively, so a registry export does not
  pinpoint your home address.
- Existing entries from earlier versions are migrated to the rounded
  unique_id format automatically on first load.

## Translations

The integration supports the following languages for **state text** (the
human-readable status of the next-shower sensor, e.g. "in 30 minutes" /
"over 30 minuten") and for the **Home Assistant UI** (entity names,
config-flow labels):

`nl` (Dutch), `en` (English), `fr` (French), `es` (Spanish),
`pt` (Portuguese, Portugal), `pt-BR` (Portuguese, Brazil), `fy` (West
Frisian / Frysk), `tr` (Turkish), `ar` (Arabic, Modern Standard),
`de` (German), `de-CH` (Swiss German).

The state-text language follows the `language` config option chosen by the
user. The HA UI labels follow the user's HA UI locale, with a fallback
chain: exact match → base language (e.g. `pt-PT` → `pt`, `de-AT` → `de`)
→ English.

### Help wanted: native-speaker review

The translations for every language other than Dutch and English were
produced as **machine-quality starting points** and have not yet been
reviewed by native speakers. They are functional, but a native speaker
will inevitably notice clumsy phrasing or better word choices.

**If you are a native speaker of any of these languages, contributions
are warmly welcomed**, no matter how small:

- Strings to review live in two places: `custom_components/buienalarm/const.py`
  (the `LANGUAGE_STRINGS` dict — five state-text strings per language),
  and `custom_components/buienalarm/translations/<locale>.json` (the
  HA UI translations — about a dozen strings).
- Open a pull request with your suggested edits, or open an issue if
  you'd rather discuss specific phrasing first. Reviews of just one or
  two strings are valuable too — please don't feel you have to fix
  every string at once.
- If your language isn't on the list and you'd like to add it, both
  files take new entries cleanly; an issue or PR to start the
  conversation is welcome.

### Notes on what isn't included

- **`de-AT` (Austrian German)** is not a separate locale. Standard German
  is used; the few Austria-specific words don't appear in any of these
  strings. HA UIs configured to `de-AT` fall through to `de`.
- **Moroccan Darija** is not included. Morocco's written language is
  Modern Standard Arabic, which is available as `ar`. Spoken Darija
  has no commonly-used locale code and no HA support.

## Upgrading to 1.2.0

Version 1.2.0 switches the data source from the retired Buienalarm API to
Buienradar's `raintext` nowcast.

**No action is required.** There is no API key to obtain, your configured
location is unchanged, and all entity IDs stay the same. Automations and
history continue to work.

What changes in behaviour:

- The three threshold sensors (`level_light`, `level_moderate`,
  `level_heavy`) now report fixed constants (`0.1`, `1.0`, `10.0` mm/h)
  rather than values supplied by the API, and are no longer recorded as
  measurement statistics. Existing recorded history is retained but the
  values will stop varying.
- The forecast window is two hours in 5-minute steps. This matches what the
  previous API provided in practice.
- The `raw` payload in the diagnostics download is now the plain-text
  Buienradar response rather than a JSON object.

Attribution to Buienradar is required by their terms of use and is surfaced
automatically in the `attribution` state attribute and on the device page.
Please leave it in place.

## Upgrading from 0.1.x

Upgrade in place via HACS. On first restart the integration will:

1. Migrate the legacy `buienalarm_next_rain_<lat>_<lon>` sensor to the new
   ID scheme — your **history is preserved**.
2. Round the entry's `unique_id` so coordinates aren't exposed in registry
   exports.
3. Bump the entry version from 1 to 2.

If your dashboards reference the `raw_data` attribute (e.g. an older
`apexcharts-card` example reading `attributes.raw_data.levels.light`),
update them to read from the dedicated threshold sensors instead, or
install the [companion card](#dashboard-card) which handles this for you.
The status sensor's other attributes (`rain_forecast`, `period_type`,
`period_start`, `next_rain_forecast`) are unchanged.

See [`CHANGES.md`](CHANGES.md) for the full changelog.

## Troubleshooting

If the integration is not working as expected:

1. Open *Settings → Devices & services → Buien-Alarm → ⋮ → Download
   diagnostics* and inspect the JSON. Latitude, longitude, and any other
   sensitive fields are redacted.
2. Enable debug logging via *Settings → Devices & services → Buien-Alarm →
   ⋮ → Enable debug logging*, reproduce the issue, then disable debug
   logging — Home Assistant will offer the log file as a download.
3. Verify your internet connection and that the configured coordinates fall
   within the Buienradar coverage area (the Netherlands and immediately
   surrounding regions).
4. Check the Home Assistant log for messages from the `buienalarm` logger.

## Related projects

- [**lovelace-buienalarm-card**](https://github.com/lancer73/lovelace-buienalarm-card)
  — Lovelace card that visualises this integration's sensors. HACS
  *Dashboard* category. Optional, but recommended. Unaffected by the 1.2.0
  data-source change.

## License

This project is licensed under the MIT License — see the [`LICENSE`](LICENSE)
file for details.

Weather forecast data is provided by [Buienradar.nl](https://www.buienradar.nl/).
Use of that data is subject to Buienradar's terms of use, which require
attribution; the integration surfaces this credit automatically and it should
not be removed.

The Buienalarm and Buienradar names and any official trademarks belong to
their respective owners. This integration is an unofficial client and is not
affiliated with either.
