import enum
from typing import TYPE_CHECKING

from aceo_bot.client.structures import IngameStaticStructure
from aceo_bot.client.structures import IngameStructure
from aceo_bot.client.structures import IngameTree

if TYPE_CHECKING:
    from aceo_bot.client import AceOnlineClient


class Item(IngameStructure):
    data_size: int = 0x28

    is_equipped: bool = False
    type: "ItemType" = None
    type_id: int = None
    name: str = None

    @classmethod
    def get_from_address(cls, client: "AceOnlineClient", address: int) -> "Item":
        item_type_id = client.read_int32(address + 0x08)
        if item_type_id == ItemType.weapon_standard.value:
            item_class = WeaponStandard
        else:
            item_class = Item
        return item_class(client, address, update_on_create=True)

    def update(self):
        super(Item, self).update()
        if self.data:
            self.type_id = self.get_data_int32(self.data, 0x08)
            self.type = ItemType(self.type_id)
            self.is_equipped = self.get_data_byte_bool(self.data, 0x20)

            if address_name := self.get_data_int32(self.data, 0x1C):
                self.name = self.client.read_str_to_end(address_name + 0x05)


class WeaponStandard(Item):
    data_size = 0x30

    ammunition: int = 0

    def update(self):
        super(WeaponStandard, self).update()

        self.ammunition = 0
        if self.data:
            self.ammunition = self.get_data_int32(self.data, 0x2C)


class ItemType(int, enum.Enum):
    unknown = -1
    resource = 19
    usable = 18
    weapon_advanced = 9
    weapon_standard = 3

    @classmethod
    def _missing_(cls, value):
        return cls.unknown


class Inventory(IngameTree, IngameStaticStructure):
    address_tree_node_end_offsets = ["ACEonline.atm", 0x54DFCC]
    client_module: str = "ACEonline.atm"
    data_size: int = 0x10
    offsets = [0x54DF50, 0x0C]

    item = Item
    items: list["Item"]

    def get_item(self, address: int) -> Item:
        return Item.get_from_address(self.client, address)
