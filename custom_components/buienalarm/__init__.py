"""The BuienAlarm integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import (
    CONF_LANGUAGE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_SCAN_INTERVAL,
    DEFAULT_LANGUAGE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import BuienAlarmDataUpdateCoordinator, create_session

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

# Typed alias: stash the coordinator on the config entry's runtime_data.
type BuienAlarmConfigEntry = ConfigEntry[BuienAlarmDataUpdateCoordinator]


async def async_setup_entry(
    hass: HomeAssistant, entry: BuienAlarmConfigEntry
) -> bool:
    """Set up BuienAlarm from a config entry."""
    latitude: float = entry.data[CONF_LATITUDE]
    longitude: float = entry.data[CONF_LONGITUDE]
    scan_interval: int = entry.options.get(
        CONF_SCAN_INTERVAL,
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )
    language: str = entry.options.get(
        CONF_LANGUAGE,
        entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
    )

    session = create_session(use_ipv4_only=True)

    coordinator = BuienAlarmDataUpdateCoordinator(
        hass,
        config_entry=entry,
        latitude=latitude,
        longitude=longitude,
        scan_interval=scan_interval,
        language=language,
        session=session,
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        # Make sure we don't leak the session if first refresh fails.
        await session.close()
        raise

    entry.runtime_data = coordinator

    # Reload the entry whenever options change so scan interval / language
    # changes take effect without an HA restart.
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    # Close the session on unload.
    async def _close_session() -> None:
        await session.close()

    entry.async_on_unload(_close_session)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: BuienAlarmConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(
    hass: HomeAssistant, entry: BuienAlarmConfigEntry
) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Migrate an old config entry to the current schema.

    Version history:
      1 -> 2 (1.0.0 release):
          - Round latitude/longitude in the config-entry unique_id to 3
            decimals (~110 m) so registry exports do not pinpoint the
            user's home address.
          - Migrate sensor entity unique_ids from the legacy
            ``buienalarm_next_rain_<lat>_<lon>`` form to
            ``<entry_id>_next_rain`` so history is preserved across the
            naming-scheme change introduced in 1.0.0.
    """
    _LOGGER.debug(
        "Migrating BuienAlarm entry %s from version %s",
        entry.entry_id,
        entry.version,
    )

    if entry.version > 2:
        # Downgrade is not supported.
        return False

    if entry.version == 1:
        latitude = entry.data.get(CONF_LATITUDE)
        longitude = entry.data.get(CONF_LONGITUDE)

        # Defensive: if the entry is malformed we skip the unique_id rewrite
        # but still bump the version so we don't loop. The setup itself will
        # surface the underlying problem.
        new_unique_id: str | None = None
        if latitude is not None and longitude is not None:
            new_unique_id = f"{round(float(latitude), 3)}_{round(float(longitude), 3)}"

        # 1) Rename legacy sensor entity unique_ids in the entity registry.
        # The old format was: buienalarm_next_rain_<lat>_<lon>
        # The new format is:  <entry_id>_next_rain
        registry = er.async_get(hass)
        legacy_prefix = "buienalarm_next_rain_"
        new_next_rain_id = f"{entry.entry_id}_next_rain"

        # Only entries belonging to this config entry — avoids touching
        # registrations from other domains that happen to collide.
        entries_for_this = er.async_entries_for_config_entry(
            registry, entry.entry_id
        )
        for reg_entry in entries_for_this:
            if reg_entry.unique_id == new_next_rain_id:
                # Already migrated.
                continue
            if reg_entry.unique_id.startswith(legacy_prefix):
                # Guard against a (very unlikely) collision: another entity
                # already has the new unique_id.
                existing = registry.async_get_entity_id(
                    reg_entry.domain, DOMAIN, new_next_rain_id
                )
                if existing and existing != reg_entry.entity_id:
                    _LOGGER.warning(
                        "Cannot migrate %s to unique_id %s: already taken by %s",
                        reg_entry.entity_id,
                        new_next_rain_id,
                        existing,
                    )
                    continue
                _LOGGER.info(
                    "Migrating sensor unique_id %s -> %s",
                    reg_entry.unique_id,
                    new_next_rain_id,
                )
                registry.async_update_entity(
                    reg_entry.entity_id, new_unique_id=new_next_rain_id
                )

        # 2) Rewrite the config-entry unique_id and bump the version.
        hass.config_entries.async_update_entry(
            entry,
            unique_id=new_unique_id if new_unique_id is not None else entry.unique_id,
            version=2,
        )

    _LOGGER.info(
        "BuienAlarm entry %s migrated to version %s",
        entry.entry_id,
        entry.version,
    )
    return True
