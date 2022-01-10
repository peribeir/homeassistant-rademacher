"""Platform for Rademacher Bridge"""
from .rademacher_entity import RademacherEntity
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    DEGREE,
    LIGHT_LUX,
    SPEED_METERS_PER_SECOND,
    TEMP_CELSIUS,
)
from .const import (
    APICAP_ID_DEVICE_LOC,
    APICAP_LIGHT_VAL_LUX_MEA,
    APICAP_NAME_DEVICE_LOC,
    APICAP_PROT_ID_DEVICE_LOC,
    APICAP_SUN_DIRECTION_MEA,
    APICAP_SUN_HEIGHT_DEG_MEA,
    APICAP_TEMP_CURR_DEG_MEA,
    APICAP_WIND_SPEED_MS_MEA,
    DOMAIN,
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    hub = hass.data[DOMAIN][config_entry.entry_id]
    new_entities = []
    env_sensors = hub.env_sensors
    for device in env_sensors:
        device_info = hub.coordinator.data[device[APICAP_ID_DEVICE_LOC]["value"]]
        if APICAP_TEMP_CURR_DEG_MEA in device_info:
            new_entities.append(
                RademacherSensor(
                    hub,
                    device_info,
                    "temp",
                    "Temperature",
                    APICAP_TEMP_CURR_DEG_MEA,
                    SensorDeviceClass.TEMPERATURE.value,
                    TEMP_CELSIUS,
                    None,
                )
            )
        if APICAP_WIND_SPEED_MS_MEA in device_info:
            new_entities.append(
                RademacherSensor(
                    hub,
                    device_info,
                    "wind_speed",
                    "Wind Speed",
                    APICAP_WIND_SPEED_MS_MEA,
                    None,
                    SPEED_METERS_PER_SECOND,
                    "mdi:weather-windy",
                )
            )
        if APICAP_LIGHT_VAL_LUX_MEA in device_info:
            new_entities.append(
                RademacherSensor(
                    hub,
                    device_info,
                    "brightness",
                    "Brightness",
                    APICAP_LIGHT_VAL_LUX_MEA,
                    SensorDeviceClass.ILLUMINANCE.value,
                    LIGHT_LUX,
                    None,
                )
            )
        if APICAP_SUN_HEIGHT_DEG_MEA in device_info:
            new_entities.append(
                RademacherSensor(
                    hub,
                    device_info,
                    "sun_height",
                    "Sun Height",
                    APICAP_SUN_HEIGHT_DEG_MEA,
                    None,
                    DEGREE,
                    "mdi:weather-sunset-up",
                )
            )
        if APICAP_SUN_DIRECTION_MEA in device_info:
            new_entities.append(
                RademacherSensor(
                    hub,
                    device_info,
                    "sun_direction",
                    "Sun Direction",
                    APICAP_SUN_DIRECTION_MEA,
                    None,
                    DEGREE,
                    "mdi:sun-compass",
                )
            )
    # If we have any new devices, add them
    if new_entities:
        async_add_entities(new_entities)


class RademacherSensor(RademacherEntity, SensorEntity):
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
        super().__init__(
            hub,
            device,
            unique_id=f"{device[APICAP_PROT_ID_DEVICE_LOC]['value']}_f{id_suffix}",
            name=f"{device[APICAP_NAME_DEVICE_LOC]['value']} {name_suffix}",
            device_class=device_class,
            icon=icon,
        )
        self._api_attr = api_attr
        self._native_unit_of_measurement = native_unit_of_measurement

    @property
    def native_unit_of_measurement(self):
        return self._native_unit_of_measurement

    @property
    def state_class(self):
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        return float(self.coordinator.data[self.did][self._api_attr]["value"])
