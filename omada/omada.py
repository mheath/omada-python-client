''' TP-Link Omada client '''
from __future__ import annotations

import logging
import requests

from typing import Any

from .const import (
    DEFAULT_PAGE_SIZE,
    HEADER_CSRF_TOKEN,
    HEADER_LOCATION,
)
from .exceptions import raiseOmadaException
from .util import (
    Pager,
    add_level_filter_param,
    add_module_filter_param,
)

_LOGGER = logging.getLogger(__name__)

#pylint: disable-msg=too-many-arguments
class Omada:
    """Client for TP-Link Omada controller."""

    def __init__(self, host: str, site: str = 'Default', session: requests.Session = None) -> None:
        self._session = session if session is not None else requests.Session()
        self.site = site

        self.page_size = DEFAULT_PAGE_SIZE

        self.base_url = self._get_base_url(host)
        _LOGGER.debug('Using base URL %s', self.base_url)

    def login(self, username: str, password: str) -> None:
        """Login to Omada controller"""
        url = f"{self.base_url}/login"
        response = self._session.post(url, json = {'username': username, 'password': password})
        result = self._validate_response(url, response)

        token = result['token']
        self._session.headers[HEADER_CSRF_TOKEN] = token

    def logout(self) -> None:
        """Log out"""
        self._post("/logout")

    def is_logged_in(self) -> bool:
        """Checks if the Omada instance is currently logged in"""
        try:
            return self._get('/loginStatus')['login']
        except requests.exceptions.JSONDecodeError:
            # One would think that this call would return False when not logged in
            # but instead it redirects to the HTML login page causing the JSON
            # parsing to fail.
            return False

    def get_current_user(self) -> dict[str, Any]:
        """Returns information about the currently logged in user"""
        return self._get('/users/current')

    # ***** Clients

    def get_client(self, mac: str) -> dict[str, Any]:
        """Returns details about the specified client"""
        return self._get(f"/sites/{self.site}/clients/{mac}")

    def get_clients(self) -> dict[str, Any]:
        """Returns a list of active clients"""
        return self.page_clients().all()

    def page_clients(self, page: int = None, page_size: int = None) -> Pager:
        """"Returns a Pager to """
        return Pager(page, lambda page:
            self._get_page(f"/sites/{self.site}/clients", page, page_size)
        )

    def update_client(self, mac: str, data: dict[str, Any]) -> None:
        """Updates a client"""
        self._patch(f"/sites/{self.site}/clients/{mac}", data)

    def block_client(self, mac: str) -> None:
        """Blocks a client"""
        self._post(f"/sites/{self.site}/cmd/clients/{mac}/block")

    def unblock_client(self, mac: str) -> None:
        """Unblocks a client"""
        self._post(f"/sites/{self.site}/cmd/clients/{mac}/unblock")

    # ***** Devices

    def get_devices(self):
        """Returns a list of all the devices"""
        return self._get(f"/sites/{self.site}/devices")

    def reboot_device(self, mac: str) -> dict[str, Any]:
        """Reboots a device"""
        return self._post(f"/sites/{self.site}/cmd/devices/{mac}/reboot")

    def upgrade_device(self, mac: str) -> None:
        """Starts the upgrade of a device"""
        self._post(f"/sites/{self.site}/cmd/devices/{mac}/onlineUpgrade")

    def get_switch(self, mac: str) -> dict[str, Any]:
        """Returns details about the specified switch"""
        return self._get(f"/sites/{self.site}/switches/{mac}")

    def get_switch_ports(self, mac: str) -> list[dict[str, Any]]:
        """Returns details about the specified switch's ports"""
        return self._get(f"/sites/{self.site}/switches/{mac}/ports")

    def get_ap(self, mac: str) -> dict[str, Any]:
        """Returns the specified ap"""
        return self._get(f"/sites/{self.site}/eaps/{mac}")

    # Alerts and events

    def get_alerts(
        self,
        archived: bool = False,
        level: str = None,
        module: str = None,
        search: str = None
    ):
        """Returns a list of alerts"""
        return self.page_alerts(1, self.page_size, archived, level, module, search).all()

    def page_alerts(
        self,
        page: int = 1,
        page_size: int = None,
        archived: bool = False,
        level: str = None,
        module: str = None,
        search: str = None
    ) -> Pager:
        params = {}

        params['filters.archived'] = 'true' if archived else 'false'
        add_level_filter_param(params, level)
        add_module_filter_param(params, module)
        if search:
            params['searchKey'] = search
        return Pager(page, lambda page:
            self._get_page(f"/sites/{self.site}/alerts", page, page_size, params)
        )

    def get_events(
        self,
        level: str = None,
        module: str = None,
        search: str = None
    ) -> list[dict[str, Any]]:
        """Returns a list of events"""
        return self.page_events(1, self.page_size, level, module, search)

    def page_events(
        self,
        page: int = 1,
        page_size: int = None,
        level: str = None,
        module: str = None,
        search: str = None,
    ) -> Pager:
        params = {}

        add_level_filter_param(params, level)
        add_module_filter_param(params, module)
        if search:
            params['searchKey'] = search

        return Pager(page, lambda page:
            self._get_page(f"/sites/{self.site}/events", page, page_size, params)
        )

    # ***** IO methods

    def _get(self, path: str, params: dict = None) -> dict[str, Any]:
        url = self.base_url + path
        response = self._session.get(url, params = params)
        _LOGGER.debug("GET %s params=%s -> %s", url, params, response)
        return self._validate_response(url, response)

    def _get_page(self, path: str, page: int, page_size: int, params: dict = None) -> dict[str, Any]:
        if page_size is None:
            page_size = self.page_size
        if params is None:
            params = {}
        params['currentPage'] = page
        params['currentPageSize'] = page_size
        return self._get(path, params)

    def _patch(self, path: str, data: dict, params: dict = None) -> dict[str, Any]:
        url = self.base_url + path
        response = self._session.patch(url, params=params, json=data)
        _LOGGER.debug("PATCH %s %s -> %s", url, params, response)
        return self._validate_response(url, response)

    def _post(self, path: str, data: dict = None, params: dict = None) -> dict[str, Any]:
        url = self.base_url + path
        response = self._session.post(url, json = data, params = params)
        _LOGGER.debug("POST %s params=%s json=%s -> %s", url, params, data, response)
        return self._validate_response(url, response)

    def _get_base_url(self, host: str) -> str:
        url = f"https://{host}"
        response = self._session.get(url, allow_redirects=False)
        response.raise_for_status()
        if not response.is_redirect:
            raise ValueError(f'Expected redirect from {host}')
        return response.headers[HEADER_LOCATION][:-6] + '/api/v2'

    def _validate_response(self, url: str, response: requests.Response):
        response.raise_for_status()
        _LOGGER.debug("Response from %s content %s", url, response.content)
        json = response.json()
        if not 'errorCode' in json:
            raise ValueError(f"Response from {url} did not contain 'errorCode'")
        error_code = json['errorCode']
        msg = None
        if 'msg' in json:
            msg = json['msg']
        if error_code != 0:
            raiseOmadaException(error_code, msg)

        if 'result' in json:
            return json['result']

        return {}

#pylint: enable-msg=too-many-arguments
