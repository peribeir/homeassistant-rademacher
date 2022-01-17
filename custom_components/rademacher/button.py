"""Platform for Rademacher Bridge"""
import logging
from homeassistant.const import CONF_DEVICES
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .homepilot.device import HomePilotDevice
from .homepilot.hub import HomePilotHub
from .entity import HomePilotEntity
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    entry = hass.data[DOMAIN][config_entry.entry_id]
    hub: HomePilotHub = entry[0]
    coordinator: DataUpdateCoordinator = entry[1]
    devices: bool = entry[2][CONF_DEVICES]
    new_entities = []
    for did in hub.devices:
        if did in devices:
            device: HomePilotDevice = hub.devices[did]
            if device.has_ping_cmd:
                _LOGGER.info("Found Ping Command Button for Device ID: %s", device.did)
                new_entities.append(HomePilotPingButtonEntity(coordinator, device))
    # If we have any new devices, add them
    if new_entities:
        async_add_entities(new_entities)


class HomePilotPingButtonEntity(HomePilotEntity, ButtonEntity):
    def __init__(
        self, coordinator: DataUpdateCoordinator, device: HomePilotDevice
    ) -> None:
        super().__init__(
            coordinator,
            device,
            unique_id=f"{device.uid}_ping",
            name=f"{device.name} Ping",
        )

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC

    @property
    def entity_registry_enabled_default(self):
        return False

    async def async_press(self) -> None:
        device: HomePilotDevice = self.coordinator.data[self.did]
        await device.async_ping()
        await self.coordinator.async_request_refresh()
