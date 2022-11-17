'''Utility classes used by Omada clients'''

from typing import Any

from .const import (
    LEVEL_VALUES,
    MODULE_VALUES,
)

def add_level_filter_param(params, level):
    if level in LEVEL_VALUES:
        params['filters.level'] = level
    elif level is not None:
        raise ValueError(f"Invalid value ({level}) for 'level'. Must be one of {LEVEL_VALUES}")

def add_module_filter_param(params, module):
    if module in MODULE_VALUES:
        params['filters.module'] = module
    elif module is not None:
        raise ValueError(f"Invalid value ({module}) for 'module'. Must be one of {MODULE_VALUES}")

class Pager:
    """Provides support for handling paged responses from Omada controller"""
    def __init__(self, page: int, getter) -> None:
        if page is None:
            page = 1
        self.current_page = page
        self.getter = getter
        self.has_next = True
        self.total_rows = None

    def next(self) -> dict[str, Any]:
        if not self.has_next:
            raise RuntimeError("All pages have been loaded")
        result = self.getter(self.current_page)
        return self._update(result)

    def _update(self, result) -> dict[str, Any]:
        self.current_page = result['currentPage'] + 1
        self.total_rows = result['totalRows']
        self.has_next = self.total_rows > result['currentPage'] * result['currentSize']
        return result['data']

    def all(self):
        data = []
        while self.has_next:
            data.extend(self.next())
        return data

class AsyncPager(Pager):
    """Provides async support for handling paged responses from Omada controller"""
    async def next(self) -> dict[str, Any]:
        if not self.has_next:
            raise RuntimeError("All pages have been loaded")
        result = await self.getter(self.current_page)
        return self._update(result)

    async def all(self):
        data = []
        while self.has_next:
            data.extend(await self.next())
        return data
