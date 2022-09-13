import atexit
import os
import struct
from typing import Union

import psutil
import pywintypes
import win32api
import win32gui
import win32process

from aceo_bot import logger
from aceo_bot.memory import kernel32


class ProcessReader:
    psutil_process: psutil.Process
    WORD_SIZE = 4

    def __init__(self, pid):
        self.closed = False
        self.hwnd = None

        self.system_info = kernel32.get_system_info()

        self.pid = pid
        self.__define_hwnd()
        if not self.hwnd:
            logger.info(
                f"""ProcessReader<pid={self.pid}> has not visible window""",
            )
            self.pid = 0

        self.process = win32api.OpenProcess(kernel32.PROCESS_ALL_ACCESS, 0, self.pid) if self.pid else None

        self.psutil_process = psutil.Process(pid)
        atexit.register(self.close)

    def __define_hwnd(self):
        win32gui.EnumWindows(self.__hwnd_set_on_match_pid, self.pid)

    def __hwnd_set_on_match_pid(self, hwnd, pid):
        _, hwnd_pid = win32process.GetWindowThreadProcessId(hwnd)
        if hwnd_pid == pid and win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
            self.hwnd = hwnd

    def close(self):
        self.psutil_process.resume()
        self.process.close()
        self.closed = True

    def find_value(self, value: bytes, limit=100):
        address = self.system_info.lpMinimumApplicationAddress

        result = []
        while address < self.system_info.lpMaximumApplicationAddress:
            memory_info = kernel32.virtual_query_ex(self.process.handle, address)
            if memory_info.accessible and memory_info.State == kernel32.MEM_COMMIT:
                dump = self.read_bytes(memory_info.BaseAddress, memory_info.RegionSize)
                index = -1
                while (index := dump.find(value, index + 1)) > 0:
                    result.append(address + index)
                    if len(result) >= limit:
                        logger.info(f"""{self.__class__.__name__} find too much {value=}. Stop memory scan""")
                        return result
            address += memory_info.RegionSize
        return result

    def get_modules(self):
        try:
            modules_addresses: list[int] = win32process.EnumProcessModules(self.process.handle)
        except pywintypes.error as err:
            logger.warn("WindowsProcess", str(err))

        return {
            os.path.basename(win32process.GetModuleFileNameEx(self.process.handle, address)): address
            for address in modules_addresses
        }

    def is_readable(self, address) -> bool:
        info = kernel32.virtual_query_ex(self.process.handle, address)
        return bool(info) and info.accessible

    def read_value_from_pointers(self, base_address, offsets: list[int] = None) -> Union[None, int]:
        address = self.read_uint32(base_address)
        if not address:
            return None

        if offsets:
            for offset in offsets:
                address = self.read_uint32(address + offset)
                if address is None:
                    return None
        return address

    def read_bool(self, address) -> Union[bool, None]:
        """ "
        :param address: address to read
        :return: on success: bool; on error: None;
        """
        value = self.read_bytes(address, 4)
        return (0 != int.from_bytes(value, byteorder="little")) if value is not None else None

    def read_bytes(self, address, length) -> Union[bytes, None]:
        """ "
        :param address: address to read
        :param length: bytes to read
        :return: on success: bytes; on error: None;
        """
        if address < self.system_info.lpMaximumApplicationAddress:
            memory_info = kernel32.virtual_query_ex(self.process.handle, address)
            if memory_info.accessible and memory_info.State == kernel32.MEM_COMMIT:
                return kernel32.read_process_memory(self.process.handle, address, length)
            else:
                logger.warning(f"Trying to read inaccessible memory {address=}")
            # try:
            #     return self._process_c.read_bytes(address, length)
            #     # return kernel32.read_process_memory(self.process.handle, address, length)
            # except Kernel32Error:
            #     logger.warning(f'Memory reading error with {address=}')
        return None

    def read_float(self, address) -> Union[float, None]:
        """ "
        :param address: address to read
        :return: on success: float; on error: None;
        """
        value = self.read_bytes(address, 4)
        return struct.unpack("f", value)[0] if value is not None else None

    def read_int32(self, address) -> Union[int, None]:
        """ "
        :param address: address to read
        :return: on success: int; on error: None;
        """
        value = self.read_bytes(address, 4)
        return int.from_bytes(value, byteorder="little", signed=True) if value is not None else None

    def read_int64(self, address) -> Union[int, None]:
        """ "
        :param address: address to read
        :return: on success: int; on error: None;
        """
        value = self.read_bytes(address, 8)
        return int.from_bytes(value, byteorder="little", signed=True) if value is not None else None

    def read_str(self, address, length) -> Union[str, None]:
        """ "
        :param address: address to read
        :param length: string length to read
        :return: on success: str on error: None;
        """
        value = self.read_bytes(address, length)
        return value.decode() if value is not None else None

    def read_str_to_end(self, address, length: int = 128) -> Union[str, None]:
        """ "
        :param address: address to read
        :param length: string length to read
        :return: on success: str on error: None;
        """
        value = self.read_bytes(address, length)

        if not value or b"\x00" not in value:
            return None

        try:
            return value[: value.index(b"\x00")].decode()
        except UnicodeDecodeError:
            return None

    def read_uint32(self, address) -> Union[int, None]:
        """ "
        :param address: address to read
        :return: on success: int; on error: None;
        """
        value = self.read_bytes(address, 4)
        return int.from_bytes(value, byteorder="little") if value is not None else None

    def read_uint64(self, address) -> Union[int, None]:
        """ "
        :param address: address to read
        :return: on success: int; on error: None;
        """
        value = self.read_bytes(address, self.WORD_SIZE)
        return int.from_bytes(value, byteorder="little") if value is not None else None

    def read_unicode(self, address, length) -> Union[str, None]:
        """ "
        :param address: address to read
        :param length: string length to read
        :return: on success: str on error: None;
        """
        value = self.read_bytes(address, length * 2)
        return value.decode("utf-16") if value is not None else None

    def write(self, address: int, data: Union[int, float], bytes=4) -> bool:
        if address < self.system_info.lpMaximumApplicationAddress:
            memory_info = kernel32.virtual_query_ex(self.process.handle, address)
            if memory_info.accessible and memory_info.State == kernel32.MEM_COMMIT:
                if isinstance(data, int):
                    bdata = data.to_bytes(bytes, byteorder="little")
                elif isinstance(data, float):
                    bdata = bytearray(struct.pack("f", data))
                else:
                    raise ValueError(f"Cannot write {data=} to {address=}")

                return kernel32.write_process_memory(self.process.handle, address, bdata[:bytes])
            else:
                logger.warning(f"Trying to write inaccessible memory {address=}")
        return False
