"""Platform for Rademacher Bridge"""
from .rademacher_entity import RademacherEntity
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
)

from .const import (
    APICAP_ID_DEVICE_LOC,
    APICAP_NAME_DEVICE_LOC,
    APICAP_PROT_ID_DEVICE_LOC,
    APICAP_RAIN_DETECTION_MEA,
    DOMAIN,
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    hub = hass.data[DOMAIN][config_entry.entry_id]
    new_entities = []
    env_sensors = hub.env_sensors
    for device in env_sensors:
        device_info = hub.coordinator.data[device[APICAP_ID_DEVICE_LOC]["value"]]
        if APICAP_RAIN_DETECTION_MEA in device_info:
            new_entities.append(
                RademacherBinarySensor(
                    hub,
                    device_info,
                    "rain_detect",
                    "Rain Detection",
                    APICAP_RAIN_DETECTION_MEA,
                    "mdi:weather-rainy",
                    "mdi:weather-sunny",
                )
            )
    # If we have any new devices, add them
    if new_entities:
        async_add_entities(new_entities)


class RademacherBinarySensor(RademacherEntity, BinarySensorEntity):
    def __init__(
        self,
        hub,
        device,
        id_suffix,
        name_suffix,
        api_attr,
        icon_on,
        icon_off,
    ):
        super().__init__(
            hub,
            device,
            unique_id=f"{device[APICAP_PROT_ID_DEVICE_LOC]['value']}_f{id_suffix}",
            name=f"{device[APICAP_NAME_DEVICE_LOC]['value']} {name_suffix}",
        )
        self._api_attr = api_attr
        self._icon_on = icon_on
        self._icon_off = icon_off

    @property
    def is_on(self):
        return self.coordinator.data[self.did][self._api_attr]["value"] == "true"

    @property
    def icon(self):
        return self._icon_on if self.is_on else self._icon_off
