"""Config flow for Rademacher integration."""
import logging
import socket

import voluptuous as vol

from homeassistant import config_entries, core, exceptions, data_entry_flow
from homeassistant.components.dhcp import IP_ADDRESS
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.helpers.typing import DiscoveryInfoType

from .hub import Hub, CannotConnect, AuthError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({vol.Required(CONF_HOST): str})
DATA_SCHEMA_PASSWORD = vol.Schema({vol.Required(CONF_PASSWORD): str})


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL
    host = ''

    async def async_step_user_password(self, user_input=None):
        errors = {}
        if user_input is not None and CONF_PASSWORD in user_input:
            try:
                await Hub.test_auth(self.host, user_input[CONF_PASSWORD])
                data = {CONF_HOST: self.host, CONF_PASSWORD: user_input[CONF_PASSWORD]}
                return self.async_create_entry(title=f"Host: {self.host}", data=data)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidHost:
                errors["base"] = "cannot_connect"
            except AuthError:
                errors["base"] = "auth_error"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
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
                ip_address = socket.gethostbyname(user_input[CONF_HOST])
                await self.async_set_unique_id(ip_address)
                self._abort_if_unique_id_configured()
                conn_test = await Hub.test_connection(user_input[CONF_HOST])
                if conn_test == 'ok':
                    return self.async_create_entry(title=f"Host: {user_input[CONF_HOST]}", data=user_input)
                elif conn_test == 'auth_required':
                    self.host = user_input[CONF_HOST]
                    return await self.async_step_user_password(user_input=user_input)
                else:
                    errors["base"] = "cannot_connect"
            except (CannotConnect, InvalidHost, socket.gaierror):
                errors["base"] = "cannot_connect"
            except AuthError:
                errors["base"] = "auth_error"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # If there is no user input or there were errors, show the form again, including any errors that were found
        # with the input.
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    async def async_step_dhcp(
        self, discovery_info: DiscoveryInfoType
    ) -> data_entry_flow.FlowResult:
        await self.async_set_unique_id(discovery_info[IP_ADDRESS])
        self._abort_if_unique_id_configured()
        conn_test = await Hub.test_connection(discovery_info[IP_ADDRESS])
        if conn_test == 'ok':
            data={CONF_HOST:discovery_info[IP_ADDRESS]}
            return self.async_create_entry(title=f"Host: {discovery_info[IP_ADDRESS]}", data=data)
        elif conn_test == 'auth_required':
            self.host = discovery_info[IP_ADDRESS]
            return await self.async_step_user_password()
        else:
            return self.async_abort(reason="Cannot connect")


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""
