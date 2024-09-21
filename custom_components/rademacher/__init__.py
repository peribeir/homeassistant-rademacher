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

from .const import DOMAIN

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
            config_entry, title=f"{nodename} ({mac_address})", unique_id=mac_address, data=config_entry.data, options=config_entry.options
        )

        config_entry.version = 2

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
        manager = await HomePilotManager.async_build_manager(api)
    except AuthError as err:
        # Raising ConfigEntryAuthFailed will cancel future updates
        # and start a config flow with SOURCE_REAUTH (async_step_reauth)
        raise ConfigEntryAuthFailed from err
    except Exception as err:
        raise ConfigEntryNotReady from err

    _LOGGER.info("Manager instance created, found %s devices", len(manager.devices))
    _LOGGER.debug("Device IDs: %s", list(manager.devices))

    async def async_update_data():
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with asyncio.timeout(10):
                return await manager.update_states()
        except AuthError as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            raise ConfigEntryAuthFailed from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        # Name of the data. For logging purposes.
        name="rademacher",
        update_method=async_update_data,
        # Polling interval. Will only be polled if there are subscribers.
        update_interval=timedelta(seconds=10),
    )

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

    hass.data[DOMAIN][entry.entry_id] = (
        manager,
        coordinator,
        entry.data,
        entry_options,
    )

    await coordinator.async_config_entry_first_refresh()

    entry.async_on_unload(entry.add_update_listener(update_listener))

    # Deleting excluded devices
    device_registry: DeviceRegistry = dr.async_get(hass)
    for did in entry.options[CONF_EXCLUDE]:
        device_entry: DeviceEntry = device_registry.async_get_device({(DOMAIN, did)})
        if device_entry is not None:
            _LOGGER.info("Deleting device %s", did)
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
        hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded
