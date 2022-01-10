"""Platform for Rademacher Bridge"""
from .rademacher_entity import RademacherEntity
from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from .const import (
    APICAP_CURR_SWITCH_POS_CFG,
    APICAP_ID_DEVICE_LOC,
    APICAP_NAME_DEVICE_LOC,
    APICAP_PROT_ID_DEVICE_LOC,
    DOMAIN,
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    hub = hass.data[DOMAIN][config_entry.entry_id]
    new_entities = []
    switch_actuators = hub.switch_actuators
    for device in switch_actuators:
        device_info = hub.coordinator.data[device[APICAP_ID_DEVICE_LOC]["value"]]
        new_entities.append(RademacherSwitchActuator(hub, device_info))
    # If we have any new devices, add them
    if new_entities:
        async_add_entities(new_entities)


class RademacherSwitchActuator(RademacherEntity, SwitchEntity):
    def __init__(self, hub, device):
        super().__init__(
            hub,
            device,
            unique_id=device[APICAP_PROT_ID_DEVICE_LOC]["value"],
            name=device[APICAP_NAME_DEVICE_LOC]["value"],
            device_class=SwitchDeviceClass.SWITCH.value,
        )

    @property
    def is_on(self):
        return (
            self.coordinator.data[self.did][APICAP_CURR_SWITCH_POS_CFG]["value"]
            == "true"
        )

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        await self.hub.turn_on(self.did)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        await self.hub.turn_off(self.did)
        await self.coordinator.async_request_refresh()

    async def async_toggle(self, **kwargs):
        """Toggle the entity."""
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()
        await self.coordinator.async_request_refresh()
