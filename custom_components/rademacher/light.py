"""Platform for Rademacher Bridge."""
import asyncio
import logging
from typing import Any

from homepilot.actuator import HomePilotActuator
from homepilot.device import HomePilotDevice
from homepilot.light import HomePilotLight
from homepilot.manager import HomePilotManager

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
)
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
                new_entities.append(HomePilotActuatorLightEntity(coordinator, device))
            if isinstance(device, HomePilotLight):
                _LOGGER.info("Found Light for Device ID: %s", device.did)
                new_entities.append(HomePilotLightEntity(coordinator, device))
    # If we have any new devices, add them
    if new_entities:
        async_add_entities(new_entities)


class HomePilotActuatorLightEntity(HomePilotEntity, LightEntity):
    """This class represents the Actuator/Light entity."""

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


class HomePilotLightEntity(HomePilotEntity, LightEntity):
    """This class represents the Light entity."""

    def __init__(
        self, coordinator: DataUpdateCoordinator, light: HomePilotLight
    ) -> None:
        super().__init__(
            coordinator,
            light,
            unique_id=light.uid,
            name=light.name,
        )
        self._attr_supported_color_modes = set()
        if light.has_rgb:
            self._attr_supported_color_modes.add(ColorMode.RGB)
        if light.has_color_temp:
            self._attr_supported_color_modes.add(ColorMode.COLOR_TEMP)
        if not light.has_rgb and not light.has_color_temp:
            self._attr_supported_color_modes.add(ColorMode.BRIGHTNESS)

    @property
    def color_mode(self):
        device: HomePilotLight = self.coordinator.data[self.did]
        if device.has_color_mode:
            return ColorMode.COLOR_TEMP if device.color_mode_value == "ct" else ColorMode.RGB
        else:
            if not device.has_rgb and not device.has_color_temp:
                return ColorMode.BRIGHTNESS
            else:
                return ColorMode.UNKNOWN

    @property
    def brightness(self):
        device: HomePilotLight = self.coordinator.data[self.did]
        return round(device.brightness*255/100)

    @property
    def color_temp_kelvin(self):
        device: HomePilotLight = self.coordinator.data[self.did]
        return round(1000000 / device.color_temp_value) if device.has_color_temp else None

    @property
    def rgb_color(self):
        device: HomePilotLight = self.coordinator.data[self.did]
        return (device.r_value, device.g_value, device.b_value)

    @property
    def is_on(self):
        device: HomePilotActuator = self.coordinator.data[self.did]
        return device.is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        device: HomePilotActuator = self.coordinator.data[self.did]
        if not device.is_on:
            await device.async_turn_on()
        if ATTR_BRIGHTNESS in kwargs:
            await device.async_set_brightness(round(kwargs[ATTR_BRIGHTNESS]*100/255))
        if ATTR_RGB_COLOR in kwargs:
            await device.async_set_rgb(*kwargs[ATTR_RGB_COLOR])
        if ATTR_COLOR_TEMP in kwargs:
            await device.async_set_color_temp(kwargs[ATTR_COLOR_TEMP])
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        device: HomePilotActuator = self.coordinator.data[self.did]
        await device.async_turn_off()
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

