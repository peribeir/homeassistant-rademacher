"""Platform for Rademacher Bridge."""
import logging
from typing import Any

from homepilot.manager import HomePilotManager
from homepilot.scenes import HomePilotScene

from homeassistant.components.scene import Scene

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup of entities for switch platform."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    manager: HomePilotManager = entry[0]
    new_entities = []
    for sid in manager.scenes:
        scene: HomePilotScene = manager.scenes[sid]
        _LOGGER.info("Found Scene for ID: %s", sid)
        new_entities.append(HomePilotSceneEntity(sid, scene))
    # If we have any new devices, add them
    if new_entities:
        async_add_entities(new_entities)


class HomePilotSceneEntity(Scene):
    """This class represents Cover Ventilation Position."""
    _sid: str
    _scene: HomePilotScene

    def __init__(
        self, sid: str, scene: HomePilotScene
    ) -> None:
        self._sid = sid
        self._scene = scene
        self._attr_unique_id = f"scene_{sid}"
        self._attr_name = f"Homepilot - {scene.name}"

    @property
    def available(self):
        return True

    async def async_activate(self, **kwargs: Any) -> None:
        """Activate scene. Try to get entities into requested state."""
        await self._scene.async_execute_scene()