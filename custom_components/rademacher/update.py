"""Platform for Rademacher Bridge"""
import asyncio
import logging
from typing import Any

from homeassistant.const import CONF_EXCLUDE
from homeassistant.components.update import UpdateDeviceClass, UpdateEntityFeature, UpdateEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from homepilot.manager import HomePilotManager
from homepilot.device import HomePilotDevice
from homepilot.hub import HomePilotHub

from .const import DOMAIN
from .entity import HomePilotEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup of entities for switch platform"""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    manager: HomePilotManager = entry[0]
    coordinator: DataUpdateCoordinator = entry[1]
    exclude_devices: list[str] = entry[3][CONF_EXCLUDE]
    new_entities = []
    for did in manager.devices:
        if did not in exclude_devices:
            device: HomePilotDevice = manager.devices[did]
            if isinstance(device, HomePilotHub):
                _LOGGER.info("Found FW Update Sensor for Device ID: %s", device.did)
                new_entities.append(
                    HomePilotUpdateEntity(
                        coordinator=coordinator,
                        device=device,
                        id_suffix="fw_update",
                        name_suffix="Firmware Update",
                        device_class=UpdateDeviceClass.FIRMWARE,
                        supported_features=(UpdateEntityFeature.INSTALL | UpdateEntityFeature.PROGRESS)
                    )
                )
    # If we have any new devices, add them
    if new_entities:
        async_add_entities(new_entities)


class HomePilotUpdateEntity(HomePilotEntity, UpdateEntity):
    """This class represents all Switches supported"""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device: HomePilotDevice,
        id_suffix,
        name_suffix,
        device_class,
        supported_features
    ) -> None:
        super().__init__(
            coordinator,
            device,
            unique_id=f"{device.uid}_{id_suffix}",
            name=f"{device.name} {name_suffix}",
            device_class=device_class,
        )
        self._attr_supported_features = supported_features

    @property
    def in_progress(self):
        return self.coordinator.data[self.did].download_progress

    @property
    def auto_update(self):
        return self.coordinator.data[self.did].auto_update

    @property
    def installed_version(self):
        return self.coordinator.data[self.did].fw_version

    @property
    def latest_version(self):
        return self.coordinator.data[self.did].fw_update_version

    @property
    def release_url(self):
        return self.coordinator.data[self.did].release_notes

    @property
    def title(self):
        return self.coordinator.data[self.did].sw_platform

    async def async_install(self, version: str | None, backup: bool, **kwargs: Any):
        """Install update."""
        device: HomePilotHub = self.coordinator.data[self.did]
        _LOGGER.info(f"Install update v:{version} b:{backup}")
        await device.async_update_firmware()
