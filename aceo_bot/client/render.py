from typing import TYPE_CHECKING

from aceo_bot.client.structures import IngameStaticStructure
from aceo_bot.client.structures import IngameStructure

if TYPE_CHECKING:
    from aceo_bot.client import AceOnlineClient


class Render(IngameStaticStructure):
    client_module = "ACEonline.atm"
    data_size = 0x2C640
    offsets = [0x54DF20]

    # scene: "RenderScene" = None

    def __init__(self, client: "AceOnlineClient", address: int = 0, *, update_on_create=False):
        super(Render, self).__init__(client, address, update_on_create=update_on_create)
        self.targets = []

    def update(self):
        super(Render, self).update()

        # self.scene = RenderScene(self.client, self.get_data_int32(self.data, 0x2C63C))


# class RenderScene(IngameStructure):
#     data_size = 0xC
#
#     list_start: int = None
#     list_end: int = None
#
#     def __init__(self, client: "Client", address: int = 0, *, update_on_create=False):
#         super(RenderScene, self).__init__(client, address, update_on_create=update_on_create)
#
#     def update(self):
#         super(RenderScene, self).update()
#
#         self.list_start = self.get_data_int32(self.data, 0xB4)
#         self.list_end = self.get_data_int32(self.data, 0xB8)
