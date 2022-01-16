"""Platform for Rademacher Bridge"""
import logging
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .homepilot.hub import HomePilotHub
from .homepilot.device import HomePilotDevice
from .homepilot.sensor import HomePilotSensor
from .entity import HomePilotEntity
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    CONF_BINARY_SENSORS,
    DEGREE,
    LIGHT_LUX,
    SPEED_METERS_PER_SECOND,
    TEMP_CELSIUS,
)
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    entry = hass.data[DOMAIN][config_entry.entry_id]
    hub: HomePilotHub = entry[0]
    coordinator: DataUpdateCoordinator = entry[1]
    binary_sensors: bool = entry[2][CONF_BINARY_SENSORS]
    new_entities = []
    for did in hub.devices:
        device: HomePilotDevice = hub.devices[did]
        if isinstance(device, HomePilotSensor):
            if device.has_sun_detection and not binary_sensors:
                _LOGGER.info("Found Sun Detection Sensor for Device ID: %s", device.did)
                new_entities.append(
                    HomePilotSensorEntity(
                        coordinator,
                        device,
                        "sun_detection",
                        "Sun Detection",
                        "sun_detection_value",
                        None,
                        None,
                        "mdi:weather-sunny",
                    )
                )
            if device.has_rain_detection and not binary_sensors:
                _LOGGER.info(
                    "Found Rain Detection Sensor for Device ID: %s", device.did
                )
                new_entities.append(
                    HomePilotSensorEntity(
                        coordinator,
                        device,
                        "rain_detection",
                        "Rain Detection",
                        "rain_detection_value",
                        None,
                        None,
                        "mdi:weather-rainy",
                    )
                )
            if device.has_temperature:
                _LOGGER.info("Found Temperature Sensor for Device ID: %s", device.did)
                new_entities.append(
                    HomePilotSensorEntity(
                        coordinator,
                        device,
                        "temp",
                        "Temperature",
                        "temperature_value",
                        SensorDeviceClass.TEMPERATURE.value,
                        TEMP_CELSIUS,
                        None,
                    )
                )
            if device.has_wind_speed:
                _LOGGER.info("Found Wind Speed Sensor for Device ID: %s", device.did)
                new_entities.append(
                    HomePilotSensorEntity(
                        coordinator,
                        device,
                        "wind_speed",
                        "Wind Speed",
                        "wind_speed_value",
                        None,
                        SPEED_METERS_PER_SECOND,
                        "mdi:weather-windy",
                    )
                )
            if device.has_brightness:
                _LOGGER.info("Found Brightness Sensor for Device ID: %s", device.did)
                new_entities.append(
                    HomePilotSensorEntity(
                        coordinator,
                        device,
                        "brightness",
                        "Brightness",
                        "brightness_value",
                        SensorDeviceClass.ILLUMINANCE.value,
                        LIGHT_LUX,
                        None,
                    )
                )
            if device.has_sun_height:
                _LOGGER.info("Found Sun Height Sensor for Device ID: %s", device.did)
                new_entities.append(
                    HomePilotSensorEntity(
                        coordinator,
                        device,
                        "sun_height",
                        "Sun Height",
                        "sun_height_value",
                        None,
                        DEGREE,
                        "mdi:weather-sunset-up",
                    )
                )
            if device.has_sun_direction:
                _LOGGER.info("Found Sun Direction Sensor for Device ID: %s", device.did)
                new_entities.append(
                    HomePilotSensorEntity(
                        coordinator,
                        device,
                        "sun_direction",
                        "Sun Direction",
                        "sun_direction_value",
                        None,
                        DEGREE,
                        "mdi:sun-compass",
                    )
                )
    # If we have any new devices, add them
    if new_entities:
        async_add_entities(new_entities)


class HomePilotSensorEntity(HomePilotEntity, SensorEntity):
    def __init__(
        self,
        coordinator,
        device: HomePilotSensor,
        id_suffix,
        name_suffix,
        value_attr,
        device_class,
        native_unit_of_measurement,
        icon,
    ) -> None:
        super().__init__(
            coordinator,
            device,
            unique_id=f"{device.uid}_f{id_suffix}",
            name=f"{device.name} {name_suffix}",
            device_class=device_class,
            icon=icon,
        )
        self._value_attr = value_attr
        self._native_unit_of_measurement = native_unit_of_measurement
        self._id_suffix = id_suffix

    @property
    def value_attr(self):
        return self._value_attr

    @property
    def native_unit_of_measurement(self):
        return self._native_unit_of_measurement

    @property
    def state_class(self):
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        if self._id_suffix == "sun_detection":
            return (
                "Sun Detected"
                if getattr(self.coordinator.data[self.did], self.value_attr)
                else "No Sun Detected"
            )
        if self._id_suffix == "rain_detection":
            return (
                "Rain Detected"
                if getattr(self.coordinator.data[self.did], self.value_attr)
                else "No Rain Detected"
            )
        return getattr(self.coordinator.data[self.did], self.value_attr)
