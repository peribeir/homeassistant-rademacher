"""Platform for Rademacher Bridge"""
import logging

from homeassistant.helpers.entity import EntityCategory
from .homepilot.hub import HomePilotHub

from homeassistant.const import CONF_DEVICES
from .homepilot.manager import HomePilotManager

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .homepilot.device import HomePilotDevice
from .entity import HomePilotEntity
from .homepilot.switch import HomePilotSwitch
from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    entry = hass.data[DOMAIN][config_entry.entry_id]
    manager: HomePilotManager = entry[0]
    coordinator: DataUpdateCoordinator = entry[1]
    devices: dict = (
        entry[2][CONF_DEVICES] if CONF_DEVICES in entry[2] else list(manager.devices)
    )
    new_entities = []
    for did in manager.devices:
        if did in devices:
            device: HomePilotDevice = manager.devices[did]
            if isinstance(device, HomePilotHub):
                _LOGGER.info("Found Led Switch for Device ID: %s", device.did)
                new_entities.append(HomePilotLedSwitchEntity(coordinator, device))
            if isinstance(device, HomePilotSwitch):
                _LOGGER.info("Found Switch for Device ID: %s", device.did)
                new_entities.append(HomePilotSwitchEntity(coordinator, device))
    # If we have any new devices, add them
    if new_entities:
        async_add_entities(new_entities)


class HomePilotSwitchEntity(HomePilotEntity, SwitchEntity):
    def __init__(
        self, coordinator: DataUpdateCoordinator, device: HomePilotDevice
    ) -> None:
        super().__init__(
            coordinator,
            device,
            unique_id=device.uid,
            name=device.name,
            device_class=SwitchDeviceClass.SWITCH.value,
        )

    @property
    def is_on(self):
        return self.coordinator.data[self.did].is_on

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        device: HomePilotSwitch = self.coordinator.data[self.did]
        await device.async_turn_on()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        device: HomePilotSwitch = self.coordinator.data[self.did]
        await device.async_turn_off()
        await self.coordinator.async_request_refresh()

    async def async_toggle(self, **kwargs):
        """Toggle the entity."""
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()
        await self.coordinator.async_request_refresh()


class HomePilotLedSwitchEntity(HomePilotEntity, SwitchEntity):
    def __init__(
        self, coordinator: DataUpdateCoordinator, device: HomePilotDevice
    ) -> None:
        super().__init__(
            coordinator,
            device,
            unique_id=f"{device.uid}_led_status",
            name=f"{device.name} LED Status",
            device_class=SwitchDeviceClass.SWITCH.value,
            entity_category=EntityCategory.CONFIG,
        )

    @property
    def is_on(self):
        device: HomePilotHub = self.coordinator.data[self.did]
        return device.led_status

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        device: HomePilotHub = self.coordinator.data[self.did]
        await device.async_turn_led_on()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        device: HomePilotHub = self.coordinator.data[self.did]
        await device.async_turn_led_off()
        await self.coordinator.async_request_refresh()

    async def async_toggle(self, **kwargs):
        """Toggle the entity."""
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()
        await self.coordinator.async_request_refresh()
