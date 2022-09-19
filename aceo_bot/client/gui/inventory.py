from typing import Optional
from typing import TYPE_CHECKING

import win32api
import win32con
import win32gui

from aceo_bot.client.inventory import Item
from aceo_bot.client.structures import IngameStructure

if TYPE_CHECKING:
    from aceo_bot.client import AceOnlineClient


class WindowInventory(IngameStructure):
    data_size: int = 0x258

    items: list["WindowInventoryCell"]  # max visible is 70
    fitted: "WindowInventoryFitted" = None
    fitted_count: int = 0

    window: Optional["WindowInventoryDisplay"]

    def __init__(self, client: "AceOnlineClient", address: int = 0, *, update_on_create=False):
        super(WindowInventory, self).__init__(client, address, update_on_create=update_on_create)

    def update(self):
        super(WindowInventory, self).update()
        if self.data:
            self.fitted = WindowInventoryFitted(self.client, self.address + 0x1D8, update_on_create=True)
            self.fitted_count = sum(1 if self.get_data_int32(self.data, 0x1D8 + i * 4) else 0 for i in range(10))

            self.items = [
                WindowInventoryCell(self.client, address_cell, update_on_create=True)
                for i in range(70)
                if (address_cell := self.get_data_int32(self.data, 0x70 + i * 4))
            ]

            if address_display := self.get_data_int32(self.data, 0x254):
                self.window = WindowInventoryDisplay(self.client, address_display, update_on_create=True)


class WindowInventoryCell(IngameStructure):
    data_size = 0x4C

    item: Optional["Item"]

    def update(self):
        super(WindowInventoryCell, self).update()

        self.item = None
        if self.data:
            if address_item := self.get_data_int32(self.data, 0x48):
                self.item = Item.get_from_address(self.client, address_item - 0x08)


class WindowInventoryFitted(IngameStructure):
    data_size = 0x28

    weapon_standard: Optional[WindowInventoryCell] = None

    def update(self):
        super(WindowInventoryFitted, self).update()

        self.weapon_standard = None
        if not self.data:
            return

        if address_weapon_standard_cell := self.get_data_int32(self.data, 0x08):
            self.weapon_standard = WindowInventoryCell(self.client, address_weapon_standard_cell, update_on_create=True)


class WindowInventoryDisplay(IngameStructure):
    data_size = 0x90

    is_open: bool = False
    x: int = 0
    y: int = 0
    items: Optional["WindowInventoryItemsDisplay"] = None

    @property
    def items_rect(self) -> tuple[int, int, int, int]:

        window_x, window_y, *_ = win32gui.GetWindowRect(self.client.hwnd)
        caption_height = win32api.GetSystemMetrics(win32con.SM_CYCAPTION)
        border_y = win32api.GetSystemMetrics(win32con.SM_CYBORDER)
        border_x = win32api.GetSystemMetrics(win32con.SM_CXBORDER)

        cells_x_start = window_x + border_x + self.x + 26
        cells_x_end = window_x + border_x + self.items.rect_x_end - 26
        cells_y_start = window_y + border_y + caption_height + self.items.rect_y_start
        cells_y_end = cells_y_start + 32 * 7  # todo: fix naive

        return cells_x_start, cells_y_start, cells_x_end, cells_y_end

    def update(self):
        super(WindowInventoryDisplay, self).update()

        if self.data:
            self.is_open = self.get_data_byte_bool(self.data, 0x28)
            self.x = self.get_data_int32(self.data, 0x2C, signed=True)
            self.y = self.get_data_int32(self.data, 0x30, signed=True)

            if address_items := self.get_data_int32(self.data, 0x8C, signed=False):
                self.items = WindowInventoryItemsDisplay(self.client, address_items, update_on_create=True)


class WindowInventoryItemsDisplay(IngameStructure):
    data_size = 0x90

    row: int = 0
    rect_y_start: int = 0
    rect_x_end: int = 0

    def update(self):
        super(WindowInventoryItemsDisplay, self).update()

        if self.data:
            self.row = self.get_data_int32(self.data, 0x60)
            self.rect_x_end = self.get_data_int32(self.data, 0x7C)
            self.rect_y_start = self.get_data_int32(self.data, 0x78)
