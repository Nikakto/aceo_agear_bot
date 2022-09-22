import abc
import os
import struct
from typing import Optional
from typing import TYPE_CHECKING
from typing import Type

import pywintypes
import win32process

from aceo_bot import logger
from aceo_bot.memory import ProcessReader

if TYPE_CHECKING:
    from aceo_bot.client import AceOnlineClient


class IngameStructure(abc.ABC):
    address: int = 0
    data: bytes = b""
    data_size: int
    client: "AceOnlineClient"

    @property
    @abc.abstractmethod
    def data_size(self):
        ...

    def __init__(self, client: "AceOnlineClient", address: int = 0, *, update_on_create=False):
        self.client = client
        self.address = address
        self.__post_init__()

        if update_on_create:
            self.update()

    def __eq__(self, other: "IngameStructure"):
        return self.address == other.address

    @staticmethod
    def get_data_byte(data: bytes, pos: int, signed: bool = False) -> int:
        data_range = slice(pos, pos + 4)
        return int.from_bytes(data[data_range], byteorder="little", signed=signed)

    @staticmethod
    def get_data_byte_bool(data: bytes, pos: int) -> bool:
        data_range = slice(pos, pos + 1)
        return bool(int.from_bytes(data[data_range], byteorder="little"))

    @staticmethod
    def get_data_float(data: bytes, pos: int) -> int:
        data_range = slice(pos, pos + 4)
        return struct.unpack("f", data[data_range])[0]

    @staticmethod
    def get_data_int16(data: bytes, pos: int, signed: bool = False) -> int:
        data_range = slice(pos, pos + 2)
        return int.from_bytes(data[data_range], byteorder="little", signed=signed)

    @staticmethod
    def get_data_int32(data: bytes, pos: int, signed: bool = False) -> int:
        data_range = slice(pos, pos + 4)
        return int.from_bytes(data[data_range], byteorder="little", signed=signed)

    def __post_init__(self):
        pass

    @abc.abstractmethod
    def update(self):
        if self.client.is_readable(self.address):
            self.data = self.client.read_bytes(self.address, self.data_size)
        else:
            self.data = b""


class IngameStaticStructure(IngameStructure):
    address: int
    client: "AceOnlineClient"
    client_module: str
    client_module_address: int = None
    offsets: list[int]  # first address is Module

    def __post_init__(self):
        self.client_module_address = self.get_module_address(self.client, self.client_module)
        if not self.client_module_address:
            raise ValueError(f'Cannot define base address of "{self.client_module}"')

    @classmethod
    def get_module_address(cls, client: ProcessReader, module_name: str) -> Optional[int]:
        return cls.get_modules(client).get(module_name)

    @staticmethod
    def get_modules(client: ProcessReader):
        try:
            modules_addresses: list[int] = win32process.EnumProcessModules(client.process.handle)
        except pywintypes.error as err:
            logger.warn("WindowsProcess", str(err))

        return {
            os.path.basename(win32process.GetModuleFileNameEx(client.process.handle, address)): address
            for address in modules_addresses
        }

    def update(self):
        address = self.client_module_address + self.offsets[0]
        self.address = self.client.read_value_from_pointers(address, offsets=self.offsets[1:])
        super(IngameStaticStructure, self).update()


class IngameTree(IngameStructure):
    item: Type[IngameStructure]

    address_tree_node_end_offsets: tuple[str, int]
    address_tree_node_end: int = 0
    items: list

    def __init__(self, client: "AceOnlineClient", address: int = 0, *, update_on_create=False):
        self.items = []
        super(IngameTree, self).__init__(client, address, update_on_create=update_on_create)

    def __iter__(self):
        return iter(self.items)

    def get_address_tree_node_end(self) -> Optional[int]:
        module_name, offset = self.address_tree_node_end_offsets
        pointer_tree_node_end = IngameStaticStructure.get_module_address(self.client, module_name) + offset
        return self.client.read_int32(pointer_tree_node_end)

    def get_item(self, address):
        return self.item(self.client, address, update_on_create=True)

    def update(self):
        super(IngameTree, self).update()

        self.address_tree_node_end = self.get_address_tree_node_end()
        self.items.clear()

        if self.data and self.address_tree_node_end:
            leafs_to_read = {self.address}
            leafs_payloads = {self.address: None, self.address_tree_node_end: None}

            while leafs_to_read:
                address = leafs_to_read.pop()
                leaf_data = self.client.read_bytes(address, 0x14)
                leafs_payloads[address] = self.get_data_int32(leaf_data, 0x10)

                leaf_child = {_address for index in range(3) if (_address := self.get_data_int32(leaf_data, index * 4))}
                leafs_to_read.update(leaf_child)
                leafs_to_read -= set(leafs_payloads)

            self.items = [self.get_item(address) for address in leafs_payloads.values() if address]
