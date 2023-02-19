"""Platform for Rademacher Bridge"""
import asyncio
import logging

from homeassistant.helpers.entity import EntityCategory

from homeassistant.const import CONF_EXCLUDE
from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from homepilot.manager import HomePilotManager
from homepilot.device import HomePilotDevice
from homepilot.cover import HomePilotCover

from .const import DOMAIN
from .entity import HomePilotEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup of entities for switch platform"""
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
    # If we have any new devices, add them
    if new_entities:
        async_add_entities(new_entities)


class HomePilotVentilationPositionEntity(HomePilotEntity, NumberEntity):
    """This class represents Cover Ventilation Position"""

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
        self._attr_native_unit_of_measurement = "%"

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
