"""Platform for Rademacher Bridge"""
import logging
from typing import Any

from aiohttp import (
    ClientError,
    ClientOSError,
    InvalidURL,
    TooManyRedirects,
    ServerTimeoutError,
)
from homeassistant.components.cover import (
    PLATFORM_SCHEMA,
    CoverEntity,
    CoverDeviceClass,
)
from homeassistant.const import CONF_HOST
from homeassistant.components.cover import (
    ATTR_POSITION,
    SUPPORT_OPEN,
    SUPPORT_CLOSE,
    SUPPORT_STOP,
    SUPPORT_SET_POSITION,
)
import homeassistant.helpers.config_validation as cv

import voluptuous as vol
from .const import DOMAIN, SUPPORTED_DEVICES

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({vol.Required(CONF_HOST): cv.string})

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    hub = hass.data[DOMAIN][config_entry.entry_id]
    new_entities = []
    covers = await hub.get_covers()
    for cover in covers:
        cover_info = await hub.get_device(cover["ID_DEVICE_LOC"]["value"])
        cover_entity = RademacherCover(hub, cover_info)
        new_entities.append(cover_entity)
    # If we have any new devices, add them
    if new_entities:
        async_add_entities(new_entities)


class RademacherCover(CoverEntity):
    def __init__(self, hub, device):
        self._hub = hub
        self._uid = device["PROT_ID_DEVICE_LOC"]["value"]
        self._did = device["ID_DEVICE_LOC"]["value"]
        self._name = device["NAME_DEVICE_LOC"]["value"]
        self._model = SUPPORTED_DEVICES[device["PROD_CODE_DEVICE_LOC"]["value"]]["name"]
        self._sw_version = device["VERSION_CFG"]["value"]
        self._available: bool = bool(device["REACHABILITY_EVT"]["value"])
        self._current_cover_position = 100 - int(device["CURR_POS_CFG"]["value"])
        self._supported_features = SUPPORT_STOP | SUPPORT_CLOSE | SUPPORT_OPEN
        if "GOTO_POS_CMD" in device:
            self._supported_features |= SUPPORT_SET_POSITION
        self._is_opening = False
        self._is_closing = False

    @property
    def device_info(self):
        """Information about this entity/device."""
        return {
            "identifiers": {(DOMAIN, self._uid)},
            # If desired, the name for the device could be different to the entity
            "name": self.name,
            "sw_version": self.sw_version,
            "model": self.model,
            "manufacturer": "Rademacher",
        }

    @property
    def supported_features(self):
        return self._supported_features

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
        return CoverDeviceClass.SHUTTER.value

    @property
    def name(self):
        return self._name

    @property
    def model(self):
        return self._model

    @property
    def sw_version(self):
        return self._sw_version

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self._hub.open_cover(self._did)

    def open_cover(self, **kwargs: Any) -> None:
        self.async_open_cover()

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self._hub.close_cover(self._did)

    def close_cover(self, **kwargs: Any) -> None:
        self.async_close_cover()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        await self._hub.set_cover_position(self._did, kwargs[ATTR_POSITION])

    async def async_stop_cover(self, **kwargs: Any) -> None:
        await self._hub.stop_cover(self._did)

    async def async_update(self):
        try:
            device = await self._hub.get_device_status(self._did)

            if device["response"] == "get_device":
                self._is_opening = False
                self._is_closing = False
                self._current_cover_position = (
                    100 - device["device"]["statusesMap"]["Position"]
                )
                self._available = device["device"]["statusValid"]
            else:
                self._available = False

        except (
            RuntimeError,
            ClientError,
            ClientOSError,
            TooManyRedirects,
            BaseException,
            InvalidURL,
            ServerTimeoutError,
        ) as e:
            self._available = False
