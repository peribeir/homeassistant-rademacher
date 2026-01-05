"""Platform for Rademacher Bridge."""
import asyncio
import logging

from homepilot.device import HomePilotDevice
from homepilot.thermostat import HomePilotThermostat
from homepilot.manager import HomePilotManager
from homepilot.cover import HomePilotCover

from homeassistant.components.button import ButtonEntity
from homeassistant.const import CONF_EXCLUDE
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .entity import HomePilotEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup of entities for button platform."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    manager: HomePilotManager = entry[0]
    coordinator: DataUpdateCoordinator = entry[1]
    exclude_devices: list[str] = entry[3][CONF_EXCLUDE]
    new_entities = []
    for did in manager.devices:
        if did not in exclude_devices:
            device: HomePilotDevice = manager.devices[did]
            if device.has_ping_cmd:
                _LOGGER.info("Found Ping Command Button for Device ID: %s", device.did)
                new_entities.append(HomePilotButtonEntity(
                    coordinator,
                    device,
                    id_suffix="ping",
                    name_suffix="Ping",
                    device_command_method=device.async_ping,
                    entity_registry_enabled_default=False,
                    entity_category=EntityCategory.DIAGNOSTIC,
                ))
            if isinstance(device, HomePilotThermostat):
                if device.has_contact_open_cmd:
                    _LOGGER.info("Found Contact Open Command Button for Device ID: %s", device.did)
                    new_entities.append(HomePilotButtonEntity(
                        coordinator,
                        device,
                        id_suffix="contact_open",
                        name_suffix="Contact Open",
                        device_command_method=device.async_contact_open_cmd,
                        entity_registry_enabled_default=False,
                    ))
                if device.has_contact_close_cmd:
                    _LOGGER.info("Found Contact Close Command Button for Device ID: %s", device.did)
                    new_entities.append(HomePilotButtonEntity(
                        coordinator,
                        device,
                        id_suffix="contact_close",
                        name_suffix="Contact Close",
                        device_command_method=device.async_contact_close_cmd,
                        entity_registry_enabled_default=False,
                    ))
            if isinstance(device, HomePilotCover):
                if device.has_sun_start_cmd:
                    _LOGGER.info("Found Sun Start Command Button for Device ID: %s", device.did)
                    new_entities.append(HomePilotButtonEntity(
                        coordinator,
                        device,
                        id_suffix="sun_start",
                        name_suffix="Sun Start",
                        device_command_method=device.async_sun_start_cmd,
                        entity_registry_enabled_default=False,
                    ))
                if device.has_sun_stop_cmd:
                    _LOGGER.info("Found Sun Stop Command Button for Device ID: %s", device.did)
                    new_entities.append(HomePilotButtonEntity(
                        coordinator,
                        device,
                        id_suffix="sun_stop",
                        name_suffix="Sun Stop",
                        device_command_method=device.async_sun_stop_cmd,
                        entity_registry_enabled_default=False,
                    ))
                if device.has_wind_start_cmd:
                    _LOGGER.info("Found Wind Start Command Button for Device ID: %s", device.did)
                    new_entities.append(HomePilotButtonEntity(
                        coordinator,
                        device,
                        id_suffix="wind_start",
                        name_suffix="Wind Start",
                        device_command_method=device.async_wind_start_cmd,
                        entity_registry_enabled_default=False,
                    ))
                if device.has_wind_stop_cmd:
                    _LOGGER.info("Found Wind Stop Command Button for Device ID: %s", device.did)
                    new_entities.append(HomePilotButtonEntity(
                        coordinator,
                        device,
                        id_suffix="wind_stop",
                        name_suffix="Wind Stop",
                        device_command_method=device.async_wind_stop_cmd,
                        entity_registry_enabled_default=False,
                    ))
                if device.has_rain_start_cmd:
                    _LOGGER.info("Found Rain Start Command Button for Device ID: %s", device.did)
                    new_entities.append(HomePilotButtonEntity(
                        coordinator,
                        device,
                        id_suffix="rain_start",
                        name_suffix="Rain Start",
                        device_command_method=device.async_rain_start_cmd,
                        entity_registry_enabled_default=False,
                    ))
                if device.has_rain_stop_cmd:
                    _LOGGER.info("Found Rain Stop Command Button for Device ID: %s", device.did)
                    new_entities.append(HomePilotButtonEntity(
                        coordinator,
                        device,
                        id_suffix="rain_stop",
                        name_suffix="Rain Stop",
                        device_command_method=device.async_rain_stop_cmd,
                        entity_registry_enabled_default=False,
                    ))
                if device.has_goto_dawn_pos_cmd:
                    _LOGGER.info("Found Goto Dawn Position Command Button for Device ID: %s", device.did)
                    new_entities.append(HomePilotButtonEntity(
                        coordinator,
                        device,
                        id_suffix="goto_dawn_pos",
                        name_suffix="Goto Dawn Position",
                        device_command_method=device.async_goto_dawn_pos_cmd,
                        entity_registry_enabled_default=False,
                    ))
                if device.has_goto_dusk_pos_cmd:
                    _LOGGER.info("Found Goto Dusk Position Command Button for Device ID: %s", device.did)
                    new_entities.append(HomePilotButtonEntity(
                        coordinator,
                        device,
                        id_suffix="goto_dusk_pos",
                        name_suffix="Goto Dusk Position",
                        device_command_method=device.async_goto_dusk_pos_cmd,
                        entity_registry_enabled_default=False,
                    ))
    if new_entities:
        async_add_entities(new_entities)


class HomePilotButtonEntity(HomePilotEntity, ButtonEntity):
    """This class represents a button which sends a ping command to a device."""

    def __init__(
        self, coordinator: DataUpdateCoordinator,
        device: HomePilotDevice,
        id_suffix,
        name_suffix,
        device_command_method,
        entity_category=None,
        entity_registry_enabled_default=False,
    ) -> None:
        super().__init__(
            coordinator,
            device,
            unique_id=f"{device.uid}_{id_suffix}",
            name=f"{device.name} {name_suffix}",
            entity_category=entity_category,
            entity_registry_enabled_default=entity_registry_enabled_default,
        )
        self._device_command_method = device_command_method

    @property
    def available(self):
        return True

    async def async_press(self) -> None:
        await self._device_command_method()
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()