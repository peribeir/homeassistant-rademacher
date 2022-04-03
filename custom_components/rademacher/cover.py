"""Platform for Rademacher Bridge"""
import asyncio
import logging
from typing import Any

from homeassistant.const import CONF_EXCLUDE
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.components.cover import (
    CoverEntity,
    CoverDeviceClass,
    ATTR_POSITION,
    SUPPORT_OPEN,
    SUPPORT_CLOSE,
    SUPPORT_STOP,
    SUPPORT_SET_POSITION,
)

from homepilot.cover import HomePilotCover, CoverType
from homepilot.device import HomePilotDevice
from homepilot.manager import HomePilotManager

from .entity import HomePilotEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup of entities for cover platform"""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    manager: HomePilotManager = entry[0]
    coordinator: DataUpdateCoordinator = entry[1]
    exclude_devices: list[str] = entry[3][CONF_EXCLUDE]
    new_entities = []
    for did in manager.devices:
        if did not in exclude_devices:
            device: HomePilotDevice = manager.devices[did]
            if isinstance(device, HomePilotCover):
                _LOGGER.info("Found Cover for Device ID: %s", device.did)
                new_entities.append(HomePilotCoverEntity(coordinator, device))
    # If we have any new devices, add them
    if new_entities:
        async_add_entities(new_entities)


class HomePilotCoverEntity(HomePilotEntity, CoverEntity):
    """This class represents the Cover entity"""

    def __init__(
        self, coordinator: DataUpdateCoordinator, cover: HomePilotCover
    ) -> None:
        super().__init__(
            coordinator,
            cover,
            unique_id=cover.uid,
            name=cover.name,
            device_class=CoverDeviceClass.SHUTTER.value
            if cover.cover_type == CoverType.SHUTTER.value
            else CoverDeviceClass.GARAGE.value,
        )
        self._supported_features = SUPPORT_STOP | SUPPORT_CLOSE | SUPPORT_OPEN
        if cover.can_set_position:
            self._supported_features |= SUPPORT_SET_POSITION

    @property
    def supported_features(self):
        return self._supported_features

    @property
    def current_cover_position(self):
        device: HomePilotCover = self.coordinator.data[self.did]
        return device.cover_position

    @property
    def is_closing(self):
        device: HomePilotCover = self.coordinator.data[self.did]
        return device.is_closing

    @property
    def is_opening(self):
        device: HomePilotCover = self.coordinator.data[self.did]
        return device.is_opening

    @property
    def is_closed(self):
        device: HomePilotCover = self.coordinator.data[self.did]
        return device.is_closed

    async def async_open_cover(self, **kwargs: Any) -> None:
        device: HomePilotCover = self.coordinator.data[self.did]
        await device.async_open_cover()
        await asyncio.sleep(5)
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        device: HomePilotCover = self.coordinator.data[self.did]
        await device.async_close_cover()
        await asyncio.sleep(5)
        await self.coordinator.async_request_refresh()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        device: HomePilotCover = self.coordinator.data[self.did]
        await device.async_set_cover_position(kwargs[ATTR_POSITION])
        await asyncio.sleep(5)
        await self.coordinator.async_request_refresh()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        device: HomePilotCover = self.coordinator.data[self.did]
        await device.async_stop_cover()
        await asyncio.sleep(5)
        await self.coordinator.async_request_refresh()
