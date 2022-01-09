"""Platform for Rademacher Bridge"""
from homeassistant.components.button import PLATFORM_SCHEMA, ButtonEntity
from homeassistant.const import CONF_HOST
import homeassistant.helpers.config_validation as cv

import voluptuous as vol

from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, SUPPORTED_DEVICES

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({vol.Required(CONF_HOST): cv.string})


async def async_setup_entry(hass, config_entry, async_add_entities):
    hub = hass.data[DOMAIN][config_entry.entry_id]
    new_entities = []
    supported_devices = hub.devices
    for device in supported_devices:
        device_info = hub.coordinator.data[device["ID_DEVICE_LOC"]["value"]]
        if "PING_CMD" in device_info:
            new_entities.append(RademacherPingButton(hub, device_info))
    # If we have any new devices, add them
    if new_entities:
        async_add_entities(new_entities)


class RademacherPingButton(CoordinatorEntity, ButtonEntity):
    def __init__(self, hub, device):
        super().__init__(hub.coordinator)
        self._hub = hub
        self._uid = f"{device['PROT_ID_DEVICE_LOC']['value']}_ping"
        self._did = device["ID_DEVICE_LOC"]["value"]
        self._device_name = device["NAME_DEVICE_LOC"]["value"]
        self._name = f"{device['NAME_DEVICE_LOC']['value']} Ping"
        self._model = SUPPORTED_DEVICES[device["PROD_CODE_DEVICE_LOC"]["value"]]["name"]
        self._sw_version = device["VERSION_CFG"]["value"]

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
            "name": self.device_name,
            "sw_version": self.sw_version,
            "model": self.model,
            "manufacturer": "Rademacher",
        }

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

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC

    @property
    def entity_registry_enabled_default(self):
        return False

    @property
    def available(self):
        return self.coordinator.data[self.did]["REACHABILITY_EVT"]["value"]

    async def async_press(self) -> None:
        await self.hub.ping_device(self.did)
        await self.coordinator.async_request_refresh()
