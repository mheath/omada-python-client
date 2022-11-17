'''Shared constants for TP-Link Omada clients'''
from __future__ import annotations

from typing import (
    Final
)

DEFAULT_PAGE_SIZE: Final = 1024

HEADER_CSRF_TOKEN: Final = "Csrf-Token"
HEADER_LOCATION: Final = "Location"

LEVEL_ERROR: Final = "Error"
LEVEL_WARNING: Final = "Warning"
LEVEL_INFORMATION: Final = "Information"
LEVEL_VALUES: Final = (LEVEL_ERROR, LEVEL_WARNING, LEVEL_INFORMATION)

MODULE_DEVICE: Final = "Device"
MODULE_OPERATION: Final = "Operation"
MODULE_SYSTEM: Final = "System"
MODULE_VALUES: Final = (MODULE_DEVICE, MODULE_OPERATION, MODULE_SYSTEM)