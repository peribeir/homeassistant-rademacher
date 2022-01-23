import logging
from .api import HomePilotApi
from .const import (
    APICAP_DEVICE_TYPE_LOC,
    APICAP_ID_DEVICE_LOC,
    APICAP_PROD_CODE_DEVICE_LOC,
)
from .device import HomePilotDevice

_LOGGER = logging.getLogger(__name__)


class HomePilotHub(HomePilotDevice):
    _nodename: str
    _hub_type: str
    _hw_platform: str
    _sw_platform: str
    _fw_version: str
    _duofern_stick_version: str
    _fw_update_available: bool
    _fw_update_version: str
    _led_status: bool

    def __init__(
        self,
        api,
        did,
        uid,
        name,
        device_number,
        model,
        device_group,
        fw_version,
        duofern_stick_version,
        nodename,
        hw_platform,
        sw_platform,
    ) -> None:
        super().__init__(
            api=api,
            did=did,
            uid=uid,
            name=name,
            device_number=device_number,
            model=model,
            fw_version=fw_version,
            device_group=device_group,
            has_ping_cmd=False,
        )
        self._duofern_stick_version = duofern_stick_version
        self._nodename = nodename
        self._hub_type = "Start2Smart" if hw_platform else "ampere"
        self._hw_platform = hw_platform
        self._sw_platform = sw_platform

    @staticmethod
    async def build_from_api(api: HomePilotApi, did):
        fw_version = await api.get_fw_version()
        nodename: str = (await api.get_nodename())["nodename"]
        capabilities_map = HomePilotDevice.get_capabilities_map(
            HomePilotHub.get_capabilities()
        )
        return HomePilotHub(
            api=api,
            did=capabilities_map[APICAP_ID_DEVICE_LOC]["value"],
            uid=api.host,
            name=nodename.capitalize(),
            device_number=capabilities_map[APICAP_PROD_CODE_DEVICE_LOC]["value"],
            model="Start2Smart"
            if fw_version["sw_platform"] == "bridge"
            else "HomePilot",
            device_group=capabilities_map[APICAP_DEVICE_TYPE_LOC]["value"],
            fw_version=fw_version["version"],
            duofern_stick_version=fw_version["df_stick_version"],
            nodename=nodename,
            hw_platform=fw_version["hw_platform"],
            sw_platform=fw_version["sw_platform"],
        )

    @staticmethod
    def get_capabilities():
        return {
            "capabilities": [
                {"name": APICAP_ID_DEVICE_LOC, "value": "-1"},
                {"name": APICAP_DEVICE_TYPE_LOC, "value": "-1"},
                {"name": APICAP_PROD_CODE_DEVICE_LOC, "value": "-1"},
            ]
        }

    def update_state(self, state):
        self.available = True
        self.fw_update_available = (
            state["status"]["update_status"] != "NO_UPDATE_AVAILABLE"
        )
        self.fw_update_version = state["status"]["version"]
        self.led_status = state["led"]["status"] == "enabled"

    async def async_ping(self):
        pass

    async def async_turn_led_on(self) -> None:
        await self.api.turn_led_on()

    async def async_turn_led_off(self) -> None:
        await self.api.turn_led_off()

    @property
    def hub_type(self):
        return self._hub_type

    @property
    def fw_version(self):
        return self._fw_version

    @property
    def nodename(self):
        return self._nodename

    @property
    def hw_platform(self):
        return self._hw_platform

    @property
    def sw_platform(self):
        return self._sw_platform

    @property
    def duofern_stick_version(self):
        return self._duofern_stick_version

    @property
    def fw_update_available(self):
        return self._fw_update_available

    @fw_update_available.setter
    def fw_update_available(self, fw_update_available):
        self._fw_update_available = fw_update_available

    @property
    def fw_update_version(self):
        return self._fw_update_version

    @fw_update_version.setter
    def fw_update_version(self, fw_update_version):
        self._fw_update_version = fw_update_version

    @property
    def led_status(self):
        return self._led_status

    @led_status.setter
    def led_status(self, led_status):
        self._led_status = led_status

    @property
    def extra_attributes(self):
        extra_attributes = {
            "HW Platform": self.hw_platform,
            "SW Platform": self.sw_platform,
            "Duofern Version": self.duofern_stick_version,
            "Current FW Version": self.fw_version,
        }
        if self.fw_update_available:
            extra_attributes["New FW Update Version"] = self.fw_update_version
        return extra_attributes
