import datetime
import time

import pydirectinput
import win32api
import win32con
import win32gui
import win32process

from aceo_bot.client.gui import GUI
from aceo_bot.client.gui.inventory import WindowInventory
from aceo_bot.client.inventory import Inventory
from aceo_bot.client.objects import MobsTree
from aceo_bot.client.objects import Player
from aceo_bot.client.objects import Target
from aceo_bot.client.status import StatusBar
from aceo_bot.memory import ProcessReader


class AceOnlineClient(ProcessReader):
    mobs_list: MobsTree = None
    status_bar: StatusBar = None
    player: Player = None

    inventory: Inventory = None
    last_update: datetime.datetime = None
    last_update_time_passed: float = None
    gui: GUI = None

    window_x: int = 0
    window_y: int = 0
    window_width: int = 0
    window_height: int = 0

    def __init__(self, pid: int, *, safe_read: bool = True):
        super(AceOnlineClient, self).__init__(pid)
        self.safe_read = safe_read

        self.gui = GUI(self, update_on_create=False)
        self.inventory = Inventory(self, update_on_create=False)
        self.mobs_list = MobsTree(self, update_on_create=False)
        self.status_bar = StatusBar(self, update_on_create=False)
        self.player = Player(self, update_on_create=False)

        self.update()

    def __repr__(self):
        return f"""AceOnline (pid={self.pid})"""

    @classmethod
    def get(cls, safe_read: bool = True) -> "AceOnlineClient":
        hwnd = win32gui.FindWindow(None, "ACEonline_R")
        if not hwnd:
            raise ValueError("Cannot find ACEonline_R active window")

        _, hwnd_pid = win32process.GetWindowThreadProcessId(hwnd)
        return cls(pid=hwnd_pid, safe_read=safe_read)

    @staticmethod
    def send_keyboard(key: str, delay=0.25):
        pydirectinput.keyDown(key, _pause=False)
        time.sleep(delay)
        pydirectinput.keyUp(key, _pause=False)

    def send_mouse_move(self, x, y):
        # win32api.SetCursorPos((x, y))
        pydirectinput.moveTo(x, y)

    def send_mouse_double_click(self, x: int = None, y: int = None):
        flags, hcursor, (mouse_x, mouse_y) = win32gui.GetCursorInfo()
        pydirectinput.click(x or mouse_x, y or mouse_y)
        time.sleep(0.1)
        pydirectinput.click(x or mouse_x, y or mouse_y)

    def send_mouse_scroll(self, rows: int, x: int = None, y: int = None):
        flags, hcursor, (mouse_x, mouse_y) = win32gui.GetCursorInfo()
        win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, x or mouse_x, y or mouse_y, -rows, 0)

    @staticmethod
    def send_mouse_right_click(x=None, y=None, delay=0.01):
        flags, hcursor, (mouse_x, mouse_y) = win32gui.GetCursorInfo()
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, x or mouse_x, y or mouse_y, 0, 0)
        time.sleep(delay)
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, x or mouse_x, y or mouse_y, 0, 0)

    def update(self):
        start_at = time.time()
        self.window_x, self.window_y, self.window_width, self.window_height = win32gui.GetWindowRect(self.hwnd)

        if self.safe_read:
            self.psutil_process.suspend()

        try:
            self.gui.update()
            self.inventory.update()
            self.mobs_list.update()
            self.status_bar.update()
            self.player.update()

            self.psutil_process.resume()
            self.last_update_time_passed = time.time() - start_at
            self.last_update = datetime.datetime.now()
        except Exception as e:
            self.psutil_process.resume()
            raise e
