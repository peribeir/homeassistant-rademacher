from typing import Any
from collections.abc import Mapping
from homepilot.device import HomePilotDevice
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN


class HomePilotEntity(CoordinatorEntity):
    def __init__(
        self,
        coordinator,
        device: HomePilotDevice,
        unique_id,
        name,
        device_class=None,
        entity_category=None,
        icon=None,
    ):
        super().__init__(coordinator)
        self._unique_id = unique_id
        self._name = name
        self._device_name = device.name
        self._device_class = device_class
        self._entity_category = entity_category
        self._icon = icon
        self._did = device.did
        self._model = device.model

    @property
    def did(self):
        return self._did

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def name(self):
        return self._name

    @property
    def device_name(self):
        return self._device_name

    @property
    def device_class(self):
        return self._device_class

    @property
    def entity_category(self):
        return self._entity_category

    @property
    def model(self):
        return self._model

    @property
    def sw_version(self):
        return self.coordinator.data[self.did].fw_version

    @property
    def icon(self):
        return self._icon

    @property
    def device_info(self):
        """Information about this entity/device."""
        return {
            "identifiers": {(DOMAIN, self.did)},
            # If desired, the name for the device could be different to the entity
            "name": self.device_name,
            "sw_version": self.coordinator.data[self.did].fw_version,
            "model": self.model,
            "manufacturer": "Rademacher",
        }

    @property
    def available(self):
        device: HomePilotDevice = self.coordinator.data[self.did]
        return device.available

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        device: HomePilotDevice = self.coordinator.data[self.did]
        return getattr(device, "extra_attributes")
