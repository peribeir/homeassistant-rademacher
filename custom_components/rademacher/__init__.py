"""Integration for Rademacher Bridge"""
import asyncio
from datetime import timedelta
import logging
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_DEVICES,
    CONF_EXCLUDE,
    CONF_HOST,
    CONF_PASSWORD,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)
from homeassistant.exceptions import ConfigEntryAuthFailed

from .homepilot.manager import HomePilotManager
from .homepilot.api import AuthError

from .const import DOMAIN

# List of platforms to support. There should be a matching .py file for each,
# eg <cover.py> and <sensor.py>
PLATFORMS = ["cover", "button", "switch", "sensor", "binary_sensor"]

_LOGGER = logging.getLogger(__name__)


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
    manager = await HomePilotManager.build_manager(
        entry.data[CONF_HOST],
        entry.data[CONF_PASSWORD] if CONF_PASSWORD in entry.data else "",
    )
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
            async with async_timeout.timeout(10):
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
        update_interval=timedelta(seconds=30),
    )

    # Backward compatibility
    entry_options = entry.options.copy()
    if CONF_EXCLUDE not in entry.options:
        if CONF_DEVICES in entry.options:
            entry_options[CONF_EXCLUDE] = [
                did for did in manager.devices if did not in entry.options[CONF_DEVICES]
            ]
        else:
            entry_options[CONF_EXCLUDE] = []

    hass.data[DOMAIN][entry.entry_id] = (
        manager,
        coordinator,
        entry.data,
        entry_options,
    )

    await coordinator.async_config_entry_first_refresh()

    entry.async_on_unload(entry.add_update_listener(update_listener))

    _LOGGER.info("Starting entry setup for each platform")
    # This creates each HA object for each platform your device requires.
    # It's done by calling the `async_setup_entry` function in each platform module.
    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    # This is called when an entry/configured device is to be removed. The class
    # needs to unload itself, and remove callbacks. See the classes for further
    # details
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
