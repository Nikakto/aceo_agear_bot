from typing import Optional

from aceo_bot.client.inventory import Item
from aceo_bot.client.structures import IngameStaticStructure
from .inventory import WindowInventory


class GUI(IngameStaticStructure):
    client_module = "ACEonline.atm"
    data_size = 0x77C
    offsets = [0x54DF4C]

    inventory: Optional[WindowInventory] = None
    item_focused: Optional[Item] = None

    def update(self):
        super(GUI, self).update()

        self.inventory = None
        self.item_focused = None

        if self.data:
            if address_inventory := self.get_data_int32(self.data, 0xD4):
                self.inventory = WindowInventory(self.client, address_inventory, update_on_create=True)

            if address_of_something := self.get_data_int32(self.data, 0x778):
                if address_item_focused := self.client.read_int32(address_of_something + 0x1A8C):
                    self.item_focused = Item(self.client, address_item_focused)
