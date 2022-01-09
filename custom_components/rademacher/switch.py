"""Platform for Rademacher Bridge"""
from aiohttp import (
    ClientError,
    ClientOSError,
    InvalidURL,
    TooManyRedirects,
    ServerTimeoutError,
)
from homeassistant.components.switch import PLATFORM_SCHEMA, SwitchEntity
from homeassistant.const import CONF_HOST
import homeassistant.helpers.config_validation as cv

import voluptuous as vol

from .const import DOMAIN, SUPPORTED_DEVICES

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({vol.Required(CONF_HOST): cv.string})


async def async_setup_entry(hass, config_entry, async_add_entities):
    hub = hass.data[DOMAIN][config_entry.entry_id]
    new_entities = []
    switch_actuators = await hub.get_switch_actuators()
    for device in switch_actuators:
        device_info = await hub.get_device(device["ID_DEVICE_LOC"]["value"])
        new_entities.append(RademacherSwitchActuator(hub, device_info))
    # If we have any new devices, add them
    if new_entities:
        async_add_entities(new_entities)


class RademacherSwitchActuator(SwitchEntity):
    def __init__(self, hub, device):
        self._hub = hub
        self._uid = device["PROT_ID_DEVICE_LOC"]["value"]
        self._did = device["ID_DEVICE_LOC"]["value"]
        self._device_name = device["NAME_DEVICE_LOC"]["value"]
        self._name = f"{device['NAME_DEVICE_LOC']['value']}"
        self._model = SUPPORTED_DEVICES[device["PROD_CODE_DEVICE_LOC"]["value"]]["name"]
        self._sw_version = device["VERSION_CFG"]["value"]
        self._available: bool = bool(device["REACHABILITY_EVT"]["value"])
        self._is_on = device["CURR_SWITCH_POS_CFG"]["value"]

    @property
    def device_info(self):
        """Information about this entity/device."""
        return {
            "identifiers": {(DOMAIN, self._uid)},
            # If desired, the name for the device could be different to the entity
            "name": self.device_name,
            "sw_version": self.sw_version,
            "model": self.model,
            "manufacturer": "Rademacher",
        }

    @property
    def available(self):
        return self._available

    @property
    def is_on(self):
        return self._is_on

    @property
    def unique_id(self):
        return self._uid

    @property
    def name(self):
        return self._name

    @property
    def device_name(self):
        return self._device_name

    @property
    def model(self):
        return self._model

    @property
    def sw_version(self):
        return self._sw_version

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        await self._hub.turn_on(self._did)

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        await self._hub.turn_off(self._did)

    async def async_toggle(self, **kwargs):
        """Toggle the entity."""
        if self._is_on:
            await self._hub.turn_off(self._did)
        else:
            await self._hub.turn_on(self._did)

    async def async_update(self):
        try:
            device = await self._hub.get_device(self._did)

            if device:
                self._available = device["REACHABILITY_EVT"]["value"]
                self._is_on = device["CURR_SWITCH_POS_CFG"]["value"] == "true"
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
