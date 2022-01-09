"""Platform for Rademacher Bridge"""
from aiohttp import (
    ClientError,
    ClientOSError,
    InvalidURL,
    TooManyRedirects,
    ServerTimeoutError,
)
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    CONF_HOST,
    DEGREE,
    LIGHT_LUX,
    SPEED_METERS_PER_SECOND,
    TEMP_CELSIUS,
)
import homeassistant.helpers.config_validation as cv

import voluptuous as vol

from .const import DOMAIN, SUPPORTED_DEVICES

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({vol.Required(CONF_HOST): cv.string})


async def async_setup_entry(hass, config_entry, async_add_entities):
    hub = hass.data[DOMAIN][config_entry.entry_id]
    new_entities = []
    env_sensors = await hub.get_env_sensors()
    for device in env_sensors:
        device_info = await hub.get_device(device["ID_DEVICE_LOC"]["value"])
        if "TEMP_CURR_DEG_MEA" in device_info:
            new_entities.append(
                RademacherSensor(
                    hub,
                    device_info,
                    "temp",
                    "Temperature",
                    "TEMP_CURR_DEG_MEA",
                    SensorDeviceClass.TEMPERATURE.value,
                    TEMP_CELSIUS,
                    None,
                )
            )
        if "WIND_SPEED_MS_MEA" in device_info:
            new_entities.append(
                RademacherSensor(
                    hub,
                    device_info,
                    "wind_speed",
                    "Wind Speed",
                    "WIND_SPEED_MS_MEA",
                    None,
                    SPEED_METERS_PER_SECOND,
                    "mdi:weather-windy",
                )
            )
        if "LIGHT_VAL_LUX_MEA" in device_info:
            new_entities.append(
                RademacherSensor(
                    hub,
                    device_info,
                    "brightness",
                    "Brightness",
                    "LIGHT_VAL_LUX_MEA",
                    SensorDeviceClass.ILLUMINANCE.value,
                    LIGHT_LUX,
                    None,
                )
            )
        if "SUN_HEIGHT_DEG_MEA" in device_info:
            new_entities.append(
                RademacherSensor(
                    hub,
                    device_info,
                    "sun_height",
                    "Sun Height",
                    "SUN_HEIGHT_DEG_MEA",
                    None,
                    DEGREE,
                    "mdi:weather-sunset-up",
                )
            )
        if "SUN_DIRECTION_MEA" in device_info:
            new_entities.append(
                RademacherSensor(
                    hub,
                    device_info,
                    "sun_direction",
                    "Sun Direction",
                    "SUN_DIRECTION_MEA",
                    None,
                    DEGREE,
                    "mdi:sun-compass",
                )
            )
    # If we have any new devices, add them
    if new_entities:
        async_add_entities(new_entities)


class RademacherSensor(SensorEntity):
    def __init__(
        self,
        hub,
        device,
        id_suffix,
        name_suffix,
        api_attr,
        device_class,
        native_unit_of_measurement,
        icon,
    ):
        self._hub = hub
        self._did = device["ID_DEVICE_LOC"]["value"]
        self._device_name = f"{device['NAME_DEVICE_LOC']['value']}"
        self._device_class = device_class
        self._native_unit_of_measurement = native_unit_of_measurement
        self._model = SUPPORTED_DEVICES[device["PROD_CODE_DEVICE_LOC"]["value"]]["name"]
        self._sw_version = device["VERSION_CFG"]["value"]
        self._uid = f"{device['PROT_ID_DEVICE_LOC']['value']}_f{id_suffix}"
        self._name = f"{device['NAME_DEVICE_LOC']['value']} {name_suffix}"
        self._api_attr = api_attr
        self._icon = icon
        self._native_value = float(device[self._api_attr]["value"])
        self._available: bool = bool(device["REACHABILITY_EVT"]["value"])

    @property
    def device_info(self):
        """Information about this entity/device."""
        return {
            "identifiers": {(DOMAIN, self._did)},
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
    def native_unit_of_measurement(self):
        return self._native_unit_of_measurement

    @property
    def state_class(self):
        return SensorStateClass.MEASUREMENT

    @property
    def available(self):
        return self._available

    @property
    def native_value(self):
        return self._native_value

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
        return self._icon

    async def async_update(self):
        try:
            device = await self._hub.get_device(self._did)

            if device:
                self._available = device["REACHABILITY_EVT"]["value"]
                self._native_value = float(device[self._api_attr]["value"])
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
