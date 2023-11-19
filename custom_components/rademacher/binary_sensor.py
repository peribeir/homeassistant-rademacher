"""Platform for Rademacher Bridge"""
import logging

from homeassistant.helpers.entity import EntityCategory

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EXCLUDE, CONF_SENSOR_TYPE, STATE_OFF, STATE_ON
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.helpers.event import async_track_time_interval

from homepilot.device import HomePilotDevice
from homepilot.sensor import HomePilotSensor
from homepilot.manager import HomePilotManager
from homepilot.wallcontroller import HomePilotWallController

from .entity import HomePilotEntity

from .const import DOMAIN

from datetime import timedelta

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry: ConfigEntry, async_add_entities):
    """Setup of entities for binary_sensor platform"""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    manager: HomePilotManager = entry[0]
    coordinator: DataUpdateCoordinator = entry[1]
    exclude_devices: list[str] = entry[3][CONF_EXCLUDE]
    ternary_contact_sensors: list[str] = entry[3][CONF_SENSOR_TYPE]
    new_entities = []

    for did in manager.devices:
        if did not in exclude_devices:
            device: HomePilotDevice = manager.devices[did]
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
                if device.has_contact_state and device.did not in ternary_contact_sensors:
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
                if device.has_motion_detection:
                    _LOGGER.info("Found Motion Sensor for Device ID: %s", device.did)
                    new_entities.append(
                        HomePilotBinarySensorEntity(
                            coordinator=coordinator,
                            device=device,
                            id_suffix="motion_sensor",
                            name_suffix="Motion Sensor",
                            value_attr="motion_detection_value",
                            device_class=BinarySensorDeviceClass.MOTION,
                        )
                    )
                if device.has_smoke_detection:
                    _LOGGER.info("Found Smoke Sensor for Device ID: %s", device.did)
                    new_entities.append(
                        HomePilotBinarySensorEntity(
                            coordinator=coordinator,
                            device=device,
                            id_suffix="smoke_detect",
                            name_suffix="Smoke Detection",
                            value_attr="smoke_detection_value",
                            device_class=BinarySensorDeviceClass.SMOKE,
                        )
                    )
            if isinstance(device, HomePilotWallController):
                channels = device.channels
                if channels is not None:
                    _LOGGER.info("Found Wall Controller with %s Button(s) for Device ID: %s", str(len(channels)), device.did)
                    for channel in channels:
                        _LOGGER.info("Adding Wall Controller Button: %s", channel)
                        new_entities.append(
                            HomePilotBinarySensorEntity(
                                coordinator=coordinator,
                                device=device,
                                id_suffix=channel,
                                name_suffix=channel,
                                value_attr=f"channel_{channel}",
                                device_class=BinarySensorDeviceClass.RUNNING,
                                has_channels=True,
                                should_poll=channel == 1 #Only the first Channel needs to poll data of device
                            )
                        )
                else:
                    _LOGGER.info("No Wall Controller Channels for Device ID: %s", device.did)
                if device.has_battery_low:
                    _LOGGER.info(
                        "Found Battery Low Event for Device ID: %s", device.did
                    )
                    new_entities.append(
                        HomePilotBinarySensorEntity(
                            coordinator=coordinator,
                            device=device,
                            id_suffix="battery_low",
                            name_suffix="Battery Low",
                            value_attr="battery_low_value",
                            device_class=BinarySensorDeviceClass.BATTERY,
                            entity_category=EntityCategory.DIAGNOSTIC,
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
        has_channels=False,
        should_poll=True,
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
        self._has_channels = has_channels
        self._should_poll = should_poll

    async def async_added_to_hass(self) -> None:
        """Set up a timer for updating"""
        if self._has_channels:
            self.async_on_remove(
                async_track_time_interval(
                    self.hass, self._data_refresh, timedelta(seconds=2)
                )
            )

    async def _data_poll(self):
        _LOGGER.debug("### Pull data for Device ID: %s, %s, entity_id: %s", self.did, self._value_attr, self.entity_id)
        if isinstance(self.coordinator.data[self.did], HomePilotWallController):
            device: HomePilotWallController = self.coordinator.data[self.did]
            await device.update_channels()
            await self.coordinator.async_request_refresh()

    async def _data_refresh(self, event_time):
        if self._should_poll:
            await self._data_poll()
        self.async_write_ha_state()

    @property
    def should_poll(self):
        return self._should_poll

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
