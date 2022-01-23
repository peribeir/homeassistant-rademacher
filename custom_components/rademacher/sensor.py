"""Platform for Rademacher Bridge"""
import logging
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .homepilot.manager import HomePilotManager
from .homepilot.device import HomePilotDevice
from .homepilot.sensor import HomePilotSensor
from .entity import HomePilotEntity
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    CONF_EXCLUDE,
    DEGREE,
    LIGHT_LUX,
    PERCENTAGE,
    SPEED_METERS_PER_SECOND,
    TEMP_CELSIUS,
)
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup of entities for sensor platform"""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    manager: HomePilotManager = entry[0]
    coordinator: DataUpdateCoordinator = entry[1]
    exclude_devices: list[str] = entry[3][CONF_EXCLUDE]
    new_entities = []
    for did in manager.devices:
        if did not in exclude_devices:
            device: HomePilotDevice = manager.devices[did]
            if isinstance(device, HomePilotSensor):
                if device.has_temperature:
                    _LOGGER.info(
                        "Found Temperature Sensor for Device ID: %s", device.did
                    )
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
                    _LOGGER.info(
                        "Found Wind Speed Sensor for Device ID: %s", device.did
                    )
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
                    _LOGGER.info(
                        "Found Brightness Sensor for Device ID: %s", device.did
                    )
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
                    _LOGGER.info(
                        "Found Sun Height Sensor for Device ID: %s", device.did
                    )
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
                    _LOGGER.info(
                        "Found Sun Direction Sensor for Device ID: %s", device.did
                    )
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
                if device.has_battery_level:
                    _LOGGER.info(
                        "Found Battery Level Sensor for Device ID: %s", device.did
                    )
                    new_entities.append(
                        HomePilotSensorEntity(
                            coordinator=coordinator,
                            device=device,
                            id_suffix="battery_level",
                            name_suffix="Battery Level",
                            value_attr="battery_level_value",
                            device_class=SensorDeviceClass.BATTERY,
                            native_unit_of_measurement=PERCENTAGE,
                            icon=None,
                            entity_category=EntityCategory.DIAGNOSTIC,
                        )
                    )
    # If we have any new devices, add them
    if new_entities:
        async_add_entities(new_entities)


class HomePilotSensorEntity(HomePilotEntity, SensorEntity):
    """This class represents all Sensors supported"""

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
        entity_category=None,
    ) -> None:
        super().__init__(
            coordinator,
            device,
            unique_id=f"{device.uid}_f{id_suffix}",
            name=f"{device.name} {name_suffix}",
            device_class=device_class,
            icon=icon,
            entity_category=entity_category,
        )
        self._value_attr = value_attr
        self._native_unit_of_measurement = native_unit_of_measurement

    @property
    def value_attr(self):
        """This property stores which attribute contains the is_on value on
        the HomePilotDevice supporting class"""
        return self._value_attr

    @property
    def native_unit_of_measurement(self):
        return self._native_unit_of_measurement

    @property
    def state_class(self):
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        return getattr(self.coordinator.data[self.did], self.value_attr)
