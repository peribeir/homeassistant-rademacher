""" This class represents a device in HomePilot GW """

from .api import HomePilotApi

from .const import (
    APICAP_DEVICE_TYPE_LOC,
    APICAP_ID_DEVICE_LOC,
)


class HomePilotDevice:
    """HomePilot Device"""

    _api: HomePilotApi
    _did: int
    _uid: str
    _name: str
    _device_number: str
    _model: str
    _fw_version: str
    _device_group: int
    _manufacturer: str = "Rademacher"
    _has_ping_cmd: bool
    _available: bool

    def __init__(
        self,
        api: HomePilotApi,
        did: int,
        uid: str,
        name: str,
        device_number: str,
        model: str,
        fw_version: str,
        device_group: int,
        has_ping_cmd: bool = False,
    ) -> None:
        self._api = api
        self._did = did
        self._uid = uid
        self._name = name
        self._device_number = device_number
        self._model = model
        self._fw_version = fw_version
        self._device_group = device_group
        self._has_ping_cmd = has_ping_cmd

    @staticmethod
    def get_capabilities_map(device):
        """Returns a map containing the capabilities of a device from a response of API"""
        return {
            capability["name"]: {
                "value": capability["value"] if "value" in capability else None,
                "read_only": capability["read_only"]
                if "read_only" in capability
                else None,
                "timestamp": capability["timestamp"]
                if "timestamp" in capability
                else None,
            }
            for capability in device["capabilities"]
        }

    @staticmethod
    def get_did_type_from_json(device):
        device_map = HomePilotDevice.get_capabilities_map(device)
        return {
            "did": device_map[APICAP_ID_DEVICE_LOC]["value"],
            "type": device_map[APICAP_DEVICE_TYPE_LOC]["value"],
        }

    def update_state(self, state):
        self.available = state["statusValid"]

    async def async_ping(self):
        if self.has_ping_cmd:
            await self.api.ping(self.did)

    @property
    def api(self) -> HomePilotApi:
        return self._api

    @property
    def did(self):
        return self._did

    @property
    def uid(self):
        return self._uid

    @property
    def name(self):
        return self._name

    @property
    def device_number(self):
        return self._device_number

    @property
    def model(self):
        return self._model

    @property
    def fw_version(self):
        return self._fw_version

    @property
    def device_group(self):
        return self._device_group

    @property
    def manufacturer(self):
        return self._manufacturer

    @property
    def has_ping_cmd(self):
        return self._has_ping_cmd

    @property
    def available(self) -> bool:
        return self._available

    @available.setter
    def available(self, available):
        self._available = available
