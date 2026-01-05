"""Platform for Rademacher Bridge."""
import asyncio
import logging

from homepilot.cover import HomePilotCover
from homepilot.thermostat import HomePilotThermostat
from homepilot.device import HomePilotDevice, HomePilotAutoConfigDevice
from homepilot.hub import HomePilotHub
from homepilot.manager import HomePilotManager
from homepilot.switch import HomePilotSwitch
from homepilot.scenes import HomePilotScene
from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.const import CONF_EXCLUDE
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity

from .const import CONF_CREATE_SCENE_ACTIVATION_ENTITIES, DOMAIN
from .entity import HomePilotEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup of entities for switch platform."""
    entry = hass.data[DOMAIN][config_entry.entry_id]
    manager: HomePilotManager = entry[0]
    coordinator: DataUpdateCoordinator = entry[1]
    exclude_devices: list[str] = entry[3][CONF_EXCLUDE]
    new_entities = []
    for did in manager.devices:
        if did not in exclude_devices:
            device: HomePilotDevice = manager.devices[did]
            if isinstance(device, HomePilotHub):
                _LOGGER.info("Found Led Switch for Device ID: %s", device.did)
                new_entities.append(HomePilotLedSwitchEntity(coordinator, device))
                new_entities.append(HomePilotAutoUpdaeSwitchEntity(coordinator, device))
            if isinstance(device, HomePilotSwitch):
                _LOGGER.info("Found Switch for Device ID: %s", device.did)
                new_entities.append(HomePilotSwitchEntity(coordinator, device))
            if isinstance(device, HomePilotCover):
                cover: HomePilotCover = device
                if cover.has_ventilation_position_config:
                    _LOGGER.info("Found Ventilation Position Config Switch for Device ID: %s", device.did)
                    new_entities.append(HomePilotVentilationSwitchEntity(coordinator, device))
            if isinstance(device, HomePilotAutoConfigDevice):
                auto_device: HomePilotAutoConfigDevice = device
                if auto_device.has_auto_mode and not isinstance(auto_device, HomePilotThermostat):
                    _LOGGER.info("Found Auto Mode Config Switch for Device ID: %s", device.did)
                    new_entities.append(HomePilotAutoModeEntity(coordinator, device))
                if auto_device.has_time_auto_mode:
                    _LOGGER.info("Found Time Auto Mode Config Switch for Device ID: %s", device.did)
                    new_entities.append(HomePilotTimeAutoModeEntity(coordinator, device))
                if auto_device.has_contact_auto_mode:
                    _LOGGER.info("Found Contact Auto Mode Config Switch for Device ID: %s", device.did)
                    new_entities.append(HomePilotContactAutoModeEntity(coordinator, device))
                if auto_device.has_wind_auto_mode:
                    _LOGGER.info("Found Wind Auto Mode Config Switch for Device ID: %s", device.did)
                    new_entities.append(HomePilotWindAutoModeEntity(coordinator, device))
                if auto_device.has_dusk_auto_mode:
                    _LOGGER.info("Found Dusk Auto Mode Config Switch for Device ID: %s", device.did)
                    new_entities.append(HomePilotDuskAutoModeEntity(coordinator, device))
                if auto_device.has_dawn_auto_mode:
                    _LOGGER.info("Found Dawn Auto Mode Config Switch for Device ID: %s", device.did)
                    new_entities.append(HomePilotDawnAutoModeEntity(coordinator, device))
                if auto_device.has_rain_auto_mode:
                    _LOGGER.info("Found Rain Auto Mode Config Switch for Device ID: %s", device.did)
                    new_entities.append(HomePilotRainAutoModeEntity(coordinator, device))
                if auto_device.has_sun_auto_mode:
                    _LOGGER.info("Found Sun Auto Mode Config Switch for Device ID: %s", device.did)
                    new_entities.append(HomePilotSunAutoModeEntity(coordinator, device))
    create_scene_activation_entities = entry[3].get(CONF_CREATE_SCENE_ACTIVATION_ENTITIES, False)
    if create_scene_activation_entities:
        for sid in manager.scenes:
            scene: HomePilotScene = manager.scenes[sid]
            _LOGGER.info("Found Scene Switch for Scene ID: %s", sid)
            new_entities.append(HomePilotRademacherSceneEnabledEntity(entry[4], scene))
    if new_entities:
        async_add_entities(new_entities)


class HomePilotSwitchEntity(HomePilotEntity, SwitchEntity):
    """This class represents all Switches supported."""

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
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        device: HomePilotSwitch = self.coordinator.data[self.did]
        await device.async_turn_off()
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_toggle(self, **kwargs):
        """Toggle the entity."""
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()


class HomePilotLedSwitchEntity(HomePilotEntity, SwitchEntity):
    """This class represents the Led Switch which controls the LEDs on the hub."""

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
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        device: HomePilotHub = self.coordinator.data[self.did]
        await device.async_turn_led_off()
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_toggle(self, **kwargs):
        """Toggle the entity."""
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()

class HomePilotAutoUpdaeSwitchEntity(HomePilotEntity, SwitchEntity):
    """This class represents the Led Switch which controls the LEDs on the hub."""

    def __init__(
        self, coordinator: DataUpdateCoordinator, device: HomePilotDevice
    ) -> None:
        super().__init__(
            coordinator,
            device,
            unique_id=f"{device.uid}_auto_update",
            name=f"{device.name} Auto Update",
            device_class=SwitchDeviceClass.SWITCH.value,
            entity_category=EntityCategory.CONFIG,
        )

    @property
    def is_on(self):
        device: HomePilotHub = self.coordinator.data[self.did]
        return device.auto_update

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        device: HomePilotHub = self.coordinator.data[self.did]
        await device.async_set_auto_update_on()
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        device: HomePilotHub = self.coordinator.data[self.did]
        await device.async_set_auto_update_off()
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_toggle(self, **kwargs):
        """Toggle the entity."""
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()

class HomePilotVentilationSwitchEntity(HomePilotEntity, SwitchEntity):
    """This class represents the Switch which controls Ventilation Position Mode."""

    def __init__(
        self, coordinator: DataUpdateCoordinator, device: HomePilotDevice
    ) -> None:
        super().__init__(
            coordinator,
            device,
            unique_id=f"{device.uid}_ventilation_position_mode",
            name=f"{device.name} Ventilation Position Mode",
            device_class=SwitchDeviceClass.SWITCH.value,
            entity_category=EntityCategory.CONFIG,
        )

    @property
    def is_on(self):
        device: HomePilotCover = self.coordinator.data[self.did]
        return device.ventilation_position_mode

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        device: HomePilotCover = self.coordinator.data[self.did]
        await device.async_set_ventilation_position_mode(True)
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        device: HomePilotCover = self.coordinator.data[self.did]
        await device.async_set_ventilation_position_mode(False)
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_toggle(self, **kwargs):
        """Toggle the entity."""
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()

class HomePilotAutoModeEntity(HomePilotEntity, SwitchEntity):
    """This class represents the Switch which controls Auto Mode."""

    def __init__(
        self, coordinator: DataUpdateCoordinator, device: HomePilotDevice
    ) -> None:
        super().__init__(
            coordinator,
            device,
            unique_id=f"{device.uid}_auto_mode",
            name=f"{device.name} Auto Mode",
            device_class=SwitchDeviceClass.SWITCH.value,
            entity_category=EntityCategory.CONFIG,
        )

    @property
    def is_on(self):
        device: HomePilotAutoConfigDevice = self.coordinator.data[self.did]
        return device.auto_mode_value

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        device: HomePilotAutoConfigDevice = self.coordinator.data[self.did]
        await device.async_set_auto_mode(True)
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        device: HomePilotAutoConfigDevice = self.coordinator.data[self.did]
        await device.async_set_auto_mode(False)
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_toggle(self, **kwargs):
        """Toggle the entity."""
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()

class HomePilotTimeAutoModeEntity(HomePilotEntity, SwitchEntity):
    """This class represents the Switch which controls Time Auto Mode."""

    def __init__(
        self, coordinator: DataUpdateCoordinator, device: HomePilotDevice
    ) -> None:
        super().__init__(
            coordinator,
            device,
            unique_id=f"{device.uid}_time_auto_mode",
            name=f"{device.name} Time Auto Mode",
            device_class=SwitchDeviceClass.SWITCH.value,
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        )

    @property
    def is_on(self):
        device: HomePilotAutoConfigDevice = self.coordinator.data[self.did]
        return device.time_auto_mode_value

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        device: HomePilotAutoConfigDevice = self.coordinator.data[self.did]
        await device.async_set_time_auto_mode(True)
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        device: HomePilotAutoConfigDevice = self.coordinator.data[self.did]
        await device.async_set_time_auto_mode(False)
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_toggle(self, **kwargs):
        """Toggle the entity."""
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()

class HomePilotContactAutoModeEntity(HomePilotEntity, SwitchEntity):
    """This class represents the Switch which controls Contact Auto Mode."""

    def __init__(
        self, coordinator: DataUpdateCoordinator, device: HomePilotDevice
    ) -> None:
        super().__init__(
            coordinator,
            device,
            unique_id=f"{device.uid}_contact_auto_mode",
            name=f"{device.name} Contact Auto Mode",
            device_class=SwitchDeviceClass.SWITCH.value,
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        )

    @property
    def is_on(self):
        device: HomePilotAutoConfigDevice = self.coordinator.data[self.did]
        return device.contact_auto_mode_value

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        device: HomePilotAutoConfigDevice = self.coordinator.data[self.did]
        await device.async_set_contact_auto_mode(True)
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        device: HomePilotAutoConfigDevice = self.coordinator.data[self.did]
        await device.async_set_contact_auto_mode(False)
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_toggle(self, **kwargs):
        """Toggle the entity."""
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()

class HomePilotWindAutoModeEntity(HomePilotEntity, SwitchEntity):
    """This class represents the Switch which controls Wind Auto Mode."""

    def __init__(
        self, coordinator: DataUpdateCoordinator, device: HomePilotDevice
    ) -> None:
        super().__init__(
            coordinator,
            device,
            unique_id=f"{device.uid}_wind_auto_mode",
            name=f"{device.name} Wind Auto Mode",
            device_class=SwitchDeviceClass.SWITCH.value,
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        )

    @property
    def is_on(self):
        device: HomePilotAutoConfigDevice = self.coordinator.data[self.did]
        return device.wind_auto_mode_value

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        device: HomePilotAutoConfigDevice = self.coordinator.data[self.did]
        await device.async_set_wind_auto_mode(True)
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        device: HomePilotAutoConfigDevice = self.coordinator.data[self.did]
        await device.async_set_wind_auto_mode(False)
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_toggle(self, **kwargs):
        """Toggle the entity."""
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()

class HomePilotDawnAutoModeEntity(HomePilotEntity, SwitchEntity):
    """This class represents the Switch which controls Dawn Auto Mode."""

    def __init__(
        self, coordinator: DataUpdateCoordinator, device: HomePilotDevice
    ) -> None:
        super().__init__(
            coordinator,
            device,
            unique_id=f"{device.uid}_dawn_auto_mode",
            name=f"{device.name} Dawn Auto Mode",
            device_class=SwitchDeviceClass.SWITCH.value,
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        )

    @property
    def is_on(self):
        device: HomePilotAutoConfigDevice = self.coordinator.data[self.did]
        return device.dawn_auto_mode_value

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        device: HomePilotAutoConfigDevice = self.coordinator.data[self.did]
        await device.async_set_dawn_auto_mode(True)
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        device: HomePilotAutoConfigDevice = self.coordinator.data[self.did]
        await device.async_set_dawn_auto_mode(False)
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_toggle(self, **kwargs):
        """Toggle the entity."""
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()

class HomePilotDuskAutoModeEntity(HomePilotEntity, SwitchEntity):
    """This class represents the Switch which controls Dusk Auto Mode."""

    def __init__(
        self, coordinator: DataUpdateCoordinator, device: HomePilotDevice
    ) -> None:
        super().__init__(
            coordinator,
            device,
            unique_id=f"{device.uid}_dusk_auto_mode",
            name=f"{device.name} Dusk Auto Mode",
            device_class=SwitchDeviceClass.SWITCH.value,
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        )

    @property
    def is_on(self):
        device: HomePilotAutoConfigDevice = self.coordinator.data[self.did]
        return device.dusk_auto_mode_value

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        device: HomePilotAutoConfigDevice = self.coordinator.data[self.did]
        await device.async_set_dusk_auto_mode(True)
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        device: HomePilotAutoConfigDevice = self.coordinator.data[self.did]
        await device.async_set_dusk_auto_mode(False)
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_toggle(self, **kwargs):
        """Toggle the entity."""
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()

class HomePilotRainAutoModeEntity(HomePilotEntity, SwitchEntity):
    """This class represents the Switch which controls Rain Auto Mode."""

    def __init__(
        self, coordinator: DataUpdateCoordinator, device: HomePilotDevice
    ) -> None:
        super().__init__(
            coordinator,
            device,
            unique_id=f"{device.uid}_rain_auto_mode",
            name=f"{device.name} Rain Auto Mode",
            device_class=SwitchDeviceClass.SWITCH.value,
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        )

    @property
    def is_on(self):
        device: HomePilotAutoConfigDevice = self.coordinator.data[self.did]
        return device.rain_auto_mode_value

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        device: HomePilotAutoConfigDevice = self.coordinator.data[self.did]
        await device.async_set_rain_auto_mode(True)
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        device: HomePilotAutoConfigDevice = self.coordinator.data[self.did]
        await device.async_set_rain_auto_mode(False)
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_toggle(self, **kwargs):
        """Toggle the entity."""
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()

class HomePilotSunAutoModeEntity(HomePilotEntity, SwitchEntity):
    """This class represents the Switch which controls Sun Auto Mode."""

    def __init__(
        self, coordinator: DataUpdateCoordinator, device: HomePilotDevice
    ) -> None:
        super().__init__(
            coordinator,
            device,
            unique_id=f"{device.uid}_sun_auto_mode",
            name=f"{device.name} Sun Auto Mode",
            device_class=SwitchDeviceClass.SWITCH.value,
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        )

    @property
    def is_on(self):
        device: HomePilotAutoConfigDevice = self.coordinator.data[self.did]
        return device.sun_auto_mode_value

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        device: HomePilotAutoConfigDevice = self.coordinator.data[self.did]
        await device.async_set_sun_auto_mode(True)
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        device: HomePilotAutoConfigDevice = self.coordinator.data[self.did]
        await device.async_set_sun_auto_mode(False)
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_toggle(self, **kwargs):
        """Toggle the entity."""
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()

class HomePilotRademacherSceneEnabledEntity(CoordinatorEntity, SwitchEntity):
    """This class represents the Switch which controls the enableing of a rademacher scene."""
    _sid: int

    def __init__(
        self, coordinator: DataUpdateCoordinator, scene: HomePilotScene, entity_registry_enabled_default=False
    ) -> None:
        super().__init__(coordinator)
        self._sid = scene.sid
        hub_mac = coordinator.config_entry.unique_id or "unknown"
        self._unique_id = f"{hub_mac}_{scene.sid}_scene_enabled"
        self._name = f"{scene.name} Enabled"
        self._device_class = SwitchDeviceClass.SWITCH.value
        self._entity_category = EntityCategory.CONFIG
        self._entity_registry_enabled_default = entity_registry_enabled_default

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def entity_registry_enabled_default(self):
        return self._entity_registry_enabled_default

    @property
    def name(self):
        return self._name

    @property
    def device_name(self):
        return self._device_name

    @property
    def device_class(self):
        return self._device_class

    @property
    def entity_category(self):
        return self._entity_category

    @property
    def sid(self):
        return self._sid

    @property
    def is_on(self):
        return self.coordinator.data[self.sid].is_enabled

    @property
    def device_info(self):
        """Information about the bridge device that scenes activation belong to."""

        hub_mac = self.coordinator.config_entry.unique_id or "unknown"
        bridge_name = self.coordinator.config_entry.title or "Rademacher HomePilot"
        return {
            "identifiers": {(DOMAIN, f"{hub_mac}_bridge")},
            "name": f"{bridge_name} Scenes",
            "manufacturer": "Rademacher",
            "model": "HomePilot Bridge",
        }

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        scene: HomePilotScene = self.coordinator.data[self.sid]
        await scene.async_activate_scene()
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        scene: HomePilotScene = self.coordinator.data[self.sid]
        await scene.async_deactivate_scene()
        async with asyncio.timeout(5):
            await self.coordinator.async_request_refresh()

    async def async_toggle(self, **kwargs):
        """Toggle the entity."""
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()