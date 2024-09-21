"""Platform for Rademacher Bridge."""
import asyncio
import logging

from homepilot.cover import HomePilotCover
from homepilot.device import HomePilotDevice
from homepilot.manager import HomePilotManager
from homepilot.thermostat import HomePilotThermostat

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import CONF_EXCLUDE, PERCENTAGE, UnitOfTemperature
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .entity import HomePilotEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup of entities for switch platform."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    manager: HomePilotManager = entry[0]
    coordinator: DataUpdateCoordinator = entry[1]
    exclude_devices: list[str] = entry[3][CONF_EXCLUDE]
    new_entities = []
    for did in manager.devices:
        if did not in exclude_devices:
            device: HomePilotDevice = manager.devices[did]
            if isinstance(device, HomePilotCover):
                cover: HomePilotCover = device
                if cover.has_ventilation_position_config:
                    _LOGGER.info("Found Ventilation Position Config for Device ID: %s", device.did)
                    new_entities.append(HomePilotVentilationPositionEntity(coordinator, device))
            if isinstance(device, HomePilotThermostat):
                thermostat: HomePilotThermostat = device
                if thermostat.has_temperature_thresh_cfg[0]:
                    _LOGGER.info("Found Temperature Threshold Config 1 for Device ID: %s", device.did)
                    new_entities.append(HomePilotTemperatureThresholdEntity(coordinator, device, 1))
                if thermostat.has_temperature_thresh_cfg[1]:
                    _LOGGER.info("Found Temperature Threshold Config 2 for Device ID: %s", device.did)
                    new_entities.append(HomePilotTemperatureThresholdEntity(coordinator, device, 2))
                if thermostat.has_temperature_thresh_cfg[2]:
                    _LOGGER.info("Found Temperature Threshold Config 3 for Device ID: %s", device.did)
                    new_entities.append(HomePilotTemperatureThresholdEntity(coordinator, device, 3))
                if thermostat.has_temperature_thresh_cfg[3]:
                    _LOGGER.info("Found Temperature Threshold Config 4 for Device ID: %s", device.did)
                    new_entities.append(HomePilotTemperatureThresholdEntity(coordinator, device, 4))
    # If we have any new devices, add them
    if new_entities:
        async_add_entities(new_entities)


class HomePilotVentilationPositionEntity(HomePilotEntity, NumberEntity):
    """This class represents Cover Ventilation Position."""

    def __init__(
        self, coordinator: DataUpdateCoordinator, device: HomePilotDevice
    ) -> None:
        super().__init__(
            coordinator,
            device,
            unique_id=f"{device.uid}_ventilation_position",
            name=f"{device.name} Ventilation Position",
            device_class=None,
            entity_category=EntityCategory.CONFIG,
        )
        self._attr_mode = NumberMode.SLIDER
        self._attr_native_max_value = 100
        self._attr_native_min_value = 0
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = PERCENTAGE

    @property
    def available(self):
        device: HomePilotCover = self.coordinator.data[self.did]
        return super().available and device.ventilation_position_mode

    @property
    def native_value(self):
        device: HomePilotCover = self.coordinator.data[self.did]
        return device.ventilation_position

    async def async_set_native_value(self, value):
        """Turn the entity on."""
        device: HomePilotCover = self.coordinator.data[self.did]
        await device.async_set_ventilation_position(value)
        await asyncio.sleep(5)
        await self.coordinator.async_request_refresh()

class HomePilotTemperatureThresholdEntity(HomePilotEntity, NumberEntity):
    """This class represents Cover Ventilation Position."""
    thresh_number: int = 0

    def __init__(
        self, coordinator: DataUpdateCoordinator, device: HomePilotThermostat, thresh_number: int
    ) -> None:
        super().__init__(
            coordinator,
            device,
            unique_id=f"{device.uid}_temperature_thresh_{thresh_number}",
            name=f"{device.name} Temp Threshold {thresh_number}",
            device_class=NumberDeviceClass.TEMPERATURE,
            entity_category=EntityCategory.CONFIG,
        )
        self._attr_mode = NumberMode.SLIDER
        self._attr_native_max_value = device.temperature_thresh_cfg_max[thresh_number-1]
        self._attr_native_min_value = device.temperature_thresh_cfg_min[thresh_number-1]
        self._attr_native_step = device.temperature_thresh_cfg_step[thresh_number-1]
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._thresh_number = thresh_number

    @property
    def native_value(self):
        device: HomePilotThermostat = self.coordinator.data[self.did]
        return device.temperature_thresh_cfg_value[self._thresh_number-1]

    async def async_set_native_value(self, value):
        """Turn the entity on."""
        device: HomePilotThermostat = self.coordinator.data[self.did]
        await device.async_set_temperature_thresh_cfg(self._thresh_number, value)
        await asyncio.sleep(5)
        await self.coordinator.async_request_refresh()
