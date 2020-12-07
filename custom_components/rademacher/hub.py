import aiohttp


class Hub:
    def __init__(self, hass, host):
        self._hass = hass
        self._host = host

    async def test_connection(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://{self._host}/") as response:
                return True if response.status == 200 else False

    async def get_covers(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://{self._host}/v4/devices?devtype=Actuator") as response:
                devices = await response.json()

                if devices['response'] == 'get_visible_devices':
                    return devices
                else:
                    return []

    async def open_cover(self, did):
        async with aiohttp.ClientSession() as session:
            async with session.put(f"http://{self._host}/devices/{did}", json={"name": "POS_UP_CMD"}) as response:
                await response.text()

    async def close_cover(self, did):
        async with aiohttp.ClientSession() as session:
            async with session.put(f"http://{self._host}/devices/{did}", json={"name": "POS_DOWN_CMD"}) as response:
                await response.text()

    async def stop_cover(self, did):
        async with aiohttp.ClientSession() as session:
            async with session.put(f"http://{self._host}/devices/{did}", json={"name": "STOP_CMD"}) as response:
                await response.text()

    async def set_cover_position(self, did, position):
        async with aiohttp.ClientSession() as session:
            async with session.put(f"http://{self._host}/devices/{did}",
                                   json={"name": "GOTO_POS_CMD", "value": 100 - position}) as response:
                await response.text()

    async def get_device_status(self, did):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://{self._host}/v4/devices/{did}") as response:
                return await response.json()
