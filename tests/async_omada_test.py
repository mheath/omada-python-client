import logging
import pytest

import aiohttp
from omada import Omada
from configparser import ConfigParser

from omada.async_omada import create_async_omada
from .util import configLogging, loadConfig

@pytest.mark.asyncio
class TestAsyncOmada:
    async def init(self):
        logging.basicConfig()
        logging.getLogger("omada").setLevel(logging.DEBUG)

        self.config = loadConfig()
        self.config.read("test.cfg")
        omadaCfg = self.config['omada']
        session = aiohttp.ClientSession(
            connector = aiohttp.TCPConnector(ssl=omadaCfg.get("verify", False)),
            cookie_jar = aiohttp.CookieJar(unsafe=True)
        )
        self.omada = await create_async_omada(session, omadaCfg.get("host"), omadaCfg.get("site", "Default"))
        await self.omada.login(omadaCfg.get("username"), omadaCfg.get("password"))
        return session

    async def test_is_logged_in(self):
        async with await self.init():
            assert await self.omada.is_logged_in()

    async def test_logout(self):
        async with await self.init():
            assert await self.omada.is_logged_in()
            await self.omada.logout()
            assert not await self.omada.is_logged_in()

    async def test_current_user(self):
        async with await self.init():
            currentUser = await self.omada.get_current_user()
            assert self.config['omada'].get("username") == currentUser['name']

    async def test_get_clients(self):
        async with await self.init():
            clients = await self.omada.get_clients()
            assert len(clients) > 0

    async def test_get_client(self):
        async with await self.init():
            clients = await self.omada.get_clients()
            mac = clients[0]['mac']

            client = await self.omada.get_client(mac)
            assert clients[0]['mac'] == client['mac']
            assert clients[0]['name'] == client['name']
            assert clients[0]['ip'] == client['ip']

    async def test_page_clients(self):
        async with await self.init():
            await self._page_clients(5)

    async def test_single_page_clients(self):
        async with await self.init():
            await self._page_clients(1)

    async def _page_clients(self, page_size):
        paged_clients = self.omada.page_clients(page_size = page_size)

        row_count = 0

        assert paged_clients.has_next
        while paged_clients.has_next:
            clients = await paged_clients.next()
            assert len(clients) <= page_size
            row_count += len(clients)
            total_rows = paged_clients.total_rows
            print(f"Row count {row_count} total rows {total_rows}")
            assert total_rows is not None
            assert row_count <= total_rows
            
        print(f"Final row count {row_count} pager total rows {paged_clients.total_rows}")
        assert row_count == paged_clients.total_rows

    async def test_update_client(self):
        async with await self.init():
            clients = await self.omada.get_clients()
            assert len(clients) > 0
            mac = clients[0]['mac']

            originalName = clients[0]['name']
            testName = f"Omada Python Client Test (was: {originalName})"
            await self.omada.update_client(mac, {'name': testName})

            updatedClient = await self.omada.get_client(mac)
            assert testName == updatedClient['name']

            await self.omada.update_client(mac, {'name': originalName})
            restoredClient = await self.omada.get_client(mac)

            assert originalName == restoredClient['name']

    async def test_get_devices(self):
        async with await self.init():
            devices = await self.omada.get_devices()
            assert len(devices) > 0

    async def test_get_switch(self):
        async with await self.init():
            device = await self._find_first_switch()
            if device is None:
                pytest.skip("No switch present")
            else:
                mac = device['mac']
                switch = await self.omada.get_switch(mac)
                assert 'switch' == switch['type']
                assert mac == switch['mac']

    async def test_get_switch_ports(self):
        async with await self.init():
            device = await self._find_first_switch()
            if device is None:
                pytest.skip("No switch present")
            else:
                mac = device['mac']
                switch = await self.omada.get_switch(mac)
                ports = await self.omada.get_switch_ports(mac)
                assert len(ports) == switch['deviceMisc']['portNum']

    async def _find_first_switch(self):
        devices = await self.omada.get_devices()
        
        for device in devices:
            if device['type'] == 'switch':
                return device

    async def test_get_ap(self):
        async with await self.init():
            device = await self._find_first_ap()
            if device is None:
                pytest.skip("No AP present")
            else:
                mac = device['mac']
                ap = await self.omada.get_ap(mac)
                assert 'ap' == ap['type']
                assert mac == ap['mac']

    async def _find_first_ap(self):
        devices = await self.omada.get_devices()
        
        for device in devices:
            if device['type'] == 'ap':
                return device

    async def test_get_alerts(self):
        async with await self.init():
            alerts = await self.omada.get_alerts()
            assert alerts is not None

            with pytest.raises(ValueError):
                await self.omada.get_alerts(level = "Foo")

            with pytest.raises(ValueError):
                await self.omada.get_alerts(module = "Bar")

