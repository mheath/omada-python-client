"""Async TP-Link Omada client"""
import aiohttp
import logging
from typing import Any

from aiohttp.client_exceptions import ContentTypeError

from .const import (
    DEFAULT_PAGE_SIZE,
    HEADER_CSRF_TOKEN,
    HEADER_LOCATION,
)
from .exceptions import raiseOmadaException
from .util import (
    AsyncPager,
    add_level_filter_param,
    add_module_filter_param,
)

_LOGGER = logging.getLogger(__name__)

class AsyncOmada:
    """Asyncio client for TP-Link Omada controller"""
    def __init__(
        self,
        session: aiohttp.ClientSession,
        site: str
    ) -> None:
        # self._base_url gets set in `init` coroutine
        self.base_url = None
        self.page_size = DEFAULT_PAGE_SIZE
        self.site = site
        self._session = session

    async def init(self, host: str) -> None:
        """Coroutine to initialize the content"""
        self.base_url = await self._get_base_url(host)
        _LOGGER.debug("Using base URL %s", self.base_url)

    # ***** Login/logout

    async def login(self, username: str, password: str) -> None:
        """Login to Omada Controller"""
        url = f"{self.base_url}/login"
        response = await self._session.post(
            url,
            json = {'username': username, 'password': password}
        )
        result = await self._validate_response(url, response)

        token = result['token']
        self._session.headers[HEADER_CSRF_TOKEN] = token

    async def logout(self) -> None:
        """Log out"""
        await self._post("/logout")

    async def is_logged_in(self) -> bool:
        """Checks if the Omada instance is currently logged in"""
        try:
            result = await self._get('/loginStatus')
            return result['login']
        except ContentTypeError:
            # Omada API redirects to login page when not logged in
            return False

    async def get_current_user(self) -> dict[str, Any]:
        """Returns information about the currently logged in user"""
        return await self._get('/users/current')

    # ***** Clients
    async def get_client(self, mac) -> dict[str, Any]:
        """Returns details about the specified client"""
        return await self._get(f"/sites/{self.site}/clients/{mac}")

    async def get_clients(self) -> dict[str, Any]:
        """Returns a list of active clients"""
        return await self.page_clients().all()

    def page_clients(self, page: int = None, page_size: int = None) -> AsyncPager:
        """"Returns a Pager to """
        return AsyncPager(page, lambda page:
            (await self._get_page(
                f"/sites/{self.site}/clients",
                page,
                page_size
            ) for _ in '_').__anext__()
        )

    async def update_client(self, mac: str, data: dict[str, Any]) -> dict[str, Any]:
        """Updates a client"""
        return await self._patch(f"/sites/{self.site}/clients/{mac}", data) 

    async def block_client(self, mac: str) -> dict[str, Any]:
        """Blocks a client"""
        await self._post(f"/sites/{self.site}/cmd/clients/{mac}/block")

    async def unblock_client(self, mac: str) -> dict[str, Any]:
        """Unblocks a client"""
        return await self._post(f"/sites/{self.site}/cmd/clients/{mac}/unblock")

    # ***** Devices
    async def get_devices(self) -> list[dict[str, Any]]:
        """Returns a list of all the devices"""
        return await self._get(f"/sites/{self.site}/devices")

    async def reboot_device(self, mac: str) -> dict[str, Any]:
        """Reboots a device"""
        return await self._post(f"/sites/{self.site}/cmd/devices/{mac}/reboot")

    async def upgrade_device(self, mac: str) -> None:
        """Starts the upgrade of a device"""
        self._post(f"/sites/{self.site}/cmd/devices/{mac}/onlineUpgrade")

    async def get_switch(self, mac: str) -> dict[str, Any]:
        """Returns details about the specified switch"""
        return await self._get(f"/sites/{self.site}/switches/{mac}")

    async def get_switch_ports(self, mac: str) -> list[dict[str, Any]]:
        """Returns details about the specified switch's ports"""
        return await self._get(f"/sites/{self.site}/switches/{mac}/ports")

    async def get_ap(self, mac: str) -> dict[str, Any]:
        """Returns the specified ap"""
        return await self._get(f"/sites/{self.site}/eaps/{mac}")

    # ***** Alerts and Events

    async def get_alerts(
        self,
        archived: bool = False,
        level: str = None,
        module: str = None,
        search: str = None
    ):
        """Returns a list of alerts"""
        return await self.page_alerts(1, self.page_size, archived, level, module, search).all()

    def page_alerts(
        self,
        page: int = 1,
        page_size: int = None,
        archived: bool = False,
        level: str = None,
        module: str = None,
        search: str = None
    ) -> AsyncPager:
        params = {}

        params['filters.archived'] = 'true' if archived else 'false'
        add_level_filter_param(params, level)
        add_module_filter_param(params, module)
        if search:
            params['searchKey'] = search
        return AsyncPager(page, lambda page:
            (await self._get_page(
                f"/sites/{self.site}/alerts",
                page,
                page_size,
                params
            ) for _ in '_').__anext__()
        )

    # ***** IO methods

    async def _get(self, path: str, params: dict = None) -> dict[str, Any]:
        url = self.base_url + path
        async with self._session.get(url, params = params) as response:
            _LOGGER.debug("GET %s params=%s -> %s", url, params, response)
            return await self._validate_response(url, response)

    async def _get_base_url(self, host: str) -> str:
        url = f"https://{host}"
        async with self._session.get(url, allow_redirects=False) as response:
            if not HEADER_LOCATION in response.headers:
                raise ValueError(f'Expected redirect from {host}')
            return response.headers[HEADER_LOCATION][:-6] + '/api/v2'

    async def _get_page(
        self,
        path: str,
        page: int,
        page_size: int,
        params: dict = None
    ) -> dict[str, Any]:
        if page_size is None:
            page_size = self.page_size
        if params is None:
            params = {}
        params['currentPage'] = page
        params['currentPageSize'] = page_size
        return await self._get(path, params)

    async def _patch(self, path: str, data: dict, params: dict = None) -> dict[str, Any]:
        url = self.base_url + path
        async with self._session.patch(url, params=params, json=data) as response:
            _LOGGER.debug("PATCH %s %s -> %s", url, params, response)
            return await self._validate_response(url, response)

    async def _post(self, path: str, data: dict = None, params: dict = None) -> dict[str, Any]:
        url = self.base_url + path
        async with self._session.post(url, json=data, params=params) as response:
            _LOGGER.debug("POST %s params=%s json=%s -> %s", url, params, data, response)
            return await self._validate_response(url, response)

    async def _validate_response(
        self,
        url: str,
        response: aiohttp.ClientResponse
    ) -> dict[str, Any]:
        #response.raise_for_status()
        await response.read()
        _LOGGER.debug("Response from %s content %s", url, response._body)
        json = await response.json()
        if not 'errorCode' in json:
            raise ValueError(f"Response from {url} did not contain 'errorCode'")
        error_code = json['errorCode']
        msg = None
        if 'msg' in json:
            msg=json['msg']
        if error_code != 0:
            raiseOmadaException(error_code, msg)

        if 'result' in json:
            return json['result']

        return {}


async def create_async_omada(
    session: aiohttp.ClientSession,
    host: str,
    site: str = 'Default'
) -> AsyncOmada:
    omada = AsyncOmada(session, site)
    await omada.init(host)
    return omada
