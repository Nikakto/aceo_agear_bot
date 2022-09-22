from aceo_bot.client import AceOnlineClient
from aceo_bot.client.inventory import WeaponStandard
from main import BOT_WEAPONS_STANDARD

if __name__ == "__main__":
    client = AceOnlineClient.get()
    client.update()

    for item in client.inventory.items:
        if isinstance(item, WeaponStandard) and item.name in BOT_WEAPONS_STANDARD:
            print(item.name, item.ammunition)
