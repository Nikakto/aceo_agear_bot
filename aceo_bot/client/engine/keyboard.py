import string

from aceo_bot.client.structures import IngameStructure


class Keyboard(IngameStructure):
    data_size = 0x3E

    # todo: bind all keys
    # VK_ALT: bool = False
    # VK_CTRL: bool = False
    # VK_ESC: bool = False
    # VK_SPACE: bool = False
    # VK_SHIFT: bool = False
    # VK_TILDE: bool = False

    VK_0: bool = False
    VK_1: bool = False
    VK_2: bool = False
    VK_3: bool = False
    VK_4: bool = False
    VK_5: bool = False
    VK_6: bool = False
    VK_7: bool = False
    VK_8: bool = False
    VK_9: bool = False
    # VK_A: bool = False
    # VK_B: bool = False
    # VK_C: bool = False
    # VK_D: bool = False
    # VK_E: bool = False
    # VK_F: bool = False
    # VK_G: bool = False
    # VK_H: bool = False
    # VK_I: bool = False
    # VK_J: bool = False
    # VK_K: bool = False
    # VK_L: bool = False
    # VK_M: bool = False
    # VK_N: bool = False
    # VK_O: bool = False
    # VK_P: bool = False
    # VK_Q: bool = False
    # VK_R: bool = False
    # VK_S: bool = False
    # VK_T: bool = False
    # VK_U: bool = False
    # VK_V: bool = False
    # VK_W: bool = False
    # VK_X: bool = False
    # VK_Y: bool = False
    # VK_Z: bool = False

    def update(self):
        super(Keyboard, self).update()

        if not self.data:
            return

        self.VK_1 = self.get_data_byte_bool(self.data, 0x06)
        self.VK_2 = self.get_data_byte_bool(self.data, 0x07)
        self.VK_3 = self.get_data_byte_bool(self.data, 0x08)
        self.VK_4 = self.get_data_byte_bool(self.data, 0x09)
        self.VK_5 = self.get_data_byte_bool(self.data, 0x0A)
        self.VK_6 = self.get_data_byte_bool(self.data, 0x0B)
        self.VK_7 = self.get_data_byte_bool(self.data, 0x0C)
        self.VK_8 = self.get_data_byte_bool(self.data, 0x0D)
        self.VK_9 = self.get_data_byte_bool(self.data, 0x0E)
        self.VK_0 = self.get_data_byte_bool(self.data, 0x0F)
