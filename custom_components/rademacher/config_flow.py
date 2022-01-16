"""Config flow for Rademacher integration."""
import logging
import socket

import voluptuous as vol

from homeassistant import config_entries, exceptions, data_entry_flow
from homeassistant.components.dhcp import IP_ADDRESS
from homeassistant.const import CONF_BINARY_SENSORS, CONF_HOST, CONF_PASSWORD
from homeassistant.core import callback

from .homepilot.api import CannotConnect, AuthError, HomePilotApi
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({vol.Required(CONF_HOST): str})
DATA_SCHEMA_PASSWORD = vol.Schema({vol.Required(CONF_PASSWORD): str})
DATA_SCHEMA_CONFIG = vol.Schema({vol.Optional(CONF_BINARY_SENSORS, default=True): bool})


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL
    host: str = ""
    password: str = ""
    binary_sensors: bool = True

    async def async_step_config(self, user_input=None):
        errors = {}
        if user_input is not None and CONF_BINARY_SENSORS in user_input:
            try:
                self.binary_sensors = user_input[CONF_BINARY_SENSORS]
                data = {
                    CONF_HOST: self.host,
                    CONF_PASSWORD: self.password,
                    CONF_BINARY_SENSORS: self.binary_sensors,
                }
                return self.async_create_entry(title=f"Host: {self.host}", data=data)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception", exc_info=True)
                errors["base"] = "unknown"

            # If there is no user input or there were errors, show the form again, including any errors that were found
            # with the input.
        return self.async_show_form(
            step_id="config", data_schema=DATA_SCHEMA_CONFIG, errors=errors
        )

    async def async_step_user_password(self, user_input=None):
        errors = {}
        if user_input is not None and CONF_PASSWORD in user_input:
            try:
                self.password = user_input[CONF_PASSWORD]
                await HomePilotApi.test_auth(self.host, self.password)
                _LOGGER.info(
                    "Password correct (IP %s), creating entries",
                    self.host,
                )
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
                await self.async_set_unique_id(self.host)
                self._abort_if_unique_id_configured()
                conn_test = await HomePilotApi.test_connection(user_input[CONF_HOST])
                if conn_test == "ok":
                    _LOGGER.info(
                        "Connection Test Successful (IP %s), no Password required",
                        self.host,
                    )
                    return await self.async_step_config(user_input=user_input)
                if conn_test == "auth_required":
                    _LOGGER.info(
                        "Connection Test Successful (IP %s), Password needed",
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
                title=f"Host: {self.host}", data={CONF_HOST: self.host}
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
        _LOGGER.info("Starting DHCP Discovery with IP Address %s", self.host)
        await self.async_set_unique_id(self.host)
        self._abort_if_unique_id_configured()
        conn_test = await HomePilotApi.test_connection(self.host)
        if conn_test == "ok":
            _LOGGER.info(
                "Connection Test Successful (IP %s), no Password required", self.host
            )
            return await self.async_step_confirm_discovery()
        if conn_test == "auth_required":
            _LOGGER.info(
                "Connection Test Successful (IP %s), Password needed", self.host
            )
            return await self.async_step_user_password()
        _LOGGER.warning("Connection Test not Successful (IP %s)", self.host)
        return self.async_abort(reason="Cannot connect")


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""
