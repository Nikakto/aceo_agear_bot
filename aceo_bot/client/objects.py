from typing import List
from typing import Optional
from typing import TYPE_CHECKING

from aceo_bot.client.player.skills import SkillsTree
from aceo_bot.client.structures import IngameStaticStructure
from aceo_bot.client.structures import IngameStructure

if TYPE_CHECKING:
    from aceo_bot.client import AceOnlineClient


class Target(IngameStaticStructure):
    client_module = "ACEonline.atm"
    data_size = 0x94C
    offsets = [0x54DF3C, 0xB44]

    display_x: int = 0
    display_y: int = 0
    in_front_of: bool = False
    name: str = None
    x: float
    y: float
    z: float

    def update(self):
        super(Target, self).update()
        if self.data:
            self.x = self.get_data_float(self.data, 0x2C)
            self.y = self.get_data_float(self.data, 0x34)
            self.z = self.get_data_float(self.data, 0x30)

            self.display_x = self.get_data_int32(self.data, 0xD8, signed=True)
            self.display_y = self.get_data_int32(self.data, 0xDC, signed=True)
            self.in_front_of = 0 < self.get_data_int32(self.data, 0xE0, signed=True)

            if name_b := self.client.read_str_to_end(self.get_data_int32(self.data, 0x948) + 0x04):
                self.name = name_b


class Object(IngameStructure):
    data_size = 0x99C

    id: int = None
    display_x: int = 0
    display_y: int = 0
    in_front_of: bool = False
    is_agro: bool = False
    health_max: int = 0
    health: int = 0
    name: str = None
    x: float
    y: float
    z: float

    def __repr__(self):
        return f"Object<{hex(self.address)}>"

    def distance_to(self, obj: "Object") -> float:
        delta_x = self.x - obj.x
        delta_y = self.y - obj.y
        delta_z = self.z - obj.z
        return (delta_x**2 + delta_y**2 + delta_z**2) ** 0.5

    def update(self):
        super(Object, self).update()
        if self.data:
            self.id = self.get_data_int32(self.data, 0x918)

            self.x = self.get_data_float(self.data, 0x2C)
            self.y = self.get_data_float(self.data, 0x34)
            self.z = self.get_data_float(self.data, 0x30)

            self.display_x = self.get_data_int32(self.data, 0xD8, signed=True)
            self.display_y = self.get_data_int32(self.data, 0xDC, signed=True)
            self.in_front_of = 0 < self.get_data_int32(self.data, 0xE0, signed=True)
            self.is_agro = 0 < self.get_data_int32(self.data, 0x998)

            self.health = self.get_data_int32(self.data, 0x91C)
            self.health_max = self.get_data_int32(self.data, 0x940)

            if name_address := self.get_data_int32(self.data, 0x948):
                if name_b := self.client.read_str_to_end(name_address + 0x04):
                    self.name = name_b


class Player(IngameStaticStructure, Object):
    client_module = "ACEonline.atm"
    data_size = 0x1354
    offsets = [0x54DF3C]

    focused_object: Optional["Object"] = None
    cursor_x: int = 0
    cursor_y: int = 0
    energy: float = 0
    energy_max: int = 0
    shield: float = 0
    shield_max: int = 0
    skills: Optional[SkillsTree] = None
    sp: int = 0
    sp_max: int = 0
    target: Optional["Object"] = None
    target_potential: Optional["Object"] = None
    weapon_advanced: Optional["PlayerWeaponAdvanced"] = None
    weapon_advanced_reload_time: Optional[int] = None
    weapon_standard: Optional["PlayerWeaponStandard"] = None
    weapon_standard_is_shooting: bool = False

    def update(self):
        super(Player, self).update()

        self.target = None
        self.target_potential = None
        self.weapon_standard = None
        if self.data:
            self.cursor_x = self.get_data_int32(self.data, 0xC58, signed=True)
            self.cursor_y = self.get_data_int32(self.data, 0xC5C, signed=True)
            self.energy = self.get_data_float(self.data, 0x998)
            self.energy_max = self.get_data_int32(self.data, 0x994, signed=True)
            self.shield = self.get_data_float(self.data, 0x9A0)
            self.shield_max = self.get_data_int32(self.data, 0x99C, signed=True)
            self.sp = self.get_data_int16(self.data, 0x9A6, signed=True)
            self.sp_max = self.get_data_int16(self.data, 0x9A4, signed=True)
            self.weapon_advanced_reload_time = self.get_data_float(self.data, 0x238) or None
            self.weapon_standard_is_shooting = self.get_data_byte_bool(self.data, 0xC3C)

            if skills_tree_address := self.get_data_int32(self.data, 0x12E0):
                if skills_tree_root_address := self.client.read_int32(skills_tree_address + 0x08):
                    self.skills = SkillsTree(self.client, skills_tree_root_address, update_on_create=True)

            if target_address := self.get_data_int32(self.data, 0xB44):
                self.target = Object(self.client, target_address, update_on_create=True)

            if target_potential_address := self.get_data_int32(self.data, 0xB40):
                self.target_potential = Object(self.client, target_potential_address, update_on_create=True)

            if weapon_advanced_address := self.get_data_int32(self.data, 0x1350):
                self.weapon_advanced = PlayerWeaponAdvanced(self.client, weapon_advanced_address, update_on_create=True)

            if weapon_standard_address := self.get_data_int32(self.data, 0x134C):
                self.weapon_standard = PlayerWeaponStandard(self.client, weapon_standard_address, update_on_create=True)


class PlayerWeapon(IngameStructure):
    data_size = 0x30

    ammunition: int = 0

    def update(self):
        super(PlayerWeapon, self).update()

        self.ammunition = 0
        if self.data:
            if address_ammunition := self.get_data_int32(self.data, 0x18):
                self.ammunition = self.client.read_int32(address_ammunition + 0x2C)


class PlayerWeaponStandard(PlayerWeapon):
    data_size = 0x30

    overheat: float = 0
    is_overheated: bool = False

    def update(self):
        super(PlayerWeaponStandard, self).update()
        if self.data:
            self.is_overheated = self.get_data_byte_bool(self.data, 0x20)
            self.overheat = self.get_data_float(self.data, 0x24)


class PlayerWeaponAdvanced(PlayerWeapon):
    data_size = 0x30

    focused: list[int]  # id of objects
    reload: float

    def __init__(self, client: "AceOnlineClient", address: int = 0, *, update_on_create=False):
        self.focused = []
        super(PlayerWeaponAdvanced, self).__init__(client, address, update_on_create=update_on_create)

    def update(self):
        super(PlayerWeaponAdvanced, self).update()

        self.focused.clear()
        if self.data:
            self.reload = self.get_data_float(self.data, 0x28)

            address_focused_start = self.get_data_int32(self.data, 0x08)
            address_focused_end = self.get_data_int32(self.data, 0x0C)
            if all([address_focused_start, address_focused_end]) and address_focused_start < address_focused_end:
                length = address_focused_end - address_focused_start
                if focused_data := self.client.read_bytes(address_focused_start, length):
                    self.focused = [
                        object_id
                        for index in range(0, length + 1, 2)
                        if (object_id := self.get_data_int16(focused_data, index))
                    ]


class MobsTree(IngameStaticStructure):
    client_module = "ACEonline.atm"
    data_size = 0xA8
    offsets = [0x54DF38]

    address_tree_node_root: int = 0
    address_tree_node_end: int = 0
    length: int = 0
    items: List[Object]

    def __init__(self, client: "AceOnlineClient", address: int = 0, *, update_on_create=False):
        super(MobsTree, self).__init__(client, address, update_on_create=update_on_create)
        self.items = []

    def update(self):
        super(MobsTree, self).update()
        self.items.clear()

        pointer_tree_node_end = IngameStaticStructure.get_module_address(self.client, "ACEonline.atm") + 0x54DFDC
        self.address_tree_node_end = self.client.read_int32(pointer_tree_node_end)
        self.address_tree_node_root = 0

        self.items.clear()
        self.length = 0

        if self.data:
            self.length = self.get_data_int32(self.data, 0x5C)
            self.address_tree_node_root = self.get_data_int32(self.data, 0x54)

            leafs_to_read = {self.address_tree_node_root}
            leafs_payloads = {self.address_tree_node_root: None, self.address_tree_node_end: None}

            while leafs_to_read:
                address = leafs_to_read.pop()
                leaf_data = self.client.read_bytes(address, 0x14)
                leafs_payloads[address] = self.get_data_int32(leaf_data, 0x10)

                leaf_child = {_address for index in range(3) if (_address := self.get_data_int32(leaf_data, index * 4))}
                leafs_to_read.update(leaf_child)
                leafs_to_read -= set(leafs_payloads)

            self.items = [
                Object(self.client, address, update_on_create=True) for address in leafs_payloads.values() if address
            ]
