from typing import Dict, NamedTuple, TYPE_CHECKING
from BaseClasses import Item, ItemClassification as IC
from .options import *

if TYPE_CHECKING:
    from . import WiiPlayWorld

class WiiPlayItem(Item):
    game: str = "Wii Play"

class ItemData(NamedTuple):
    id: int
    classification: IC

base_id = 0

progressive_games = {
    "Shooting Range": ItemData(base_id + 1, IC.progression|IC.useful),
    "Find Mii": ItemData(base_id + 2, IC.progression|IC.useful),
    "Table Tennis": ItemData(base_id + 3, IC.progression|IC.useful),
    "Pose Mii": ItemData(base_id + 4, IC.progression|IC.useful),
    "Laser Hockey": ItemData(base_id + 5, IC.progression|IC.useful),
    "Billiards": ItemData(base_id + 6, IC.progression|IC.useful),
    "Fishing": ItemData(base_id + 7, IC.progression|IC.useful),
    "Charge!": ItemData(base_id + 8, IC.progression|IC.useful),
    "Tanks!": ItemData(base_id + 9, IC.progression|IC.useful),
}

find_mii_upgrades = {
    "Starting Clock Extension - Find Mii": ItemData(base_id + 101, IC.useful),
    "Stage Clear Time Bonus - Find Mii": ItemData(base_id + 102, IC.useful),
}

pose_mii_upgrades = {
    "Extra Life - Pose Mii": ItemData(base_id + 201, IC.useful),
    # "Progressive Pose - Pose Mii": ItemData(base_id + 202, IC.useful), # Will add in future
}

fishing_upgrades = {
    "No more Small Fry - Fishing": ItemData(base_id + 301, IC.useful),
}

tanks_items = {
    "Extra Starting Life - Tanks!": ItemData(base_id + 401, IC.useful),
    "Max Bullets Up - Tanks!": ItemData(base_id + 402, IC.useful),
    "Max Mines Up - Tanks!": ItemData(base_id + 403, IC.useful),
    "Max Ricochets Up - Tanks!": ItemData(base_id + 404, IC.useful),
}

wiiplay_fillers = {
    "Filler": ItemData(base_id + 502, IC.filler),
    "+10 Rally Bonus! - Table Tennis": ItemData(base_id + 503, IC.filler),
    "+2 Points! - Laser Hockey": ItemData(base_id + 504, IC.filler),
    "Feeling sleepy...": ItemData(base_id + 505, IC.filler),
    "Extra Life - Tanks!": ItemData(base_id + 506, IC.filler),
}

# I don't really have any ideas on what to give the other games for now.

item_table = {
    **progressive_games,
    **find_mii_upgrades,
    **pose_mii_upgrades,
    **fishing_upgrades,
    **tanks_items,
    **wiiplay_fillers,
}

ITEM_NAME_TO_ID = {name: data.id for name, data in item_table.items()}

def create_all_items(world:"WiiPlayWorld") -> None:
    itempool = []

    game_unlock_names = list(progressive_games.keys())
    world.random.shuffle(game_unlock_names)

    starting_count = world.options.starting_games.value
    starting_game_names = game_unlock_names[:starting_count]
    remaining_game_names = game_unlock_names[starting_count:]

    for name in starting_game_names:
        starting_item = world.create_item(name)
        world.multiworld.push_precollected(starting_item)

    for name in remaining_game_names:
        new_item = world.create_item(name)
        itempool.append(new_item)

    for item in find_mii_upgrades:
        new_item = world.create_item(item)
        itempool.append(new_item)

    for item in pose_mii_upgrades:
        new_item = world.create_item(item)
        itempool.append(new_item)

    for item in fishing_upgrades:
        new_item = world.create_item(item)
        itempool.append(new_item)

    for item in tanks_items:
        new_item = world.create_item(item)
        itempool.append(new_item)

    for item in wiiplay_fillers:
        new_item = world.create_item(item)
        itempool.append(new_item)

    # length of current itempool
    number_of_items = len(itempool)

    number_of_unfilled_locations = len(world.multiworld.get_unfilled_locations(world.player))
    needed_number_of_filler_items = number_of_unfilled_locations - number_of_items
    # create filler for the remaining needed

    itempool += [world.create_filler() for _ in range(needed_number_of_filler_items)]
    world.multiworld.itempool += itempool

    #world.push_precollected(world.create_item(item)

def get_random_filler_item_name(world: "WiiPlayWorld") -> str:
    names = [
        "Filler",
        "+10 Rally Bonus! - Table Tennis",
        "+2 Points! - Laser Hockey",
        "Feeling sleepy...",
        "Extra Life - Tanks!",
    ]
    weights = [84, 5, 5, 1, 5]
    return world.random.choices(names, weights=weights, k=1)[0]

def create_item_with_correct_classification(world: "WiiPlayWorld", name: str) -> WiiPlayItem:
    data = item_table[name]
    return WiiPlayItem(name, data.classification, data.id, world.player)