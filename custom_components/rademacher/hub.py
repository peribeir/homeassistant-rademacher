import aiohttp
import hashlib
import logging
from http.cookies import SimpleCookie


_LOGGER = logging.getLogger(__name__)


class Hub:
    def __init__(self, hass, host, password=''):
        self._hass = hass
        self._host = host
        self._password = password
        self._cookie_jar = aiohttp.CookieJar()
        self._authenticated = False

    async def authenticate(self) -> str:
        if self._password != '' and self._authenticated == False:
            async with aiohttp.ClientSession(cookie_jar=self._cookie_jar) as session:
                response = await session.post(f"http://{self._host}/authentication/password_salt")
                response_data = await response.json()
                if response.status == 500 and response_data['error_code'] == 5007:
                    return 'forbidden'
                if response.status != 200:
                    return 'error'
                if response_data['error_code'] != 0:
                    return 'error'
                salt = response_data['password_salt']
                hashed_password = hashlib.sha256(self._password.encode('utf-8')).hexdigest()
                salted_password = hashlib.sha256(f"{salt}{hashed_password}".encode('utf-8')).hexdigest()
                response = await session.post(
                    f"http://{self._host}/authentication/login",
                    json={"password": salted_password, "password_salt": salt}
                )
                if response.status != 200:
                    return 'forbidden'
                self._authenticated = True
                return 'ok'


    async def test_connection(self):
        if self._password == '':
            async with aiohttp.ClientSession() as session:
                response = await session.get(f"http://{self._host}/v4/devices")
                if response.status == 200:
                    return 'ok'
                elif response.status == 401:
                    return 'forbidden'
                else:
                    return 'error'
        else:
            return await self.authenticate()


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
