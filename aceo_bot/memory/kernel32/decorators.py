import logging
import ctypes

from . import kernel32
from .exceptions import Kernel32Error


logger = logging.getLogger("eve_assistant")


def raise_on_error(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if code := kernel32.get_last_error():
            kernel32.set_last_error(0)
            error = ctypes.WinError(code)
            raise Kernel32Error(
                f"""OSErrorL [WinError {error.winerror}] {error.strerror}"""
            )
        return result

    return wrapper
