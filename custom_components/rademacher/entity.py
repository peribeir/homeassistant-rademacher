from collections.abc import Mapping
from typing import Any

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
        entity_registry_enabled_default=True,
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
        self._entity_registry_enabled_default = entity_registry_enabled_default

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
        # Use config entry unique_id (MAC address) + device_id for unique identifier
        hub_mac = self.coordinator.config_entry.unique_id or "unknown"
        device_identifier = f"{hub_mac}_{self.did}"
        device: HomePilotDevice = self.coordinator.data[self.did]

        # Build device info
        device_info = {
            "identifiers": {(DOMAIN, device_identifier)},
            "name": self.device_name,
            "sw_version": device.fw_version,
            "model": self.model,
            "model_id": str(self.did),
            "manufacturer": "Rademacher",
            "serial_number": device.uid.split('_')[0] if device.uid else None,
        }

        # Only add configuration_url for Rademacher HomePilot (have Web UI)
        # Newer HomePilot bridges (pure app-based) don't have web UI
        api_version = self.coordinator.config_entry.data.get('api_version', 1)
        if api_version == 1:
            device_info["configuration_url"] = f"http://{self.coordinator.config_entry.data.get('host', '')}/"

        return device_info

    @property
    def available(self):
        device: HomePilotDevice = self.coordinator.data[self.did]
        return device.available

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        device: HomePilotDevice = self.coordinator.data[self.did]
        return getattr(device, "extra_attributes")

    @property
    def entity_registry_enabled_default(self):
        return self._entity_registry_enabled_default
