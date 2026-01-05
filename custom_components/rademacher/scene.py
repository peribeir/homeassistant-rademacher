"""Platform for Rademacher Bridge."""
import asyncio
import logging
from typing import Any

from homepilot.manager import HomePilotManager
from homepilot.scenes import HomePilotScene

from homeassistant.components.scene import Scene
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup of entities for scene platform."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    manager: HomePilotManager = entry[0]
    scene_coordinator: DataUpdateCoordinator = entry[4]  # Scene coordinator is at index 4

    new_entities = []
    for sid in manager.scenes:
        scene: HomePilotScene = manager.scenes[sid]
        _LOGGER.info("Found Scene for ID: %s", sid)
        new_entities.append(HomePilotSceneEntity(scene_coordinator, scene))
    # If we have any new devices, add them
    if new_entities:
        async_add_entities(new_entities)



class HomePilotSceneEntity(CoordinatorEntity, Scene):
    """This class represents a Rademacher HomePilot Scene."""

    def __init__(
        self, coordinator: DataUpdateCoordinator, scene: HomePilotScene
    ) -> None:
        # Initialize both parent classes
        CoordinatorEntity.__init__(self, coordinator)
        Scene.__init__(self)

        self._sid = scene.sid
        # Use hub MAC + scene sid for globally unique ID, similar to device entities
        hub_mac = coordinator.config_entry.unique_id or "unknown"
        self._attr_unique_id = f"{hub_mac}_scene_{scene.sid}"
        self._attr_name = f"Homepilot - {scene.name}"

    @property
    def device_info(self):
        """Information about the bridge device that scenes belong to."""
        # Get the bridge/hub identifier from config entry
        hub_mac = self.coordinator.config_entry.unique_id or "unknown"
        bridge_name = self.coordinator.config_entry.title or "Rademacher HomePilot"

        # Group scenes under the HomePilot bridge device
        return {
            "identifiers": {(DOMAIN, f"{hub_mac}_bridge")},
            "name": f"{bridge_name} Scenes",
            "manufacturer": "Rademacher",
            "model": "HomePilot Bridge",
        }

    @property
    def sid(self):
        return self._sid

    @property
    def available(self):
        try:
            scene: HomePilotScene = self.coordinator.data[self._sid]
            return scene.available
        except (KeyError, AttributeError):
            return False

    @property
    def is_enabled(self):
        scene: HomePilotScene = self.coordinator.data[self._sid]
        return scene.is_enabled

    @property
    def is_manual_executable(self):
        scene: HomePilotScene = self.coordinator.data[self._sid]
        return scene.is_manual_executable

    @property
    def icon(self):
        """Return icon based on whether scene is manually executable."""
        scene: HomePilotScene = self.coordinator.data[self._sid]
        if scene.is_manual_executable:
            return "mdi:palette"  # Executable scene - palette icon
        else:
            return "mdi:palette-outline"  # Non-executable scene - outlined palette icon

    @property
    def extra_state_attributes(self):
        scene: HomePilotScene = self.coordinator.data[self._sid]
        return {
            "scene_id": self._sid,
            "is_enabled": scene.is_enabled,
            "is_manual_executable": scene.is_manual_executable,
            "description": scene.description,
        }

    async def async_activate(self, **kwargs: Any) -> None:
        """Activate scene. Try to get entities into requested state."""
        # Follow same pattern as other entities: get current data and execute action
        scene: HomePilotScene = self.coordinator.data[self._sid]

        # Check if scene is manually executable
        if not scene.is_manual_executable:
            _LOGGER.warning("Scene %s (%s) is not manually executable", scene.name, self._sid)
            return

        await scene.async_execute_scene()
        # Request coordinator refresh after scene execution (like other entities)
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()