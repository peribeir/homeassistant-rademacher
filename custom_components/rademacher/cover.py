"""Platform for Rademacher Bridge"""
from typing import Any
from .rademacher_entity import RademacherEntity

from homeassistant.components.cover import (
    CoverEntity,
    CoverDeviceClass,
)
from homeassistant.components.cover import (
    ATTR_POSITION,
    SUPPORT_OPEN,
    SUPPORT_CLOSE,
    SUPPORT_STOP,
    SUPPORT_SET_POSITION,
)
from .const import (
    APICAP_CURR_POS_CFG,
    APICAP_GOTO_POS_CMD,
    APICAP_ID_DEVICE_LOC,
    APICAP_NAME_DEVICE_LOC,
    APICAP_PROT_ID_DEVICE_LOC,
    DOMAIN,
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    hub = hass.data[DOMAIN][config_entry.entry_id]
    new_entities = []
    covers = hub.covers
    for cover in covers:
        cover_info = hub.coordinator.data[cover[APICAP_ID_DEVICE_LOC]["value"]]
        cover_entity = RademacherCoverEntity(hub, cover_info)
        new_entities.append(cover_entity)
    # If we have any new devices, add them
    if new_entities:
        async_add_entities(new_entities)


class RademacherCoverEntity(RademacherEntity, CoverEntity):
    def __init__(self, hub, device):
        super().__init__(
            hub,
            device,
            unique_id=device[APICAP_PROT_ID_DEVICE_LOC]["value"],
            name=device[APICAP_NAME_DEVICE_LOC]["value"],
            device_class=CoverDeviceClass.SHUTTER.value,
        )
        self._supported_features = SUPPORT_STOP | SUPPORT_CLOSE | SUPPORT_OPEN
        if APICAP_GOTO_POS_CMD in device:
            self._supported_features |= SUPPORT_SET_POSITION

    @property
    def supported_features(self):
        return self._supported_features

    @property
    def current_cover_position(self):
        return 100 - int(self.coordinator.data[self.did][APICAP_CURR_POS_CFG]["value"])

    @property
    def is_closing(self):
        return False

    @property
    def is_opening(self):
        return False

    @property
    def is_closed(self):
        return self.current_cover_position == 0

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self.hub.open_cover(self.did)
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self.hub.close_cover(self.did)
        await self.coordinator.async_request_refresh()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        await self.hub.set_cover_position(self.did, kwargs[ATTR_POSITION])
        await self.coordinator.async_request_refresh()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        await self.hub.stop_cover(self.did)
        await self.coordinator.async_request_refresh()
