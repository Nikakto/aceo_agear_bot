from typing import TYPE_CHECKING

from aceo_bot.client.structures import IngameStaticStructure
from aceo_bot.client.structures import IngameStructure

if TYPE_CHECKING:
    from aceo_bot.client import AceOnlineClient


class StatusBar(IngameStaticStructure):
    client_module = "ACEonline.atm"
    data_size = 0x94C
    offsets = [0x54DF48, 0x24, 0xF0]

    effects: list["Effect"]

    def __init__(self, client: "AceOnlineClient", address: int = 0, *, update_on_create=False):
        super(StatusBar, self).__init__(client, address, update_on_create=update_on_create)
        self.effects = []

    def update(self):
        super(StatusBar, self).update()

        self.effects.clear()
        if self.data:
            effects_list_start = self.get_data_int32(self.data, 0x2C, signed=True)
            effects_list_end = self.get_data_int32(self.data, 0x30, signed=True)
            if effects_list_start and effects_list_end:
                effects_data = self.client.read_bytes(effects_list_start, effects_list_end - effects_list_start)
                self.effects = [
                    Effect(self.client, self.get_data_int32(effects_data, index), update_on_create=True)
                    for index in range(0, effects_list_end - effects_list_start, 0x04)
                ]


class Effect(IngameStructure):
    data_size = 0x04

    skill: "Skill" = None

    def update(self):
        super(Effect, self).update()
        if skill_address := self.get_data_int32(self.data, 0x00):
            self.skill = Skill(self.client, skill_address, update_on_create=True)


class Skill(IngameStructure):
    data_size = 0x20

    name: str = ""

    def update(self):
        super(Skill, self).update()
        if name_address := self.get_data_int32(self.data, 0x1C):
            # i really dont know what mean fist 4 bytes and first char at name
            self.name = self.client.read_str_to_end(name_address + 5)
