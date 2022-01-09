"""Platform for Rademacher Bridge"""
import logging
from typing import Any

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

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, SUPPORTED_DEVICES

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({vol.Required(CONF_HOST): cv.string})

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    hub = hass.data[DOMAIN][config_entry.entry_id]
    new_entities = []
    covers = hub.covers
    for cover in covers:
        cover_info = hub.coordinator.data[cover["ID_DEVICE_LOC"]["value"]]
        cover_entity = RademacherCover(hub, cover_info)
        new_entities.append(cover_entity)
    # If we have any new devices, add them
    if new_entities:
        async_add_entities(new_entities)


class RademacherCover(CoordinatorEntity, CoverEntity):
    def __init__(self, hub, device):
        super().__init__(hub.coordinator)
        self._hub = hub
        self._uid = device["PROT_ID_DEVICE_LOC"]["value"]
        self._did = device["ID_DEVICE_LOC"]["value"]
        self._name = device["NAME_DEVICE_LOC"]["value"]
        self._model = SUPPORTED_DEVICES[device["PROD_CODE_DEVICE_LOC"]["value"]]["name"]
        self._sw_version = device["VERSION_CFG"]["value"]
        self._supported_features = SUPPORT_STOP | SUPPORT_CLOSE | SUPPORT_OPEN
        if "GOTO_POS_CMD" in device:
            self._supported_features |= SUPPORT_SET_POSITION

    @property
    def hub(self):
        return self._hub

    @property
    def did(self):
        return self._did

    @property
    def device_info(self):
        """Information about this entity/device."""
        return {
            "identifiers": {(DOMAIN, self.did)},
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
    def unique_id(self):
        return self._uid

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

    @property
    def available(self):
        return self.coordinator.data[self.did]["REACHABILITY_EVT"]["value"]

    @property
    def current_cover_position(self):
        return 100 - int(self.coordinator.data[self.did]["CURR_POS_CFG"]["value"])

    @property
    def is_closing(self):
        return False

    @property
    def is_opening(self):
        return False

    @property
    def is_closed(self):
        return self.current_cover_position == 0

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self.hub.open_cover(self.did)
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self.hub.close_cover(self.did)
        await self.coordinator.async_request_refresh()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        await self.hub.set_cover_position(self.did, kwargs[ATTR_POSITION])
        await self.coordinator.async_request_refresh()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        await self.hub.stop_cover(self.did)
        await self.coordinator.async_request_refresh()
