"""Platform for Rademacher Bridge"""
from homeassistant.components.binary_sensor import (
    PLATFORM_SCHEMA,
    BinarySensorEntity,
)
from homeassistant.const import (
    CONF_HOST,
)
import homeassistant.helpers.config_validation as cv

import voluptuous as vol

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SUPPORTED_DEVICES

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({vol.Required(CONF_HOST): cv.string})


async def async_setup_entry(hass, config_entry, async_add_entities):
    hub = hass.data[DOMAIN][config_entry.entry_id]
    new_entities = []
    env_sensors = hub.env_sensors
    for device in env_sensors:
        device_info = hub.coordinator.data[device["ID_DEVICE_LOC"]["value"]]
        if "RAIN_DETECTION_MEA" in device_info:
            new_entities.append(
                RademacherBinarySensor(
                    hub,
                    device_info,
                    "rain_detect",
                    "Rain Detection",
                    "RAIN_DETECTION_MEA",
                    None,
                    "mdi:weather-rainy",
                    "mdi:weather-sunny",
                )
            )
    # If we have any new devices, add them
    if new_entities:
        async_add_entities(new_entities)


class RademacherBinarySensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(
        self,
        hub,
        device,
        id_suffix,
        name_suffix,
        api_attr,
        device_class,
        icon_on,
        icon_off,
    ):
        super().__init__(hub.coordinator)
        self._hub = hub
        self._did = device["ID_DEVICE_LOC"]["value"]
        self._device_name = f"{device['NAME_DEVICE_LOC']['value']}"
        self._device_class = device_class
        self._model = SUPPORTED_DEVICES[device["PROD_CODE_DEVICE_LOC"]["value"]]["name"]
        self._sw_version = device["VERSION_CFG"]["value"]
        self._uid = f"{device['PROT_ID_DEVICE_LOC']['value']}_f{id_suffix}"
        self._name = f"{device['NAME_DEVICE_LOC']['value']} {name_suffix}"
        self._api_attr = api_attr
        self._icon_on = icon_on
        self._icon_off = icon_off

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
    def device_class(self):
        return self._device_class

    @property
    def available(self):
        return self.coordinator.data[self.did]["REACHABILITY_EVT"]["value"]

    @property
    def is_on(self):
        return self.coordinator.data[self.did][self._api_attr]["value"] == "true"

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
    def icon(self):
        return self._icon_on if self.is_on else self._icon_off
