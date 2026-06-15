"""Platform for Rademacher Bridge."""
from typing import Callable
import logging

from homepilot.cover import HomePilotCover
from homepilot.device import HomePilotDevice, HomePilotAutoConfigDevice
from homepilot.manager import HomePilotManager

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
            # Weather/contact command buttons are exposed by any auto config
            # device (cover, switch/actuator, thermostat) advertising the
            # corresponding command capability, not only covers/thermostats.
            if isinstance(device, HomePilotAutoConfigDevice):
                if device.has_contact_open_cmd:
                    _LOGGER.info("Found Contact Open Command Button for Device ID: %s", device.did)
                    new_entities.append(HomePilotButtonEntity(
                        coordinator,
                        device,
                        id_suffix="contact_open",
                        name_suffix="Contact Open",
                        device_command_method=device.async_contact_open_cmd,
                        entity_registry_enabled_default=False,
                        available_condition=lambda d: isinstance(d, HomePilotAutoConfigDevice) and (not d.has_contact_auto_mode or d.contact_auto_mode_value),
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
                        available_condition=lambda d: isinstance(d, HomePilotAutoConfigDevice) and (not d.has_contact_auto_mode or d.contact_auto_mode_value),
                    ))
                if device.has_sun_start_cmd:
                    _LOGGER.info("Found Sun Start Command Button for Device ID: %s", device.did)
                    new_entities.append(HomePilotButtonEntity(
                        coordinator,
                        device,
                        id_suffix="sun_start",
                        name_suffix="Sun Start",
                        device_command_method=device.async_sun_start_cmd,
                        entity_registry_enabled_default=False,
                        available_condition=lambda d: isinstance(d, HomePilotAutoConfigDevice) and (not d.has_sun_auto_mode or d.sun_auto_mode_value),
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
                        available_condition=lambda d: isinstance(d, HomePilotAutoConfigDevice) and (not d.has_sun_auto_mode or d.sun_auto_mode_value),
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
                        available_condition=lambda d: isinstance(d, HomePilotAutoConfigDevice) and (not d.has_wind_auto_mode or d.wind_auto_mode_value),
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
                        available_condition=lambda d: isinstance(d, HomePilotAutoConfigDevice) and (not d.has_wind_auto_mode or d.wind_auto_mode_value),
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
                        available_condition=lambda d: isinstance(d, HomePilotAutoConfigDevice) and (not d.has_rain_auto_mode or d.rain_auto_mode_value),
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
                        available_condition=lambda d: isinstance(d, HomePilotAutoConfigDevice) and (not d.has_rain_auto_mode or d.rain_auto_mode_value),
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
                        available_condition=lambda d: isinstance(d, HomePilotAutoConfigDevice) and (not d.has_dawn_auto_mode or d.dawn_auto_mode_value),
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
                        available_condition=
                            lambda d: isinstance(d, HomePilotAutoConfigDevice) and (not d.has_dusk_auto_mode or d.dusk_auto_mode_value),
                    ))
            if isinstance(device, HomePilotCover):
                if device.has_ventilation_position_config:
                    _LOGGER.info("Found Goto Ventilation Position Command Button for Device ID: %s", device.did)
                    new_entities.append(HomePilotButtonEntity(
                        coordinator,
                        device,
                        id_suffix="goto_ventilation_pos",
                        name_suffix="Goto Ventilation Position",
                        device_command_method=device.async_goto_ventilation_position,
                        entity_registry_enabled_default=True,
                        available_condition=
                            lambda d: isinstance(d, HomePilotCover) and d.ventilation_position_mode,
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
        available_condition: Callable[[HomePilotDevice], bool] = lambda d: True,
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
        self._available_condition = available_condition

    @property
    def available(self):
        device: HomePilotDevice = self.coordinator.data[self.did]
        return self._available_condition(device)

    async def async_press(self) -> None:
        await self.async_execute_and_poll(
            lambda _: self._device_command_method(),
            lambda: True,
            pre_poll_delay=3.0,
        )
