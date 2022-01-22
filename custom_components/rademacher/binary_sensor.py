"""Platform for Rademacher Bridge"""
import logging

from homeassistant.helpers.entity import EntityCategory
from .homepilot.hub import HomePilotHub

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EXCLUDE
from .homepilot.device import HomePilotDevice
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)
from .homepilot.sensor import HomePilotSensor
from .homepilot.manager import HomePilotManager
from .entity import HomePilotEntity
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry: ConfigEntry, async_add_entities):
    """Setup of entities for binary_sensor platform"""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    manager: HomePilotManager = entry[0]
    coordinator: DataUpdateCoordinator = entry[1]
    exclude_devices: list[str] = entry[3][CONF_EXCLUDE]
    new_entities = []

    for did in manager.devices:
        if did not in exclude_devices:
            device: HomePilotDevice = manager.devices[did]
            if isinstance(device, HomePilotHub):
                _LOGGER.info("Found FW Update Sensor for Device ID: %s", device.did)
                new_entities.append(
                    HomePilotBinarySensorEntity(
                        coordinator=coordinator,
                        device=device,
                        id_suffix="fw_update",
                        name_suffix="FW Update",
                        value_attr="fw_update_available",
                        device_class=BinarySensorDeviceClass.UPDATE,
                        entity_category=EntityCategory.DIAGNOSTIC,
                    )
                )
            if isinstance(device, HomePilotSensor):
                if device.has_rain_detection:
                    _LOGGER.info(
                        "Found Rain Detection Sensor for Device ID: %s", device.did
                    )
                    new_entities.append(
                        HomePilotBinarySensorEntity(
                            coordinator=coordinator,
                            device=device,
                            id_suffix="rain_detect",
                            name_suffix="Rain Detection",
                            value_attr="rain_detection_value",
                            device_class=BinarySensorDeviceClass.MOISTURE,
                        )
                    )
                if device.has_sun_detection:
                    _LOGGER.info(
                        "Found Sun Detection Sensor for Device ID: %s", device.did
                    )
                    new_entities.append(
                        HomePilotBinarySensorEntity(
                            coordinator=coordinator,
                            device=device,
                            id_suffix="sun_detect",
                            name_suffix="Sun Detection",
                            value_attr="sun_detection_value",
                            device_class=BinarySensorDeviceClass.LIGHT,
                        )
                    )
                if device.has_contact_state:
                    _LOGGER.info("Found Contact Sensor for Device ID: %s", device.did)
                    new_entities.append(
                        HomePilotBinarySensorEntity(
                            coordinator=coordinator,
                            device=device,
                            id_suffix="contact_state",
                            name_suffix="Contact State",
                            value_attr="contact_state_value",
                            device_class=BinarySensorDeviceClass.OPENING,
                        )
                    )
    # If we have any new devices, add them
    if new_entities:
        async_add_entities(new_entities)


class HomePilotBinarySensorEntity(HomePilotEntity, BinarySensorEntity):
    """This class represents all Binary Sensors supported"""

    def __init__(
        self,
        coordinator,
        device: HomePilotSensor,
        id_suffix,
        name_suffix,
        value_attr,
        device_class,
        entity_category=None,
        icon_on=None,
        icon_off=None,
    ):
        super().__init__(
            coordinator,
            device,
            unique_id=f"{device.uid}_f{id_suffix}",
            name=f"{device.name} {name_suffix}",
            device_class=device_class,
            entity_category=entity_category,
        )
        self._value_attr = value_attr
        self._icon_on = icon_on
        self._icon_off = icon_off

    @property
    def value_attr(self):
        """This property stores which attribute contains the is_on value on
        the HomePilotDevice supporting class"""
        return self._value_attr

    @property
    def is_on(self):
        value = getattr(self.coordinator.data[self.did], self.value_attr)
        return value if isinstance(value, bool) else value.value

    @property
    def icon(self):
        return self._icon_on if self.is_on else self._icon_off
