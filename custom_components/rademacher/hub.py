import aiohttp
import hashlib
import logging
from aiohttp import ClientConnectorError
from aiohttp.abc import AbstractCookieJar
from homeassistant import exceptions


_LOGGER = logging.getLogger(__name__)


class Hub:
    def __init__(self, hass, host, password=''):
        self._hass = hass
        self._host = host
        self._password = password
        self._cookie_jar = aiohttp.CookieJar()
        self._authenticated = False

    @staticmethod
    async def test_auth(host: str, password: str) -> AbstractCookieJar:
        cookie_jar = aiohttp.CookieJar(unsafe=True)
        async with aiohttp.ClientSession(cookie_jar=cookie_jar) as session:
            response = await session.post(f"http://{host}/authentication/password_salt")
            response_data = await response.json()
            if response.status == 500 and response_data['error_code'] == 5007:
                raise AuthError()
            if response.status != 200 or response_data['error_code'] != 0:
                raise CannotConnect()
            salt = response_data['password_salt']
            hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
            salted_password = hashlib.sha256(f"{salt}{hashed_password}".encode('utf-8')).hexdigest()
            response = await session.post(
                f"http://{host}/authentication/login",
                json={"password": salted_password, "password_salt": salt}
            )
            if response.status != 200:
                raise AuthError()
            return session.cookie_jar

    @staticmethod
    async def test_connection(host: str) -> str:
        async with aiohttp.ClientSession() as session:
            try:
                response = await session.get(f"http://{host}/")
                if response.status != 200:
                    return 'error'
                response = await session.post(f"http://{host}/authentication/password_salt")
                if response.status == 500:
                    return 'ok'
                else:
                    return 'auth_required'
            except ClientConnectorError:
                return 'error'

    async def authenticate(self):
        if not self._authenticated and self._password != '':
            self._cookie_jar = await self.test_auth(self._host, self._password)
        return self._cookie_jar

    async def get_covers(self):
        await self.authenticate()
        async with aiohttp.ClientSession(cookie_jar=self._cookie_jar) as session:
            async with session.get(f"http://{self._host}/v4/devices?devtype=Actuator") as response:
                devices = await response.json()

                if devices['response'] == 'get_visible_devices':
                    return [cover for cover in devices['devices'] if cover['deviceGroup'] and cover['deviceGroup'] == 2]
                else:
                    return []

    async def open_cover(self, did):
        await self.authenticate()
        async with aiohttp.ClientSession(cookie_jar=self._cookie_jar) as session:
            async with session.put(f"http://{self._host}/devices/{did}", json={"name": "POS_UP_CMD"}) as response:
                await response.text()

    async def close_cover(self, did):
        await self.authenticate()
        async with aiohttp.ClientSession(cookie_jar=self._cookie_jar) as session:
            async with session.put(f"http://{self._host}/devices/{did}", json={"name": "POS_DOWN_CMD"}) as response:
                await response.text()

    async def stop_cover(self, did):
        await self.authenticate()
        async with aiohttp.ClientSession(cookie_jar=self._cookie_jar) as session:
            async with session.put(f"http://{self._host}/devices/{did}", json={"name": "STOP_CMD"}) as response:
                await response.text()

    async def set_cover_position(self, did, position):
        await self.authenticate()
        async with aiohttp.ClientSession(cookie_jar=self._cookie_jar) as session:
            async with session.put(f"http://{self._host}/devices/{did}",
                                   json={"name": "GOTO_POS_CMD", "value": 100 - position}) as response:
                await response.text()

    async def get_device_status(self, did):
        await self.authenticate()
        async with aiohttp.ClientSession(cookie_jar=self._cookie_jar) as session:
            async with session.get(f"http://{self._host}/v4/devices/{did}") as response:
                return await response.json()


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class AuthError(exceptions.HomeAssistantError):
    """Error to indicate an authentication error."""
