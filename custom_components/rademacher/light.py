"""Platform for Rademacher Bridge."""
import asyncio
import logging
from typing import Any

from homepilot.actuator import HomePilotActuator
from homepilot.device import HomePilotDevice
from homepilot.manager import HomePilotManager

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.const import CONF_EXCLUDE
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .entity import HomePilotEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup of entities for light platform."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    manager: HomePilotManager = entry[0]
    coordinator: DataUpdateCoordinator = entry[1]
    exclude_devices: list[str] = entry[3][CONF_EXCLUDE]
    new_entities = []
    for did in manager.devices:
        if did not in exclude_devices:
            device: HomePilotDevice = manager.devices[did]
            if isinstance(device, HomePilotActuator):
                _LOGGER.info("Found Actuator/Light for Device ID: %s", device.did)
                new_entities.append(HomePilotLightEntity(coordinator, device))
    # If we have any new devices, add them
    if new_entities:
        async_add_entities(new_entities)


class HomePilotLightEntity(HomePilotEntity, LightEntity):
    """This class represents the Light entity."""

    def __init__(
        self, coordinator: DataUpdateCoordinator, actuator: HomePilotActuator
    ) -> None:
        super().__init__(
            coordinator,
            actuator,
            unique_id=actuator.uid,
            name=actuator.name,
        )
        self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        self._attr_color_mode = ColorMode.BRIGHTNESS

    @property
    def brightness(self):
        device: HomePilotActuator = self.coordinator.data[self.did]
        return round(device.brightness*255/100)

    @property
    def is_on(self):
        device: HomePilotActuator = self.coordinator.data[self.did]
        return device.is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        device: HomePilotActuator = self.coordinator.data[self.did]
        if ATTR_BRIGHTNESS in kwargs: 
            await device.async_set_brightness(round(kwargs[ATTR_BRIGHTNESS]*100/255))
        else:
            await device.async_turn_on()
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        device: HomePilotActuator = self.coordinator.data[self.did]
        await device.async_turn_off()
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()
