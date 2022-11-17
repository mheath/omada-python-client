'''Exceptions thrown by Omada clients'''
from __future__ import annotations

def raiseOmadaException(error_code: int, msg: str) -> None:
    raise OmadaError(error_code, msg)


class OmadaError(Exception):
    """Exception thrown when Omada returns an error response"""

    def __init__(self, error_code: int, msg: str) -> None:
        self.error_code = error_code
        self.msg = msg

    def __str__(self):
        return f"errorCode: {self.error_code}, msg: '{self.msg}'"
