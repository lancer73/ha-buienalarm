"""BuienAlarm sensor platform."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import UnitOfVolumetricFlux
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import BuienAlarmConfigEntry
from .const import (
    ATTR_ATTRIBUTION,
    ATTR_NEXT_PERIOD,
    ATTR_NEXT_RAIN_FORECAST,
    ATTR_PERIOD_START,
    ATTR_RAIN_FORECAST,
    ATTRIBUTION,
    ATTRIBUTION_URL,
    DATA_LEVEL_HEAVY,
    DATA_LEVEL_LIGHT,
    DATA_LEVEL_MODERATE,
    DATA_NEXT_PERIOD,
    DATA_NEXT_RAIN_TEXT,
    DATA_PERIOD_START_TEXT,
    DATA_PRECIPITATION,
    DATA_SHOWER_END,
    DATA_SHOWER_START,
    DOMAIN,
)
from .coordinator import BuienAlarmDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class BuienAlarmSensorDescription(SensorEntityDescription):
    """Describe a BuienAlarm coordinator-backed sensor."""

    value_fn: Callable[[dict[str, Any]], Any]


# Native unit for the precipitation thresholds. The coordinator converts
# Buienradar's 0-255 byte values to mm/h before they reach the entities.
PRECIP_UNIT = UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR


# Rain-intensity thresholds.
#
# These report fixed constants (see const.LEVEL_*): Buienradar's nowcast has
# no server-supplied `levels` field, unlike the retired Buienalarm API.
# They therefore carry NO state_class — a value that never changes is
# configuration, not a measurement, and must not be recorded as statistics.
# They remain diagnostic entities so existing entity IDs and history survive.
LEVEL_DESCRIPTIONS: tuple[BuienAlarmSensorDescription, ...] = (
    BuienAlarmSensorDescription(
        key="level_light",
        translation_key="level_light",
        native_unit_of_measurement=PRECIP_UNIT,
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:weather-rainy",
        value_fn=lambda d: d.get(DATA_LEVEL_LIGHT),
    ),
    BuienAlarmSensorDescription(
        key="level_moderate",
        translation_key="level_moderate",
        native_unit_of_measurement=PRECIP_UNIT,
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:weather-pouring",
        value_fn=lambda d: d.get(DATA_LEVEL_MODERATE),
    ),
    BuienAlarmSensorDescription(
        key="level_heavy",
        translation_key="level_heavy",
        native_unit_of_measurement=PRECIP_UNIT,
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:weather-lightning-rainy",
        value_fn=lambda d: d.get(DATA_LEVEL_HEAVY),
    ),
)

TIMESTAMP_DESCRIPTIONS: tuple[BuienAlarmSensorDescription, ...] = (
    BuienAlarmSensorDescription(
        key="shower_start",
        translation_key="shower_start",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:weather-pouring",
        value_fn=lambda d: d.get(DATA_SHOWER_START),
    ),
    BuienAlarmSensorDescription(
        key="shower_end",
        translation_key="shower_end",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:weather-partly-rainy",
        value_fn=lambda d: d.get(DATA_SHOWER_END),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BuienAlarmConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the BuienAlarm sensors from a config entry."""
    coordinator = entry.runtime_data

    entities: list[SensorEntity] = [
        BuienAlarmStatusSensor(coordinator, entry.entry_id),
    ]

    for description in TIMESTAMP_DESCRIPTIONS + LEVEL_DESCRIPTIONS:
        entities.append(
            BuienAlarmGenericSensor(
                coordinator,
                entry.entry_id,
                description=description,
            )
        )

    async_add_entities(entities)


def _build_device_info(coordinator: BuienAlarmDataUpdateCoordinator) -> DeviceInfo:
    """Build the (single) DeviceInfo all entities for this entry share."""
    return DeviceInfo(
        identifiers={
            (
                DOMAIN,
                f"{round(coordinator.latitude, 3)}_"
                f"{round(coordinator.longitude, 3)}",
            )
        },
        name="Buien-Alarm",
        manufacturer="Buienradar",
        model="Rain forecast",
        entry_type=DeviceEntryType.SERVICE,
        configuration_url=ATTRIBUTION_URL,
    )


class BuienAlarmStatusSensor(
    CoordinatorEntity[BuienAlarmDataUpdateCoordinator], SensorEntity
):
    """Sensor showing the human-readable next-rain status."""

    _attr_has_entity_name = True
    _attr_translation_key = "next_rain"

    def __init__(
        self,
        coordinator: BuienAlarmDataUpdateCoordinator,
        entry_id: str,
    ) -> None:
        """Initialise the status sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_next_rain"
        self._attr_device_info = _build_device_info(coordinator)

    @property
    def native_value(self) -> str | None:
        """Return the state."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(DATA_NEXT_RAIN_TEXT)

    @property
    def icon(self) -> str:
        """Return the icon."""
        if not self.coordinator.data:
            return "mdi:weather-cloudy"
        if self.coordinator.data.get(DATA_NEXT_RAIN_TEXT) == self.coordinator.strings[
            "no_rain"
        ]:
            return "mdi:weather-sunny"
        return "mdi:weather-rainy"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes.

        raw_data is intentionally NOT exposed here; the full payload is
        available via the diagnostics download instead, which keeps the
        recorder small and avoids state attribute bloat.
        """
        data = self.coordinator.data
        if not data:
            # Attribution is contractual (Buienradar terms) and must be
            # present even before the first successful refresh.
            return {ATTR_ATTRIBUTION: ATTRIBUTION}
        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            ATTR_NEXT_RAIN_FORECAST: data.get(DATA_NEXT_RAIN_TEXT),
            ATTR_RAIN_FORECAST: data.get(DATA_PRECIPITATION, []),
            ATTR_NEXT_PERIOD: data.get(DATA_NEXT_PERIOD),
            ATTR_PERIOD_START: data.get(DATA_PERIOD_START_TEXT),
        }


class BuienAlarmGenericSensor(
    CoordinatorEntity[BuienAlarmDataUpdateCoordinator], SensorEntity
):
    """Generic coordinator-backed sensor driven by a description."""

    _attr_has_entity_name = True
    entity_description: BuienAlarmSensorDescription

    def __init__(
        self,
        coordinator: BuienAlarmDataUpdateCoordinator,
        entry_id: str,
        description: BuienAlarmSensorDescription,
    ) -> None:
        """Initialise the generic sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_device_info = _build_device_info(coordinator)

    @property
    def native_value(self) -> Any:
        """Return the value via the description's value_fn.

        Returning None causes HA to render the entity as 'unknown', which is
        the desired behaviour when the API does not provide the value.
        """
        if not self.coordinator.data:
            return None
        value = self.entity_description.value_fn(self.coordinator.data)
        # For timestamp sensors, only return real datetimes.
        if self.entity_description.device_class == SensorDeviceClass.TIMESTAMP:
            return value if isinstance(value, datetime) else None
        return value

    @callback
    def _handle_coordinator_update(self) -> None:
        """Forward coordinator updates."""
        self.async_write_ha_state()
