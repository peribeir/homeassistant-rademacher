from .sensor import HomePilotSensor
from .switch import HomePilotSwitch
from .cover import HomePilotCover
from .api import HomePilotApi

from .device import HomePilotDevice


class HomePilotHub:
    _api: HomePilotApi
    _devices: dict[str, HomePilotDevice]

    def __init__(self, host: str, password: str) -> None:
        self._api = HomePilotApi(host, password)

    @staticmethod
    async def build_hub(host: str, password: str):
        hub = HomePilotHub(host=host, password=password)
        hub.devices = {
            id_type["did"]: await HomePilotHub.build_device(hub.api, id_type)
            for id_type in await hub.get_device_ids_types()
            if id_type["type"] in ["1", "2", "3"]
        }
        return hub

    @staticmethod
    async def build_device(api, id_type):
        if id_type["type"] == "1":
            return await HomePilotSwitch.build_from_api(api, id_type["did"])
        if id_type["type"] == "2":
            return await HomePilotCover.build_from_api(api, id_type["did"])
        if id_type["type"] == "3":
            return await HomePilotSensor.build_from_api(api, id_type["did"])
        return None

    async def update_states(self):
        try:
            states = await self.api.get_devices_state()
        except Exception:
            for did in self.devices:
                device: HomePilotDevice = self.devices[did]
                device.available = False
            raise

        for did in self.devices:
            device: HomePilotDevice = self.devices[did]
            if device.did in states:
                device.update_state(states[did])
            else:
                device.available = False

        return self.devices

    async def get_device_ids_types(self):
        return [
            HomePilotDevice.get_did_type_from_json(device)
            for device in await self.api.get_devices()
        ]

    @property
    def api(self) -> HomePilotApi:
        return self._api

    @property
    def devices(self):
        return self._devices

    @devices.setter
    def devices(self, devices):
        self._devices = devices
