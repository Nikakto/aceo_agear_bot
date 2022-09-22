from aceo_bot.client.structures import IngameStaticStructure
from .keyboard import Keyboard


class Engine(IngameStaticStructure):
    client_module = "ACEonline.atm"
    data_size = 0x2BAE0
    offsets = [0x54DF20]

    keyboard: Keyboard = None

    def update(self):
        super(Engine, self).update()
        if not self.data:
            return

        if keyboard_address := self.get_data_int32(self.data, 0x2BADC):
            self.keyboard = Keyboard(self.client, keyboard_address, update_on_create=True)
