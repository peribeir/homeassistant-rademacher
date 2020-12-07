"""Platform for Rademacher Bridge"""
import logging
from typing import Any

from homeassistant.components.cover import PLATFORM_SCHEMA, CoverEntity
from homeassistant.const import CONF_HOST
from homeassistant.components.cover import (
    ATTR_POSITION,
    SUPPORT_OPEN,
    SUPPORT_CLOSE,
    SUPPORT_STOP,
    SUPPORT_SET_POSITION,
    DEVICE_CLASS_SHUTTER
)
import homeassistant.helpers.config_validation as cv

import voluptuous as vol
from .const import DOMAIN

SUPPORT_RADEMACHER = (
        SUPPORT_STOP | SUPPORT_CLOSE | SUPPORT_OPEN | SUPPORT_SET_POSITION
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string
})

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_devices):
    hub = hass.data[DOMAIN][config_entry.entry_id]
    new_devices = []
    covers = await hub.get_covers()
    for cover in covers['devices']:
        cover_entity = RademacherCover(hub, cover)
        new_devices.append(cover_entity)
    # If we have any new devices, add them
    if new_devices:
        async_add_devices(new_devices)


class RademacherCover(CoverEntity):
    def __init__(self, hub, device):
        self._hub = hub
        self._uid = device['uid']
        self._did = device['did']
        self._name = device['name']
        self._available: bool = device['statusValid']
        self._current_cover_position = 100 - device['statusesMap']['Position']
        self._is_opening = False
        self._is_closing = False

    @property
    def device_info(self):
        """Information about this entity/device."""
        return {
            "identifiers": {(DOMAIN, self._uid)},
            # If desired, the name for the device could be different to the entity
            "name": self.name,
            "sw_version": self._roller.firmware_version,
#            "model": self._roller.model,
            "manufacturer": "Rademacher",
        }

    @property
    def supported_features(self):
        return SUPPORT_RADEMACHER

    @property
    def available(self):
        return self._available

    @property
    def unique_id(self):
        return self._uid

    @property
    def current_cover_position(self):
        return self._current_cover_position

    @property
    def is_closing(self):
        return self._is_closing

    @property
    def is_opening(self):
        return self._is_opening

    @property
    def is_closed(self):
        return self._current_cover_position == 0

    @property
    def device_class(self):
        return DEVICE_CLASS_SHUTTER

    @property
    def name(self):
        return self._name

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self._hub.open_cover(self._did)

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self._hub.close_cover(self._did)

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        await self._hub.set_cover_position(self._did, kwargs[ATTR_POSITION])

    async def async_stop_cover(self, **kwargs: Any) -> None:
        await self._hub.stop_cover(self._did)

    async def async_update(self):
        device = await self._hub.get_device_status(self._did)

        if device['response'] == 'get_device':
            self._is_opening = False
            self._is_closing = False
            self._current_cover_position = 100 - device['device']['statusesMap']['Position']
            self._available = device['device']['statusValid']
