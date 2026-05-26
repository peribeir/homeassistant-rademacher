"""Integration for Rademacher Bridge."""
import asyncio
from datetime import timedelta
import logging

from homepilot.api import AuthError, HomePilotApi
from homepilot.hub import HomePilotHub
from homepilot.manager import HomePilotManager

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_API_VERSION,
    CONF_DEVICES,
    CONF_EXCLUDE,
    CONF_HOST,
    CONF_PASSWORD,
    CONF_SENSOR_TYPE,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import (
    DeviceEntry,
    DeviceRegistry,
    format_mac,
)
from homeassistant.helpers.entity_registry import async_migrate_entries
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN,
    CONF_ENABLE_CYCLIC_SCENE_POLLING,
    CONF_INCLUDE_NON_EXECUTABLE_SCENES,
    CONF_INVERT_COVER_POSITION,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    CONF_SCENE_UPDATE_INTERVAL,
    DEFAULT_SCENE_UPDATE_INTERVAL,
)

# List of platforms to support. There should be a matching .py file for each,
# eg <cover.py> and <sensor.py>
PLATFORMS = ["cover", "button", "switch", "sensor", "binary_sensor", "climate", "light", "number", "update", "scene"]

_LOGGER = logging.getLogger(__name__)


async def async_migrate_entry(hass, config_entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.info("Migrating from version %s", config_entry.version)

    #  Flatten configuration but keep old data if user rollbacks HASS prior to 0.106
    if config_entry.version == 1:
        api = HomePilotApi(config_entry.data[CONF_HOST], config_entry.data[CONF_PASSWORD])
        try:
            host = config_entry.data[CONF_HOST]
            mac_address = format_mac(await HomePilotHub.get_hub_macaddress(api))
            nodename = (await api.async_get_nodename())["nodename"]
        except AuthError:
            _LOGGER.error("Cannot migrate config entry. Authentication error. Please delete integration and restart HomeAssistant.")
            return False
        except Exception as err:
            _LOGGER.error("Cannot migrate config entry (%s). Check if bridge is online and restart Home Assistant. If problem persists, delete integration and restart HomeAssistant.", err)
            return False

        @callback
        def update_unique_id(entity_entry):
            """Update unique ID of entity entry."""
            new_unique_id = entity_entry.unique_id.replace(
                host, mac_address
            )
            if new_unique_id == entity_entry.unique_id:
                return None
            return {
                "new_unique_id": entity_entry.unique_id.replace(
                    host, mac_address
                )
            }

        await async_migrate_entries(hass, config_entry.entry_id, update_unique_id)

        hass.config_entries.async_update_entry(
            config_entry, title=f"{nodename} ({mac_address})", unique_id=mac_address, data=config_entry.data, options=config_entry.options, version=2
        )

    if config_entry.version == 2:
        @callback
        def update_scene_unique_id(entity_entry):
            # Only migrate scene entities with old format
            if entity_entry.unique_id.startswith("scene_") and not entity_entry.unique_id.startswith(f"{config_entry.unique_id}_scene_"):
                new_unique_id = f"{config_entry.unique_id}_{entity_entry.unique_id}"
                _LOGGER.info("Migrating scene entity unique_id from %s to %s", entity_entry.unique_id, new_unique_id)
                return {"new_unique_id": new_unique_id}
            return None

        await async_migrate_entries(hass, config_entry.entry_id, update_scene_unique_id)
        hass.config_entries.async_update_entry(config_entry, version=3)

    _LOGGER.info("Migration to version %s successful", config_entry.version)

    return True

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Rademacher component."""
    # Ensure our name space for storing objects is a known type. A dict is
    # common/preferred as it allows a separate instance of your class for each
    # instance that has been created in the UI.
    hass.data.setdefault(DOMAIN, {})

    return True



async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Rademacher from a config entry."""
    # Store an instance of the "connecting" class that does the work of speaking
    # with your actual devices.
    api = HomePilotApi(
        entry.data[CONF_HOST],
        entry.data.get(CONF_PASSWORD, ""),
        entry.data.get(CONF_API_VERSION, 1),
    )

    try:
        # Check if include non executable scenes is enabled
        include_non_manual = entry.options.get(CONF_INCLUDE_NON_EXECUTABLE_SCENES, False)
        manager = await HomePilotManager.async_build_manager(api, include_non_manual_executable=include_non_manual)
    except AuthError as err:
        # Raising ConfigEntryAuthFailed will cancel future updates
        # and start a config flow with SOURCE_REAUTH (async_step_reauth)
        await api.async_close()
        raise ConfigEntryAuthFailed from err
    except Exception as err:
        await api.async_close()
        raise ConfigEntryNotReady from err

    _LOGGER.info("%s - Manager instance created, found %s devices and %s scenes with config version: %s", entry.title, len(manager.devices), len(manager.scenes), entry.version)
    _LOGGER.debug("Device IDs: %s", list(manager.devices))
    _LOGGER.debug("Scene IDs: %s", list(manager.scenes))

    update_interval = entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    update_timeout = min(update_interval - 2, 10)

    async def async_update_data():
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with asyncio.timeout(update_timeout):
                _LOGGER.info("%s - Updating states for %s devices with %s-second timeout every %s-second interval", entry.title, len(manager.devices), update_timeout, update_interval)
                return await manager.update_states()
        except AuthError as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            raise ConfigEntryAuthFailed from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="rademacher",
        update_method=async_update_data,
        update_interval=timedelta(seconds=update_interval),
    )

    scene_update_interval = entry.options.get(CONF_SCENE_UPDATE_INTERVAL, DEFAULT_SCENE_UPDATE_INTERVAL)
    scene_update_timeout = min(scene_update_interval - 2, 10)
    async def async_update_scene_data():
        """Fetch data from API endpoint.
        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with asyncio.timeout(scene_update_timeout):
                _LOGGER.info("%s - Updating states for %s scenes with %s-second timeout every %s-second interval", entry.title, len(manager.scenes), scene_update_timeout, scene_update_interval)
                return await manager.async_update_scenes()
        except AuthError as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            raise ConfigEntryAuthFailed from err

    enable_cyclic_scene_polling = entry.options.get(CONF_ENABLE_CYCLIC_SCENE_POLLING, False)    
    scene_coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="rademacher_scene",
        update_method=async_update_scene_data,
        update_interval=timedelta(seconds=scene_update_interval) if enable_cyclic_scene_polling else None,
    )

    if enable_cyclic_scene_polling:
        _LOGGER.info("%s - Cyclic scene polling enabled with %s-second interval", entry.title, scene_update_interval)
    else:
        _LOGGER.info("%s - Cyclic scene polling disabled, scenes will be static", entry.title)

    # Backward compatibility
    entry_options = {key: entry.options[key] for key in entry.options}
    if CONF_EXCLUDE not in entry.options:
        if CONF_DEVICES in entry.options:
            entry_options[CONF_EXCLUDE] = [
                did for did in manager.devices if did not in entry.options[CONF_DEVICES]
            ]
        else:
            entry_options[CONF_EXCLUDE] = []
    if CONF_SENSOR_TYPE not in entry.options:
        entry_options[CONF_SENSOR_TYPE] = []
    if CONF_INVERT_COVER_POSITION not in entry.options:
        entry_options[CONF_INVERT_COVER_POSITION] = False

    hass.data[DOMAIN][entry.entry_id] = (
        manager,
        coordinator,
        entry.data,
        entry_options,
        scene_coordinator,
    )

    await coordinator.async_config_entry_first_refresh()
    await scene_coordinator.async_config_entry_first_refresh()

    entry.async_on_unload(entry.add_update_listener(update_listener))

    # Deleting excluded devices
    device_registry: DeviceRegistry = dr.async_get(hass)
    for did in entry.options[CONF_EXCLUDE]:
        device_entry: DeviceEntry = device_registry.async_get_device({(DOMAIN, did)})
        if device_entry is not None:
            _LOGGER.info("Deleting device %s", did)
            device_registry.async_remove_device(device_entry.id)

    # Remove stale devices not present in the API
    api_device_ids = set(manager.devices)
    _LOGGER.debug("Devices in API: %s", api_device_ids)

    registered_devices = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    for device_entry in registered_devices:
        device_did = None
        for domain, identifier in device_entry.identifiers:
            if domain == DOMAIN:
                if identifier == f"{entry.unique_id}_bridge" or identifier.endswith("_bridge"):
                    # Keep the hub/bridge device
                    device_did = None
                    break

                if "_" in identifier:
                    parts = identifier.split("_")
                    if parts[-1] == "bridge":
                        device_did = None
                        break
                    device_did = parts[-1]
                else:
                    device_did = identifier

        if device_did is not None and device_did not in api_device_ids:
            _LOGGER.info("Removing stale device %s (ID: %s) from device registry as it is no longer present in the API", device_entry.name, device_did)
            device_registry.async_remove_device(device_entry.id)

    _LOGGER.info("Starting entry setup for each platform")
    # This creates each HA object for each platform your device requires.
    # It's done by calling the `async_setup_entry` function in each platform module.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    # This is called when an entry/configured device is to be removed. The class
    # needs to unload itself, and remove callbacks. See the classes for further
    # details
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        manager, _, _, _, _ = hass.data[DOMAIN].pop(entry.entry_id)
        # Close the API session
        await manager.api.async_close()

    return unloaded
