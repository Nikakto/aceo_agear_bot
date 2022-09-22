from typing import Optional

from aceo_bot.client.inventory import Item
from aceo_bot.client.structures import IngameTree


class Skill(Item):
    data_size: int = 0x50

    cooldown: float = 0
    remain: float = 0

    def update(self):
        super(Skill, self).update()
        if not self.data:
            return

        self.cooldown = self.get_data_float(self.data, 0x48) / 1000
        self.remain = self.get_data_float(self.data, 0x4C) / 1000


class SkillsTree(IngameTree):
    address_tree_node_end_offsets = ["ACEonline.atm", 0x54DFE0]
    client_module: str = "ACEonline.atm"
    data_size: int = 0x10
    offsets = [0x54DF3C, 0x12E0, 0x08]

    item = Skill
    items: list["Skill"]

    def get(self, name: str) -> Optional[Skill]:
        return next(skill for skill in self if skill.name == name)

    def get_item(self, address: int) -> Skill:
        return Skill(self.client, address, update_on_create=True)
