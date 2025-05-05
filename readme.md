# BuienAlarm Integration for Home Assistant

This integration uses the BuienAlarm API to create a sensor that displays the time of the next rain shower, with all forecast data included in the sensor attributes.

## Features

- Displays the time of the next rain shower
- Includes full forecast data in the sensor attributes
- Configurable scan interval
- Bilingual: supports both Dutch and English
- User-friendly configuration through the Home Assistant UI

## Installation

### Method 1: HACS (Custom repository)

1. Make sure [HACS](https://hacs.xyz/) is installed.
2. Go to HACS > Integrations > Menu (top right) > Custom repositories.
3. Add the URL of your repository and select "Integration" as the category.
4. Click "Add".
5. Search for "BuienAlarm" in the HACS store and install it.

### Method 2: Manual installation

1. Create a `custom_components/buienalarm` directory in your Home Assistant config directory.
2. Copy all files from this repository to the `custom_components/buienalarm` directory.
3. Restart Home Assistant.

## Configuration

After installation, you can add the integration through:

1. Go to Configuration > Integrations > Add Integration.
2. Search for "BuienAlarm" and select it.
3. Enter the required information:
   - **Latitude**: The latitude of your location
   - **Longitude**: The longitude of your location
   - **Scan interval**: How often the data should be refreshed (in minutes)
   - **Language**: Choose Dutch or English

## Usage

The sensor will display the time of the next rain shower, or "No rain expected" if no rain is forecast. The sensor will be named "BuienAlarm Volgende Bui" in Dutch or "BuienAlarm Next Rain" in English.

The sensor contains the following attributes:
- `next_rain_forecast`: Time of the next rain shower
- `rain_forecast`: A list of all forecast data, with each item containing:
  - `precip`: The expected precipitation in mm/h
  - `attime`: The timestamp for this forecast
- `raw_data`: The complete raw data from the BuienAlarm API

## Example Automations

```yaml
# Send notification when rain is expected within 30 minutes
automation:
  - alias: "Rain warning"
    trigger:
      - platform: state
        entity_id: sensor.buienalarm_next_rain
    condition:
      - condition: template
        value_template: >
          {{ not is_state('sensor.buienalarm_next_rain', 'No rain expected') and 
             not is_state('sensor.buienalarm_next_rain', 'Geen regen verwacht') }}
    action:
      - service: notify.mobile_app
        data:
          message: "Rain is coming: {{ states('sensor.buienalarm_next_rain') }}"
```

## Troubleshooting

If you're having issues with this integration:

1. Check your Home Assistant logs for error messages
2. Check if your internet connection is working
3. Verify that the entered coordinates are correct

## Error Handling

The integration includes robust error handling:
- Timeout protection for API calls
- HTTP status code checks
- JSON parsing error handling
- Empty data handling
- Graceful degradation when the service is temporarily unavailable

## Rain chart for dashboard
```yaml
type: custom:apexcharts-card
graph_span: 2h
span:
  start: minute
  offset: "-10m"
now:
  show: true
  label: Nu
header:
  show: false
yaxis:
  - decimals: 2
    min: 0
apex_config:
  legend:
    show: false
  grid:
    yaxis:
      lines:
        show: false
  xaxis:
    tooltip:
      enabled: false
  chart:
    height: 200px
series:
  - entity: sensor.buienalarm_volgende_bui
    stroke_width: 6
    float_precision: 2
    name: Voorspelling
    type: column
    opacity: 1
    color: royalblue
    data_generator: |
      return entity.attributes.rain_forecast.map((data, index) => {
        return [new Date(data['attime']*1000), data['precip']];
      });
  - entity: sensor.buienalarm_volgende_bui
    float_precision: 2
    type: line
    name: licht
    stroke_width: 2
    stroke_dash: 4
    show:
      legend_value: false
    color: green
    opacity: 1
    data_generator: |
      return entity.attributes.rain_forecast.map((data, index) => {
        return [new Date(data['attime']*1000), entity.attributes.raw_data.levels.light];
      });
  - entity: sensor.buienalarm_volgende_bui
    float_precision: 2
    type: line
    name: gemiddeld
    stroke_width: 2
    stroke_dash: 4
    color: orange
    show:
      legend_value: false
    opacity: 1
    data_generator: |
      return entity.attributes.rain_forecast.map((data, index) => {
        return [new Date(data['attime']*1000), entity.attributes.raw_data.levels.moderate];
      });
  - entity: sensor.buienalarm_volgende_bui
    float_precision: 2
    type: line
    name: zwaar
    show:
      legend_value: false
    stroke_width: 2
    stroke_dash: 4
    color: red
    opacity: 1
    data_generator: |
      return entity.attributes.rain_forecast.map((data, index) => {
        return [new Date(data['attime']*1000), entity.attributes.raw_data.levels.heavy];
      });
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
