"""Platform for Rademacher Bridge"""
import asyncio
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.components.climate import (
    ClimateEntity,
    SUPPORT_TARGET_TEMPERATURE,
    HVAC_MODE_HEAT_COOL,
)
from homeassistant.const import (
    CONF_EXCLUDE,
    TEMP_CELSIUS,
)

from homepilot.manager import HomePilotManager
from homepilot.device import HomePilotDevice
from homepilot.thermostat import HomePilotThermostat

from .entity import HomePilotEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup of entities for sensor platform"""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    manager: HomePilotManager = entry[0]
    coordinator: DataUpdateCoordinator = entry[1]
    exclude_devices: list[str] = entry[3][CONF_EXCLUDE]
    new_entities = []
    for did in manager.devices:
        if did not in exclude_devices:
            device: HomePilotDevice = manager.devices[did]
            if isinstance(device, HomePilotThermostat):
                _LOGGER.info("Found Thermostat for Device ID: %s", device.did)
                new_entities.append(
                    HomePilotClimateEntity(
                        coordinator,
                        device,
                        TEMP_CELSIUS,
                    )
                )
    # If we have any new devices, add them
    if new_entities:
        async_add_entities(new_entities)


class HomePilotClimateEntity(HomePilotEntity, ClimateEntity):
    """This class represents all Sensors supported"""

    def __init__(
        self,
        coordinator,
        device: HomePilotThermostat,
        temperature_unit,
    ) -> None:
        super().__init__(
            coordinator,
            device,
            unique_id=f"{device.uid}",
            name=f"{device.name}",
            device_class=None,
        )
        self._attr_temperature_unit = temperature_unit
        self._attr_max_temp = device.max_target_temperature
        self._attr_min_temp = device.min_target_temperature
        self._attr_target_temperature_step = device.step_target_temperature
        self._attr_supported_features = SUPPORT_TARGET_TEMPERATURE
        self._attr_hvac_modes = [HVAC_MODE_HEAT_COOL]

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        _LOGGER.debug("async_set_hvac_mode: %s", hvac_mode)
        return

    async def async_set_temperature(self, **kwargs) -> None:
        device: HomePilotThermostat = self.coordinator.data[self.did]
        await device.async_set_target_temperature(kwargs["temperature"])
        await asyncio.sleep(5)
        await self.coordinator.async_request_refresh()

    @property
    def current_temperature(self) -> float:
        device: HomePilotThermostat = self.coordinator.data[self.did]
        return device.temperature_value

    @property
    def target_temperature(self) -> float:
        device: HomePilotThermostat = self.coordinator.data[self.did]
        return device.target_temperature_value

    @property
    def hvac_mode(self) -> str:
        return HVAC_MODE_HEAT_COOL
