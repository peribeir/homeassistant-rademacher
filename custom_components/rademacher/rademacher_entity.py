from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import (
    APICAP_ID_DEVICE_LOC,
    APICAP_NAME_DEVICE_LOC,
    APICAP_PROD_CODE_DEVICE_LOC,
    APICAP_REACHABILITY_EVT,
    APICAP_VERSION_CFG,
    DOMAIN,
    SUPPORTED_DEVICES,
)


class RademacherEntity(CoordinatorEntity):
    def __init__(self, hub, device, unique_id, name, device_class=None, icon=None):
        super().__init__(hub.coordinator)
        self._hub = hub
        self._unique_id = unique_id
        self._name = name
        self._device_name = device[APICAP_NAME_DEVICE_LOC]["value"]
        self._device_class = device_class
        self._icon = icon
        self._did = device[APICAP_ID_DEVICE_LOC]["value"]
        self._model = SUPPORTED_DEVICES[device[APICAP_PROD_CODE_DEVICE_LOC]["value"]][
            "name"
        ]
        self._sw_version = device[APICAP_VERSION_CFG]["value"]

    @property
    def hub(self):
        return self._hub

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
    def model(self):
        return self._model

    @property
    def sw_version(self):
        return self._sw_version

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
            "sw_version": self.sw_version,
            "model": self.model,
            "manufacturer": "Rademacher",
        }

    @property
    def available(self):
        return self.coordinator.data[self.did][APICAP_REACHABILITY_EVT]["value"]
