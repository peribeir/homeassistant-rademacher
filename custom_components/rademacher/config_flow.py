"""Config flow for Rademacher integration."""
import logging
import socket
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.device_registry import format_mac
import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries, exceptions, data_entry_flow
from homeassistant.components.dhcp import IP_ADDRESS, HOSTNAME, MAC_ADDRESS
from homeassistant.const import (
    CONF_DEVICES,
    CONF_EXCLUDE,
    CONF_HOST,
    CONF_PASSWORD,
    CONF_SENSOR_TYPE,
    CONF_API_VERSION
)

from homepilot.manager import HomePilotManager
from homepilot.api import CannotConnect, AuthError, HomePilotApi
from homepilot.sensor import HomePilotSensor

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({vol.Required(CONF_HOST): str})
DATA_SCHEMA_PASSWORD = vol.Schema({vol.Required(CONF_PASSWORD): str})


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 2
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL
    host: str = ""
    password: str = ""
    api_version: int = 1
    mac_address: str = ""
    hostname: str = ""
    reauth_entry: ConfigEntry | None = None
    exclude_devices: list[str] = []
    ternary_contact_sensors: list[str] = []

    async def async_step_config(self, user_input=None):
        errors = {}
        if user_input is not None and CONF_EXCLUDE in user_input:
            try:
                self.exclude_devices = user_input[CONF_EXCLUDE]
                self.ternary_contact_sensors = (
                    user_input[CONF_SENSOR_TYPE]
                    if CONF_SENSOR_TYPE in user_input
                    else []
                )
                data = {
                    CONF_HOST: self.host,
                    CONF_PASSWORD: self.password,
                    CONF_API_VERSION: self.api_version
                }
                options = {
                    CONF_EXCLUDE: self.exclude_devices,
                    CONF_SENSOR_TYPE: self.ternary_contact_sensors,
                }
                return self.async_create_entry(
                    title=f"{self.hostname} ({self.mac_address})", data=data, options=options
                )
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception", exc_info=True)
                errors["base"] = "unknown"
        api = HomePilotApi(
            self.host, self.password, self.api_version
        )  # password can be empty if not defined ("")
        manager = await HomePilotManager.async_build_manager(api)
        self.hostname = await manager.get_nodename()
        if not self.mac_address:
            self.mac_address = format_mac(await manager.get_hub_macaddress())
            await self.async_set_unique_id(self.mac_address)
            self._abort_if_unique_id_configured(updates={CONF_HOST: self.host})

        if not manager.devices:
            return self.async_abort(reason="no_devices_found")
        data_schema_config = self.build_data_schema(manager.devices)
        # If there is no user input or there were errors, show the form again, including any errors that were found
        # with the input.
        return self.async_show_form(
            step_id="config",
            data_schema=data_schema_config,
            errors=errors,
        )

    async def async_step_reauth(self, user_input=None):
        self.reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        self.host=self.reauth_entry.data[CONF_HOST]
        self.password=self.reauth_entry.data[CONF_PASSWORD]
        errors={}

        try:
            conn_test = await HomePilotApi.test_connection(user_input[CONF_HOST])
            if conn_test == "ok":
                data = {
                    CONF_HOST: self.host,
                    CONF_PASSWORD: "",
                    CONF_API_VERSION: 1
                }
                self.hass.config_entries.async_update_entry(self.reauth_entry, data=data)
                await self.hass.config_entries.async_reload(self.reauth_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

            await HomePilotApi.test_auth(self.host, self.password, self.api_version)
            return self.async_abort(reason="reauth_successful")
        except CannotConnect:
            _LOGGER.warning("Connect error (IP %s)", self.host)
            errors["base"] = "cannot_connect"
        except InvalidHost:
            _LOGGER.warning("Invalid Host (IP %s)", self.host)
            errors["base"] = "cannot_connect"
        except AuthError:
            _LOGGER.warning("Wrong Password (IP %s)", self.host)
            errors["base"] = "auth_error"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception", exc_info=True)
            errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user_password", data_schema=DATA_SCHEMA_PASSWORD, errors=errors
        )

    async def async_step_user_password(self, user_input=None):
        errors = {}
        if user_input is not None and CONF_PASSWORD in user_input:
            try:
                self.password = user_input[CONF_PASSWORD]
                await HomePilotApi.test_auth(self.host, self.password, self.api_version)
                _LOGGER.info(
                    "Password correct (IP %s), creating entries",
                    self.host,
                )
                if self.reauth_entry:
                    data = {
                        CONF_HOST: self.host,
                        CONF_PASSWORD: self.password,
                        CONF_API_VERSION: self.api_version
                    }
                    self.hass.config_entries.async_update_entry(self.reauth_entry, data=data)
                    await self.hass.config_entries.async_reload(self.reauth_entry.entry_id)
                    return self.async_abort(reason="reauth_successful")
                return await self.async_step_config(user_input=user_input)
            except CannotConnect:
                _LOGGER.warning("Connect error (IP %s)", self.host)
                errors["base"] = "cannot_connect"
            except InvalidHost:
                _LOGGER.warning("Invalid Host (IP %s)", self.host)
                errors["base"] = "cannot_connect"
            except AuthError:
                _LOGGER.warning("Wrong Password (IP %s)", self.host)
                errors["base"] = "auth_error"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception", exc_info=True)
                errors["base"] = "unknown"

            # If there is no user input or there were errors, show the form again, including any errors that were found
            # with the input.
        return self.async_show_form(
            step_id="user_password", data_schema=DATA_SCHEMA_PASSWORD, errors=errors
        )

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        # This goes through the steps to take the user through the setup process.
        # Using this it is possible to update the UI and prompt for additional
        # information. This example provides a single form (built from `DATA_SCHEMA`),
        # and when that has some validated input, it calls `async_create_entry` to
        # actually create the HA config entry. Note the "title" value is returned by
        # `validate_input` above.
        errors = {}
        if user_input is not None:
            try:
                self.host = socket.gethostbyname(user_input[CONF_HOST])
                _LOGGER.info("Starting manual config for IP %s", self.host)
                conn_test = await HomePilotApi.test_connection(user_input[CONF_HOST])
                if conn_test == "ok":
                    self.api_version = 1
                    _LOGGER.info(
                        "Connection Test Successful (IP %s), no Password required",
                        self.host,
                    )
                    return await self.async_step_config(user_input=user_input)
                if conn_test == "ok_v2":
                    self.api_version = 2
                    _LOGGER.info(
                        "Connection Test Successful (IP %s) with New Homepilot, no Password required",
                        self.host,
                    )
                    return await self.async_step_config(user_input=user_input)
                if conn_test == "auth_required":
                    self.api_version = 1
                    _LOGGER.info(
                        "Connection Test Successful (IP %s), Password needed",
                        self.host,
                    )
                    return await self.async_step_user_password(user_input=user_input)
                if conn_test == "auth_required_v2":
                    self.api_version = 2
                    _LOGGER.info(
                        "Connection Test Successful (IP %s) with New Homepilot, Password needed",
                        self.host,
                    )
                    return await self.async_step_user_password(user_input=user_input)

                _LOGGER.warning("Connection Test not Successful (IP %s)", self.host)
                errors["base"] = "cannot_connect"
            except (CannotConnect, InvalidHost, socket.gaierror):
                _LOGGER.warning("Connect error (IP %s)", self.host)
                errors["base"] = "cannot_connect"
            except AuthError:
                _LOGGER.warning("Auth (IP %s)", self.host)
                errors["base"] = "auth_error"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # If there is no user input or there were errors, show the form again, including any errors that were found
        # with the input.
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    async def async_step_confirm_discovery(
        self, user_input=None
    ) -> data_entry_flow.FlowResult:
        """Handle discovery confirm."""
        errors: dict[str, str] = {}

        if user_input is not None:
            _LOGGER.info(
                "User confirmed integration (IP %s), creating entries", self.host
            )
            return self.async_create_entry(
                title=f"{self.hostname} ({self.mac_address})", data={CONF_HOST: self.host, CONF_API_VERSION: self.api_version}
            )

        self._set_confirm_only()

        _LOGGER.info("Waiting for user confirmation (IP %s)", self.host)
        return self.async_show_form(
            step_id="confirm_discovery",
            description_placeholders={"host": self.host},
            errors=errors,
        )

    async def async_step_dhcp(self, discovery_info) -> data_entry_flow.FlowResult:
        self.host = (
            discovery_info.ip
            if hasattr(discovery_info, "ip")
            else discovery_info[IP_ADDRESS]
        )
        self.hostname = (
            discovery_info.hostname
            if hasattr(discovery_info, "hostname")
            else discovery_info[HOSTNAME]
        )
        self.mac_address = format_mac(
            discovery_info.macaddress
            if hasattr(discovery_info, "macaddress")
            else discovery_info[MAC_ADDRESS]
        )
        _LOGGER.info("Starting DHCP Discovery with IP Address %s", self.host)

        await self.async_set_unique_id(self.mac_address)
        self._abort_if_unique_id_configured(updates={CONF_HOST: self.host})

        conn_test = await HomePilotApi.test_connection(self.host)
        if conn_test == "ok":
            self.api_version = 1
            _LOGGER.info(
                "Connection Test Successful (IP %s), no Password required", self.host
            )
            return await self.async_step_config()
        if conn_test == "ok_v2":
            self.api_version = 2
            _LOGGER.info(
                "Connection Test Successful (IP %s) with New Homepilot, no Password required", self.host
            )
            return await self.async_step_config()
        if conn_test == "auth_required":
            self.api_version = 1
            _LOGGER.info(
                "Connection Test Successful (IP %s), Password needed", self.host
            )
            return await self.async_step_user_password()
        if conn_test == "auth_required_v2":
            self.api_version = 2
            _LOGGER.info(
                "Connection Test Successful (IP %s) with New Homepilot, Password needed", self.host
            )
            return await self.async_step_user_password()
        _LOGGER.warning("Connection Test not Successful (IP %s)", self.host)
        return self.async_abort(reason="cannot_connect")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)

    def build_data_schema(self, devices):
        devices_to_exclude = {
            did: f"{devices[did].name} (id: {devices[did].did})" for did in devices
        }
        contact_sensors = {
            did: f"{devices[did].name} (id: {devices[did].did})"
            for did in devices
            if isinstance(devices[did], HomePilotSensor)
            and devices[did].has_contact_state
        }
        schema = vol.Schema({})
        schema = schema.extend(
            {
                vol.Optional(CONF_EXCLUDE, default=[]): cv.multi_select(
                    devices_to_exclude
                ),
            }
        )
        if contact_sensors:
            schema = schema.extend(
                {
                    vol.Optional(CONF_SENSOR_TYPE, default=[]): cv.multi_select(
                        contact_sensors
                    )
                }
            )
        return schema


class OptionsFlowHandler(config_entries.OptionsFlow):
    host: str
    password: str

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            data = {
                CONF_EXCLUDE: user_input[CONF_EXCLUDE],
                CONF_SENSOR_TYPE: user_input[CONF_SENSOR_TYPE]
                if CONF_SENSOR_TYPE in user_input
                else [],
            }
            return self.async_create_entry(title=f"{self.hostname} ({self.mac_address})", data=data)
        self.host = self.config_entry.data[CONF_HOST]
        self.password = (
            self.config_entry.data[CONF_PASSWORD]
            if CONF_PASSWORD in self.config_entry.data
            else ""
        )
        self.api_version = (
            self.config_entry.data[CONF_API_VERSION]
            if CONF_API_VERSION in self.config_entry.data
            else 1
        )
        api = HomePilotApi(
            self.host, self.password, self.api_version
        )  # password can be empty if not defined ("")
        manager = await HomePilotManager.async_build_manager(api)
        self.mac_address = format_mac(await manager.get_hub_macaddress())
        self.hostname = await manager.get_nodename()
        if not manager.devices:
            return self.async_abort(reason="no_devices_found")

        if CONF_EXCLUDE in self.config_entry.options:
            previous_excluded_devices = self.config_entry.options[CONF_EXCLUDE]
        elif CONF_DEVICES in self.config_entry.options:
            previous_excluded_devices = [
                did
                for did in manager.devices
                if did not in self.config_entry.options[CONF_DEVICES]
            ]
        else:
            previous_excluded_devices = []
        if CONF_SENSOR_TYPE in self.config_entry.options:
            previous_ternary_contact_sensors = self.config_entry.options[
                CONF_SENSOR_TYPE
            ]
        else:
            previous_ternary_contact_sensors = []

        data_schema_config = self.build_data_schema(
            manager.devices, previous_excluded_devices, previous_ternary_contact_sensors
        )

        return self.async_show_form(step_id="init", data_schema=data_schema_config)

    def build_data_schema(
        self, devices, previous_excluded_devices, previous_ternary_contact_sensors
    ):
        devices_to_exclude = {
            did: f"{devices[did].name} (id: {devices[did].did})" for did in devices
        }
        contact_sensors = {
            did: f"{devices[did].name} (id: {devices[did].did})"
            for did in devices
            if isinstance(devices[did], HomePilotSensor)
            and devices[did].has_contact_state
        }
        schema = vol.Schema({})
        schema = schema.extend(
            {
                vol.Optional(
                    CONF_EXCLUDE, default=list(previous_excluded_devices)
                ): cv.multi_select(devices_to_exclude),
            }
        )
        if contact_sensors:
            schema = schema.extend(
                {
                    vol.Optional(
                        CONF_SENSOR_TYPE, default=list(previous_ternary_contact_sensors)
                    ): cv.multi_select(contact_sensors)
                }
            )
        return schema


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""
