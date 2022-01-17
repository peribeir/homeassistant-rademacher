from enum import Enum
from .const import (
    APICAP_CLOSE_CONTACT_MEA,
    APICAP_DEVICE_TYPE_LOC,
    APICAP_ID_DEVICE_LOC,
    APICAP_LIGHT_VAL_LUX_MEA,
    APICAP_NAME_DEVICE_LOC,
    APICAP_PING_CMD,
    APICAP_PROD_CODE_DEVICE_LOC,
    APICAP_PROT_ID_DEVICE_LOC,
    APICAP_RAIN_DETECTION_MEA,
    APICAP_SUN_DETECTION_MEA,
    APICAP_SUN_DIRECTION_MEA,
    APICAP_SUN_HEIGHT_DEG_MEA,
    APICAP_TEMP_CURR_DEG_MEA,
    APICAP_VERSION_CFG,
    APICAP_WIND_SPEED_MS_MEA,
    SUPPORTED_DEVICES,
)
from .api import HomePilotApi
from .device import HomePilotDevice


class ContactState(Enum):
    OPENED = True
    CLOSED = False


class HomePilotSensor(HomePilotDevice):
    _has_temperature: bool
    _temperature_value: float
    _has_wind_speed: bool
    _wind_speed_value: float
    _has_brightness: bool
    _brightness_value: float
    _has_sun_height: bool
    _sun_height_value: float
    _has_sun_direction: bool
    _sun_direction_value: float
    _has_rain_detection: bool
    _rain_detection_value: bool
    _has_sun_detection: bool
    _sun_detection_value: bool
    _has_contact_state: bool
    _contact_state_value: ContactState

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
        has_temperature: bool = False,
        has_wind_speed: bool = False,
        has_brightness: bool = False,
        has_sun_height: bool = False,
        has_sun_direction: bool = False,
        has_rain_detection: bool = False,
        has_sun_detection: bool = False,
        has_contact_state: bool = False,
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
            has_ping_cmd=has_ping_cmd,
        )
        self._has_temperature = has_temperature
        self._has_wind_speed = has_wind_speed
        self._has_brightness = has_brightness
        self._has_sun_height = has_sun_height
        self._has_sun_direction = has_sun_direction
        self._has_rain_detection = has_rain_detection
        self._has_sun_detection = has_sun_detection
        self._has_contact_state = has_contact_state

    @staticmethod
    async def build_from_api(api: HomePilotApi, did):
        """Build a new HomePilotDevice from the response of API"""
        device = await api.get_device(did)
        device_map = HomePilotDevice.get_capabilities_map(device)
        return HomePilotSensor(
            api=api,
            did=device_map[APICAP_ID_DEVICE_LOC]["value"],
            uid=device_map[APICAP_PROT_ID_DEVICE_LOC]["value"],
            name=device_map[APICAP_NAME_DEVICE_LOC]["value"],
            device_number=device_map[APICAP_PROD_CODE_DEVICE_LOC]["value"],
            model=SUPPORTED_DEVICES[device_map[APICAP_PROD_CODE_DEVICE_LOC]["value"]][
                "name"
            ]
            if device_map[APICAP_PROD_CODE_DEVICE_LOC]["value"] in SUPPORTED_DEVICES
            else "Generic Device",
            fw_version=device_map[APICAP_VERSION_CFG]["value"],
            device_group=device_map[APICAP_DEVICE_TYPE_LOC]["value"],
            has_ping_cmd=APICAP_PING_CMD in device_map,
            has_temperature=APICAP_TEMP_CURR_DEG_MEA in device_map,
            has_wind_speed=APICAP_WIND_SPEED_MS_MEA in device_map,
            has_brightness=APICAP_LIGHT_VAL_LUX_MEA in device_map,
            has_sun_height=APICAP_SUN_HEIGHT_DEG_MEA in device_map,
            has_sun_direction=APICAP_SUN_DIRECTION_MEA in device_map,
            has_rain_detection=APICAP_RAIN_DETECTION_MEA in device_map,
            has_sun_detection=APICAP_SUN_DETECTION_MEA in device_map,
            has_contact_state=APICAP_CLOSE_CONTACT_MEA in device_map,
        )

    def update_state(self, state):
        super().update_state(state)
        if self.has_temperature:
            self.temperature_value = state["readings"]["temperature_primary"]
        if self.has_wind_speed:
            self.wind_speed_value = state["readings"]["wind_speed"]
        if self.has_brightness:
            self.brightness_value = state["readings"]["sun_brightness"]
        if self.has_sun_height:
            self.sun_height_value = state["readings"]["sun_elevation"]
        if self.has_sun_direction:
            self.sun_direction_value = state["readings"]["sun_direction"]
        if self.has_rain_detection:
            self.rain_detection_value = state["readings"]["rain_detected"]
        if self.has_sun_detection:
            self.sun_detection_value = state["readings"]["sun_detected"]
        if self.has_contact_state:
            self.contact_state_value = (
                ContactState.CLOSED
                if state["readings"]["contact_state"] == "closed"
                else ContactState.OPENED
            )

    @property
    def has_temperature(self) -> bool:
        return self._has_temperature

    @property
    def has_wind_speed(self) -> bool:
        return self._has_wind_speed

    @property
    def has_brightness(self) -> bool:
        return self._has_brightness

    @property
    def has_sun_height(self) -> bool:
        return self._has_sun_height

    @property
    def has_sun_direction(self) -> bool:
        return self._has_sun_direction

    @property
    def has_rain_detection(self) -> bool:
        return self._has_rain_detection

    @property
    def has_sun_detection(self) -> bool:
        return self._has_sun_detection

    @property
    def has_contact_state(self) -> bool:
        return self._has_contact_state

    @property
    def temperature_value(self) -> float:
        return self._temperature_value

    @temperature_value.setter
    def temperature_value(self, temperature_value):
        self._temperature_value = temperature_value

    @property
    def wind_speed_value(self) -> float:
        return self._wind_speed_value

    @wind_speed_value.setter
    def wind_speed_value(self, wind_speed_value):
        self._wind_speed_value = wind_speed_value

    @property
    def brightness_value(self) -> float:
        return self._brightness_value

    @brightness_value.setter
    def brightness_value(self, brightness_value):
        self._brightness_value = brightness_value

    @property
    def sun_height_value(self) -> float:
        return self._sun_height_value

    @sun_height_value.setter
    def sun_height_value(self, sun_height_value):
        self._sun_height_value = sun_height_value

    @property
    def sun_direction_value(self) -> float:
        return self._sun_direction_value

    @sun_direction_value.setter
    def sun_direction_value(self, sun_direction_value):
        self._sun_direction_value = sun_direction_value

    @property
    def rain_detection_value(self) -> bool:
        return self._rain_detection_value

    @rain_detection_value.setter
    def rain_detection_value(self, rain_detection_value):
        self._rain_detection_value = rain_detection_value

    @property
    def sun_detection_value(self) -> bool:
        return self._sun_detection_value

    @sun_detection_value.setter
    def sun_detection_value(self, sun_detection_value):
        self._sun_detection_value = sun_detection_value

    @property
    def contact_state_value(self) -> ContactState:
        return self._contact_state_value

    @contact_state_value.setter
    def contact_state_value(self, contact_state_value):
        self._contact_state_value = contact_state_value
