import datetime
import time
from collections import defaultdict
from typing import Optional
from typing import TYPE_CHECKING

import pydirectinput as pydirectinput
import win32gui
from pynput import keyboard

from aceo_bot.client import AceOnlineClient

if TYPE_CHECKING:
    from aceo_bot.client.objects import Object


BOT_ATTACK_RANGE = 1400
BOT_ATTACK_RANGE_AGRO = 1650
BOT_ATTACK_PRIORITY = [
    ["NGC Scout"],
    ["NGC Supply Ship"],
    ["Scavenger"],
]

BOT_ATTACK_IGNORE_TEMP: dict[int, datetime.datetime] = dict()
BOT_ATTACK_IGNORE_TEMP_TIME: int = 2
BOT_ATTACK_IGNORE_TEMP_TIME_COUNTER: defaultdict[int, int] = defaultdict(int)
BOT_ATTACK_IGNORE = ["Uruk", "NGC Research Probe"]

BOT_ENERGY_MIN_RATE = 1
BOT_SHIELD_MIN_RATE = 0.75
BOT_REMEDY_TIMEOUT: int = 10  # seconds
BOT_REMEDY_MIN_RATE = 0.25
BOT_SP_MIN_RATE = 0.5

BOT_TARGET_GAP = 20
BOT_TICK_TIME = 0.1

KEY_SIEGE_MODE = "2"
BOT_KEYBOARD_ENERGY_KIT = "7"
BOT_KEYBOARD_SP_KIT = "6"
BOT_KEYBOARD_SHIELD_KIT = "8"
BOT_KEYBOARD_REMEDY = "5"
BOT_KEYBOARD_BUFFS = {
    "Fire Shot": "9",
    "Concentration": "0",
}


def _target_key(client: "AceOnlineClient", obj: "Object"):
    """
    Most important target will have the heaviest key
    """
    target_in_display_x = 0 < obj.display_x < client.window_width
    target_in_display_y = 0 < obj.display_y < client.window_height

    in_display = target_in_display_x and target_in_display_y and obj.in_front_of
    in_distance = target_is_in_distance(client, obj)
    importance = next(
        (len(BOT_ATTACK_PRIORITY) - index for index, _list in enumerate(BOT_ATTACK_PRIORITY) if obj.name in _list),
        float("Infinity"),
    )
    damaged = -(obj.health / obj.health_max)
    return in_distance, in_distance and obj.is_agro, importance, damaged, in_display, obj.in_front_of


def target_get(client: "AceOnlineClient", is_agro=False, in_distance=False) -> Optional["Object"]:
    targets = sorted(
        [
            obj
            for obj in client.mobs_list.items
            if obj.name
            and (obj.name not in BOT_ATTACK_IGNORE or obj.is_agro)
            and obj.id not in BOT_ATTACK_IGNORE_TEMP
            and obj.health
            and (not is_agro or obj.is_agro)
            and (not in_distance or target_is_in_distance(client, obj))
        ],
        key=lambda obj: _target_key(client, obj),
        reverse=True,
    )

    # [print(hex(target.address), target.name, *_target_key(client, target)) for target in targets]
    return targets and targets[0]


def target_is_in_distance(client, obj):
    return client.player.distance_to(obj) <= (BOT_ATTACK_RANGE_AGRO if obj.is_agro else BOT_ATTACK_RANGE)


def target_set(client: "AceOnlineClient", target: "Object" = None) -> Optional["Object"]:
    if client.safe_read:
        client.psutil_process.suspend()

    try:
        client.mobs_list.update()
        if target := target or target_get(client, in_distance=True):
            client.write(client.player.address + 0xB44, target.address)

        client.psutil_process.resume()
        return target

    except Exception as e:
        client.psutil_process.resume()
        raise e


def run():
    client = AceOnlineClient.get()

    win32gui.SetForegroundWindow(client.hwnd)
    time.sleep(1)

    skill_remedy_timeout: datetime.datetime = datetime.datetime.min
    target_health_prev: float = 0
    target_prev: Optional[int] = None
    target_last_attack: Optional[datetime.datetime] = datetime.datetime.min
    weapon_standard_cooling_until: datetime.datetime = datetime.datetime.min

    running = True

    def stop_run():
        nonlocal running
        running = False

    global BOT_ATTACK_IGNORE_TEMP
    with keyboard.GlobalHotKeys({"<ctrl>+s": stop_run}) as h:
        while running:
            client.update()

            BOT_ATTACK_IGNORE_TEMP = {k: v for k, v in BOT_ATTACK_IGNORE_TEMP.items() if datetime.datetime.now() < v}
            mobs_exists = [mob.id for mob in client.mobs_list.items]
            mobs_was_ignored = list(BOT_ATTACK_IGNORE_TEMP_TIME_COUNTER.keys())
            for mob_id in mobs_was_ignored:
                if mob_id not in mobs_exists:
                    del BOT_ATTACK_IGNORE_TEMP_TIME_COUNTER[mob_id]

            do_nothing_triggers = [client.hwnd != win32gui.GetForegroundWindow(), not client.player]
            if any(do_nothing_triggers):
                print(datetime.datetime.now().isoformat(), "Do nothing")

                if client.player.weapon_standard_is_shooting:
                    pydirectinput.mouseUp(_pause=False)

                time.sleep(1)
                continue

            if client.player.weapon_standard_is_shooting and not client.player.target:
                pydirectinput.mouseUp(_pause=False)

            active_skills = [effect.skill.name for effect in client.status_bar.effects if effect.skill]

            shoot_only_agro = datetime.datetime.now() < weapon_standard_cooling_until
            can_shoot = (client.player.target and client.player.target.is_agro) or not shoot_only_agro
            ignored = client.player.target and (
                client.player.target.id in BOT_ATTACK_IGNORE_TEMP or client.player.target.name in BOT_ATTACK_IGNORE
            )

            if not client.player.target:
                target_prev = None

            if client.player.energy < client.player.energy_max * BOT_ENERGY_MIN_RATE:
                pydirectinput.keyDown(BOT_KEYBOARD_ENERGY_KIT, _pause=False)
            else:
                pydirectinput.keyUp(BOT_KEYBOARD_ENERGY_KIT, _pause=False)

            if client.player.shield < client.player.shield_max * BOT_SHIELD_MIN_RATE:
                pydirectinput.keyDown(BOT_KEYBOARD_SHIELD_KIT, _pause=False)
            else:
                pydirectinput.keyUp(BOT_KEYBOARD_SHIELD_KIT, _pause=False)

            if client.player.sp < client.player.sp_max * BOT_SP_MIN_RATE:
                pydirectinput.keyDown(BOT_KEYBOARD_SP_KIT, _pause=False)
            else:
                pydirectinput.keyUp(BOT_KEYBOARD_SP_KIT, _pause=False)

            no_agro_targets = not target_get(client, is_agro=True, in_distance=True)
            if required_ammunition := client.player.weapon_standard.ammunition < 250 and no_agro_targets:
                print(datetime.datetime.now().isoformat(), f"Require ammunition. Stop")

            if required_sp := client.player.sp < 50:
                print(datetime.datetime.now().isoformat(), f"Require sp. Stop")

            if required_ammunition or required_sp:
                if client.player.weapon_standard_is_shooting:
                    pydirectinput.mouseUp(_pause=False)

                if "Siege Mode" in active_skills:
                    print(datetime.datetime.now().isoformat(), 'Deactivate "Siege Mode"')
                    client.send_keyboard(KEY_SIEGE_MODE)

                time.sleep(BOT_TICK_TIME)
                continue

            buff_used = False
            for buff, key in BOT_KEYBOARD_BUFFS.items():
                if buff not in active_skills:
                    client.send_keyboard(key)
                    buff_used = True

            can_use_remedy = skill_remedy_timeout <= datetime.datetime.now()
            if client.player.shield < client.player.shield_max * BOT_REMEDY_MIN_RATE and can_use_remedy:
                client.send_keyboard(BOT_KEYBOARD_REMEDY)
                buff_used = True

            if buff_used:
                client.update()

            if client.player.weapon_standard.is_overheated:
                if "Siege Mode" in active_skills:
                    print(datetime.datetime.now().isoformat(), 'Deactivate "Siege Mode"')
                    client.send_keyboard(KEY_SIEGE_MODE)

                if client.player.weapon_standard_is_shooting:
                    pydirectinput.mouseUp(_pause=False)

                target_last_attack = None
                target_prev = None
                print(datetime.datetime.now(), f"Standard ammo is overheated")
                time.sleep(BOT_TICK_TIME)
                continue

            if client.player.target and can_shoot and not ignored:
                if client.player.target.id != target_prev:
                    print(datetime.datetime.now(), f"Target changed from {target_prev} to {client.player.target.id}")
                    target_prev = client.player.target.id
                    target_last_attack = None
                elif client.player.target.health < target_health_prev:
                    target_last_attack = datetime.datetime.now()
                elif not target_last_attack:
                    print(
                        datetime.datetime.now(),
                        f"Target {client.player.target.name} ({client.player.target.id}) is new",
                    )
                    target_last_attack = datetime.datetime.now()
                elif target_last_attack + datetime.timedelta(seconds=2) < datetime.datetime.now():
                    print(
                        datetime.datetime.now(),
                        f"Target {client.player.target.name} ({client.player.target.id}) undamaged too long",
                    )
                    delta = BOT_ATTACK_IGNORE_TEMP_TIME * (
                        5 ** BOT_ATTACK_IGNORE_TEMP_TIME_COUNTER[client.player.target.id]
                    )
                    until = datetime.datetime.now() + datetime.timedelta(seconds=delta)
                    BOT_ATTACK_IGNORE_TEMP[client.player.target.id] = until
                    BOT_ATTACK_IGNORE_TEMP_TIME_COUNTER[client.player.target.id] += 1

                if not client.player.target.is_agro and (target := target_get(client, is_agro=True, in_distance=True)):
                    if target.is_agro:
                        target_set(client, target)
                        target_last_attack = None
                        time.sleep(BOT_TICK_TIME)

                if BOT_ATTACK_RANGE_AGRO < client.player.distance_to(client.player.target):
                    until = datetime.datetime.now() + datetime.timedelta(seconds=BOT_ATTACK_IGNORE_TEMP_TIME)
                    print(
                        datetime.datetime.now().isoformat(),
                        f"Target {client.player.target.name} ({client.player.target.id}) too far. Ignore until {until.isoformat()}",
                    )
                    BOT_ATTACK_IGNORE_TEMP[client.player.target.id] = until
                    target_set(client)
                    target_last_attack = None
                    time.sleep(BOT_TICK_TIME)
                    continue

                if "Siege Mode" not in active_skills:
                    print(datetime.datetime.now().isoformat(), 'Activate "Siege Mode"')
                    client.send_keyboard(KEY_SIEGE_MODE)

                window_center_x = int(client.window_x + client.window_width / 2)
                window_center_y = int(client.window_y + client.window_height / 2) + 24

                cursor_x_min = client.player.target.display_x - BOT_TARGET_GAP
                cursor_x_max = client.player.target.display_x + BOT_TARGET_GAP
                cursor_y_min = client.player.target.display_y - BOT_TARGET_GAP
                cursor_y_max = client.player.target.display_y + BOT_TARGET_GAP

                target_health_prev = client.player.target.health

                target_focused_x = cursor_x_min <= client.player.cursor_x <= cursor_x_max
                target_focused_y = cursor_y_min <= client.player.cursor_y <= cursor_y_max
                target_in_display_x = 0 < client.player.target.display_x < client.window_width
                target_in_display_y = 0 < client.player.target.display_y < client.window_height
                target_is_potential = (
                    client.player.target_potential
                    and client.player.target_potential.address == client.player.target.address
                )

                if target_is_potential or (target_focused_x and target_focused_y):
                    if not client.player.weapon_standard_is_shooting:
                        pydirectinput.mouseDown(duration=BOT_TICK_TIME, _pause=False)
                        print(
                            datetime.datetime.now().isoformat(),
                            f"Shoot on target [Standard]: {client.player.target.name} ({client.player.target.id})",
                        )

                    can_shoot_advanced = (
                        not client.player.weapon_advanced_reload_time
                        or client.player.weapon_advanced.reload == client.player.weapon_advanced_reload_time
                    ) and client.player.target.id in client.player.weapon_advanced.focused

                    if can_shoot_advanced and client.player.weapon_advanced.ammunition:
                        print(
                            datetime.datetime.now().isoformat(),
                            f"Shoot on target [Advanced]: {client.player.target.name} ({client.player.target.id})",
                        )
                        client.send_mouse_right_click(delay=BOT_TICK_TIME)

                    time.sleep(BOT_TICK_TIME)
                    continue

                elif client.player.weapon_standard_is_shooting:
                    pydirectinput.mouseUp(_pause=False)

                if target_in_display_x and target_in_display_y:
                    print(
                        datetime.datetime.now().isoformat(),
                        f"Set mouse on target: {client.player.target.name} ({client.player.target.id})",
                    )
                    client.send_mouse_move(
                        client.window_x + client.player.target.display_x,
                        client.window_y + client.player.target.display_y + 24,
                    )

                else:
                    print(
                        datetime.datetime.now().isoformat(),
                        f"Targeting: {client.player.target.name} ({client.player.target.id})",
                    )
                    if client.player.target.in_front_of:
                        if client.player.target.display_x < 0:
                            client.send_mouse_move(client.window_x + 200, window_center_y)
                        elif client.window_width < client.player.target.display_x:
                            client.send_mouse_move(client.window_x + client.window_width - 200, window_center_y)
                        elif client.player.target.display_y < 0:
                            client.send_mouse_move(window_center_x, client.window_y + 200)
                        elif client.window_height < client.player.target.display_y:
                            client.send_mouse_move(window_center_x, client.window_y + client.window_height - 200)
                    else:
                        client.send_mouse_move(int(client.window_x + client.window_width - 200), window_center_y)

                    time.sleep(BOT_TICK_TIME)

            elif not target_get(client, is_agro=True, in_distance=True) and client.player.weapon_standard.overheat < 10:
                pydirectinput.mouseUp(_pause=False)

                if weapon_standard_cooling_until < datetime.datetime.now():
                    weapon_standard_cooling_until = datetime.datetime.now() + datetime.timedelta(seconds=10)
                    print(
                        datetime.datetime.now().isoformat(),
                        f"Cooling standard gun until {weapon_standard_cooling_until.isoformat()}",
                    )

            elif (
                not target_get(client, is_agro=True, in_distance=True)
                and datetime.datetime.now() < weapon_standard_cooling_until
            ):
                pydirectinput.mouseUp(_pause=False)

                if "Siege Mode" in active_skills:
                    print(datetime.datetime.now().isoformat(), 'Deactivate "Siege Mode"')
                    client.send_keyboard(KEY_SIEGE_MODE)

            else:
                print(datetime.datetime.now().isoformat(), "Find target: ", end="")
                pydirectinput.mouseUp(_pause=False)

                target = target_set(client)
                target_last_attack = None

                if target:
                    print(f"{target.name} ({target.id})")
                else:
                    print("None")

                if not target and "Siege Mode" in active_skills:
                    print(datetime.datetime.now().isoformat(), 'Deactivate "Siege Mode"')
                    client.send_keyboard(KEY_SIEGE_MODE)

            time.sleep(BOT_TICK_TIME)


if __name__ == "__main__":
    run()

    # client = AceOnlineClient.get()
    # win32gui.SetForegroundWindow(client.hwnd)
    # time.sleep(1)
    # pydirectinput.moveTo(800, 800)
    # pydirectinput.mouseDown()
