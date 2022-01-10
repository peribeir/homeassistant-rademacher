"""Platform for Rademacher Bridge"""
from .rademacher_entity import RademacherEntity
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import EntityCategory
from .const import (
    APICAP_ID_DEVICE_LOC,
    APICAP_NAME_DEVICE_LOC,
    APICAP_PING_CMD,
    APICAP_PROT_ID_DEVICE_LOC,
    DOMAIN,
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    hub = hass.data[DOMAIN][config_entry.entry_id]
    new_entities = []
    supported_devices = hub.devices
    for device in supported_devices:
        device_info = hub.coordinator.data[device[APICAP_ID_DEVICE_LOC]["value"]]
        if APICAP_PING_CMD in device_info:
            new_entities.append(RademacherPingButton(hub, device_info))
    # If we have any new devices, add them
    if new_entities:
        async_add_entities(new_entities)


class RademacherPingButton(RademacherEntity, ButtonEntity):
    def __init__(self, hub, device):
        super().__init__(
            hub,
            device,
            unique_id=f"{device[APICAP_PROT_ID_DEVICE_LOC]['value']}_ping",
            name=f"{device[APICAP_NAME_DEVICE_LOC]['value']} Ping",
        )

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC

    @property
    def entity_registry_enabled_default(self):
        return False

    async def async_press(self) -> None:
        await self.hub.ping_device(self.did)
        await self.coordinator.async_request_refresh()
