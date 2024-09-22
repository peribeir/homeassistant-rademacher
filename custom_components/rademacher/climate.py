"""Platform for Rademacher Bridge."""
import asyncio
import logging

from homepilot.device import HomePilotDevice
from homepilot.manager import HomePilotManager
from homepilot.thermostat import HomePilotThermostat

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    PRESET_BOOST,
    PRESET_ECO,
    PRESET_NONE,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import CONF_EXCLUDE, UnitOfTemperature
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .entity import HomePilotEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup of entities for sensor platform."""
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
                        UnitOfTemperature.CELSIUS,
                    )
                )
    # If we have any new devices, add them
    if new_entities:
        async_add_entities(new_entities)


class HomePilotClimateEntity(HomePilotEntity, ClimateEntity):
    """This class represents all Sensors supported."""

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
        self._attr_hvac_modes = (
            [HVACMode.HEAT, HVACMode.OFF]
        )
        self._attr_preset_modes = ([PRESET_ECO, PRESET_BOOST])

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        device: HomePilotThermostat = self.coordinator.data[self.did]

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        device: HomePilotThermostat = self.coordinator.data[self.did]
        if device.has_auto_mode:
            await device.async_set_auto_mode(preset_mode == PRESET_ECO)
            async with asyncio.timeout(5):
                await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs) -> None:
        device: HomePilotThermostat = self.coordinator.data[self.did]
        if device.can_set_target_temperature:
            await device.async_set_target_temperature(kwargs["temperature"])
            async with asyncio.timeout(5):
                await self.coordinator.async_request_refresh()

    @property
    def current_temperature(self) -> float:
        device: HomePilotThermostat = self.coordinator.data[self.did]
        return device.temperature_value if device.has_temperature else None

    @property
    def target_temperature(self) -> float:
        device: HomePilotThermostat = self.coordinator.data[self.did]
        return (
            device.target_temperature_value if device.has_target_temperature else None
        )

    @property
    def preset_mode(self) -> str:
        device: HomePilotThermostat = self.coordinator.data[self.did]
        return (
            PRESET_NONE
            if not device.has_auto_mode
            else (PRESET_ECO if device.auto_mode_value else PRESET_BOOST)
        )

    @property
    def hvac_mode(self) -> str:
        device: HomePilotThermostat = self.coordinator.data[self.did]
        return (
            HVACMode.HEAT
            if device.has_relais_status and device.relais_value == 1
            else HVACMode.OFF
        )

    @property
    def supported_features(self) -> int:
        device: HomePilotThermostat = self.coordinator.data[self.did]
        return (
            (ClimateEntityFeature.TARGET_TEMPERATURE
            if device.can_set_target_temperature
            else 0) |
            (ClimateEntityFeature.PRESET_MODE
            if device.has_auto_mode
            else 0)
        )
