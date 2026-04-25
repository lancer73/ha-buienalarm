# BuienAlarm Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Version](https://img.shields.io/github/v/release/lancer73/ha-buienalarm)](https://github.com/lancer73/ha-buienalarm/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A Home Assistant integration that uses the BuienAlarm API to provide rain
forecast data for any location in the Netherlands.

> **Disclaimer.** This is an unofficial community integration. It is not
> affiliated with or endorsed by BuienAlarm. The brand icons shipped in
> `custom_components/buienalarm/brand/` are generic rain-cloud graphics, not
> the BuienAlarm trademark.

## Features

- **Next shower** sensor with a human-readable status (Dutch or English)
- **Next shower start** sensor with `device_class: timestamp`
- **Current shower end** sensor with `device_class: timestamp`
- **Rain-intensity threshold** sensors (`level_light`, `level_moderate`,
  `level_heavy`) with unit `mm/h`
- Configurable through the Home Assistant UI (config flow + options flow)
- Diagnostics support — download a JSON dump of the integration state for
  troubleshooting, with latitude/longitude redacted automatically
- Bilingual UI (Dutch and English)
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
4. Search for *BuienAlarm* in the HACS store and install it.
5. Restart Home Assistant.

### Method 2 — Manual

1. Copy the `custom_components/buienalarm/` directory from this repository
   into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

## Configuration

After installation:

1. Go to *Settings → Devices & services → Add integration*.
2. Search for *BuienAlarm* and select it.
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
| Light threshold          | Drempel licht            | mm/h      | Light-rain threshold reported by the API                           |
| Moderate threshold       | Drempel gemiddeld        | mm/h      | Moderate-rain threshold                                            |
| Heavy threshold          | Drempel zwaar            | mm/h      | Heavy-rain threshold                                               |

The next-shower sensor exposes these state attributes:

- `next_rain_forecast` — same value as the state, for templating
- `rain_forecast` — list of `{precip: mm/h, attime: unix_ts}` entries
  covering the full forecast window
- `period_type` — `wet` (next shower coming), `dry` (current shower will
  end), or `nan` (no transition in window)
- `period_start` — clock time string (`HH:MM`) of the upcoming transition

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

Open *Settings → Devices & services → BuienAlarm* and click your device to
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

![BuienAlarm Card screenshot](https://raw.githubusercontent.com/lancer73/lovelace-buienalarm-card/main/images/screenshot.png)

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

- All API calls are HTTPS with default certificate verification.
- No credentials are required, transmitted, or stored.
- Latitude and longitude are **redacted** from the diagnostics download.
- The config-entry `unique_id` and entry title are based on coordinates
  rounded to ~110 m and ~1.1 km respectively, so a registry export does not
  pinpoint your home address.
- Existing entries from earlier versions are migrated to the rounded
  unique_id format automatically on first load.

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

1. Open *Settings → Devices & services → BuienAlarm → ⋮ → Download
   diagnostics* and inspect the JSON. Latitude, longitude, and any other
   sensitive fields are redacted.
2. Enable debug logging via *Settings → Devices & services → BuienAlarm →
   ⋮ → Enable debug logging*, reproduce the issue, then disable debug
   logging — Home Assistant will offer the log file as a download.
3. Verify your internet connection and that the configured coordinates fall
   within the BuienAlarm coverage area (the Netherlands and immediately
   surrounding regions).
4. Check the Home Assistant log for messages from the `buienalarm` logger.

## Related projects

- [**lovelace-buienalarm-card**](https://github.com/lancer73/lovelace-buienalarm-card)
  — Lovelace card that visualises this integration's sensors. HACS
  *Dashboard* category. Optional, but recommended.

## License

This project is licensed under the MIT License — see the [`LICENSE`](LICENSE)
file for details.

The BuienAlarm name and any official trademarks belong to their respective
owners. This integration is an unofficial client of BuienAlarm's public
forecast API.
