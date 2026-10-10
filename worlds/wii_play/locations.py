from __future__ import annotations
from typing import TYPE_CHECKING, NamedTuple, Dict
from BaseClasses import Location, LocationProgressType as LPT
from . import items
from .options import *

if TYPE_CHECKING:
    from . import WiiPlayWorld

class WiiPlayLocation(Location):
    game = "Wii Play"

class LocData(NamedTuple):
    id: int
    location_type: LPT = LPT.DEFAULT

base_id = 0

shooting_range_locations = {
    "Shooting Range - Bronze Medal":        LocData(base_id + 1),
    "Shooting Range - Silver Medal":        LocData(base_id + 2),
    "Shooting Range - Give It Your Best Shot (Gold Medal)":          LocData(base_id + 3),
}

find_mii_locations = {
    "Find Mii - Bronze Medal":              LocData(base_id + 101),
    "Find Mii - Silver Medal":              LocData(base_id + 102),
    "Find Mii - Can You Find Mii? (Gold Medal)":                LocData(base_id + 103),
}

find_mii_challengesanity_locations = {
    "Find Mii - Find 2 Look Alikes":        LocData(base_id + 151),
    "Find Mii - Find 3 Look Alikes":        LocData(base_id + 152),
    "Find Mii - Find 4 Look Alikes":        LocData(base_id + 153),
    "Find Mii - Find 5 Look Alikes":        LocData(base_id + 154),
    "Find Mii - Find the Odd Mii Out":      LocData(base_id + 155),
    "Find Mii - Find the Fastest Mii":      LocData(base_id + 156),
    "Find Mii - Find the Mii You're Using": LocData(base_id + 157),
    "Find Mii - Find This Mii":             LocData(base_id + 158),
    "Find Mii - Find the Sleepyhead":       LocData(base_id + 159),
    "Find Mii - Find Your Favorite":        LocData(base_id + 160),
}

pose_mii_locations = {
    "Pose Mii - Bronze Medal":              LocData(base_id + 201),
    "Pose Mii - Silver Medal":              LocData(base_id + 202),
    "Pose Mii - You're Just A Poser (Gold Medal)":                LocData(base_id + 203),
}

pose_mii_missionsanity_locations = {
    "Pose Mii - Stage 1 Complete":  LocData(base_id + 251),
    "Pose Mii - Stage 2 Complete":  LocData(base_id + 252),
    "Pose Mii - Stage 3 Complete":  LocData(base_id + 253),
    "Pose Mii - Stage 4 Complete":  LocData(base_id + 254),
    "Pose Mii - Stage 5 Complete":  LocData(base_id + 255),
    "Pose Mii - Stage 6 Complete":  LocData(base_id + 256),
    "Pose Mii - Stage 7 Complete":  LocData(base_id + 257),
    "Pose Mii - Stage 8 Complete":  LocData(base_id + 258),
    "Pose Mii - Stage 9 Complete":  LocData(base_id + 259),
    "Pose Mii - Stage 10 Complete": LocData(base_id + 260),
    "Pose Mii - Stage 11 Complete": LocData(base_id + 261),
    "Pose Mii - Stage 12 Complete": LocData(base_id + 262),
    "Pose Mii - Stage 13 Complete": LocData(base_id + 263),
    "Pose Mii - Stage 14 Complete": LocData(base_id + 264),
    "Pose Mii - Stage 15 Complete": LocData(base_id + 265),
}

laser_hockey_locations = {
    "Laser Hockey - Bronze Medal": LocData(base_id + 301),
    "Laser Hockey - Silver Medal": LocData(base_id + 302),
    "Laser Hockey - Laser-Focused (Gold Medal)": LocData(base_id + 303),
}

table_tennis_locations = {
    "Table Tennis - Bronze Medal": LocData(base_id + 401),
    "Table Tennis - Silver Medal": LocData(base_id + 402),
    "Table Tennis - No Net Losses (Gold Medal)": LocData(base_id + 403),
}

fishing_locations = {
    "Fishing - Bronze Medal": LocData(base_id + 501),
    "Fishing - Silver Medal": LocData(base_id + 502),
    "Fishing - Out on the Lake (Gold Medal)": LocData(base_id + 503),
}

fishing_fishsanity_locations = {
    "Fishing - Catch Plain Ol' Fish": LocData(base_id + 551),
    "Fishing - Catch Nibbler": LocData(base_id + 552),
    "Fishing - Catch Touchy Fish": LocData(base_id + 553),
    "Fishing - Catch King of the Pond": LocData(base_id + 554),
    "Fishing - Catch Mystery Fish": LocData(base_id + 555),
}

billiards_locations = {
    "Billiards - Bronze Medal": LocData(base_id + 601),
    "Billiards - Silver Medal": LocData(base_id + 602),
    "Billiards - Pool Shark (Gold Medal)": LocData(base_id + 603),
}

billiards_foulsanity_locations = {
    "Billiards - Your 1st Foul": LocData(base_id + 651),
    "Billiards - Natural Fouler! (3 Fouls)": LocData(base_id + 652),
    "Billiards - Ooh, it's not looking good. (6 Fouls)": LocData(base_id + 653),
    "Billiards - How do you do it? (10 Fouls)": LocData(base_id + 654),
}

charge_locations = {
    "Charge! - Bronze Medal": LocData(base_id + 701),
    "Charge! - Silver Medal": LocData(base_id + 702),
    "Charge! - Cattle Rangling (Gold Medal)": LocData(base_id + 703),
}

tanks_locations = {
    "Tanks! - Bronze Medal": LocData(base_id + 1001),
    "Tanks! - Silver Medal": LocData(base_id + 1002),
    "Tanks! - Boom! (Gold Medal)": LocData(base_id + 1003),
}

tanks_missionsanity_locations = {
    f"Tanks! - Mission {n} Complete": LocData(base_id + 1100 + n)
    for n in range(1, 101)
}

platinum_medal_locations = {
    "Shooting Range - You're on Target! (Platinum Medal)":  LocData(base_id + 4),
    "Find Mii - Hey! You Found Mii! (Platinum Medal)":        LocData(base_id + 104),
    "Pose Mii - Picture-Perfect Posing (Platinum Medal)":        LocData(base_id + 204),
    "Laser Hockey - The Puck Stops Here (Platinum Medal)":    LocData(base_id + 304),
    "Table Tennis - Serve It Up (Platinum Medal)":    LocData(base_id + 404),
    "Fishing - But Her Aim Is Getting Better (Platinum Medal)":         LocData(base_id + 504),
    "Billiards - Take the Cue (Platinum Medal)":       LocData(base_id + 604),
    "Charge! - Special Delivery (Platinum Medal)":         LocData(base_id + 704),
    "Tanks! - Tank! Tank! Tank! (Platinum Medal)":          LocData(base_id + 1004),
}

location_table = {
    **shooting_range_locations,
    **find_mii_locations,
    **find_mii_challengesanity_locations,
    **pose_mii_locations,
    **pose_mii_missionsanity_locations,
    **laser_hockey_locations,
    **table_tennis_locations,
    **fishing_locations,
    **fishing_fishsanity_locations,
    **billiards_locations,
    **billiards_foulsanity_locations,
    **charge_locations,
    **tanks_locations,
    **tanks_missionsanity_locations,
    **platinum_medal_locations,
}

LOCATION_NAME_TO_ID = {location_name: data.id for location_name, data in location_table.items()}

def create_all_locations(world: "WiiPlayWorld") -> None:
    create_regular_locations(world)
    create_events(world)

def create_regular_locations(world: "WiiPlayWorld") -> None:
    shooting_range = world.get_region("Shooting Range")
    find_mii = world.get_region("Find Mii")
    pose_mii = world.get_region("Pose Mii")
    laser_hockey = world.get_region("Laser Hockey")
    table_tennis = world.get_region("Table Tennis")
    fishing = world.get_region("Fishing")
    billiards = world.get_region("Billiards")
    charge = world.get_region("Charge!")
    tanks = world.get_region("Tanks!")

    shooting_range.add_locations(
        get_location_names_with_ids(list(shooting_range_locations.keys())), WiiPlayLocation)
    find_mii.add_locations(
        get_location_names_with_ids(list(find_mii_locations.keys())), WiiPlayLocation)
    pose_mii.add_locations(
        get_location_names_with_ids(list(pose_mii_locations.keys())), WiiPlayLocation)
    laser_hockey.add_locations(
        get_location_names_with_ids(list(laser_hockey_locations.keys())), WiiPlayLocation)
    table_tennis.add_locations(
        get_location_names_with_ids(list(table_tennis_locations.keys())), WiiPlayLocation)
    fishing.add_locations(
        get_location_names_with_ids(list(fishing_locations.keys())), WiiPlayLocation)
    billiards.add_locations(
        get_location_names_with_ids(list(billiards_locations.keys())), WiiPlayLocation)
    charge.add_locations(
        get_location_names_with_ids(list(charge_locations.keys())), WiiPlayLocation)
    tanks.add_locations(
        get_location_names_with_ids(list(tanks_locations.keys())), WiiPlayLocation)

    # sanity options

    if world.options.find_mii_challengesanity:
        find_mii.add_locations(
            get_location_names_with_ids(list(find_mii_challengesanity_locations.keys())),
            WiiPlayLocation)

    if world.options.missionsanity in (Missionsanity.option_pose_mii, Missionsanity.option_both):
        pose_mii.add_locations(
            get_location_names_with_ids(list(pose_mii_missionsanity_locations.keys())),
            WiiPlayLocation)

    if world.options.fishsanity:
        fishing.add_locations(
            get_location_names_with_ids(list(fishing_fishsanity_locations.keys())),
            WiiPlayLocation)

    if world.options.foulsanity:
        billiards.add_locations(
            get_location_names_with_ids(list(billiards_foulsanity_locations.keys())),
            WiiPlayLocation)

    if world.options.missionsanity in (Missionsanity.option_tanks, Missionsanity.option_both):
        highest_mission = world.options.tanks_missionsanity.value
        gated_names = [
            f"Tanks! - Mission {mission} Complete"
            for mission in range(1, highest_mission + 1)
        ]
        tanks.add_locations(get_location_names_with_ids(gated_names), WiiPlayLocation)

    if world.options.platinum_medals:
        platinum_regions = {
            "Shooting Range - You're on Target! (Platinum Medal)": shooting_range,
            "Find Mii - Hey! You Found Mii! (Platinum Medal)": find_mii,
            "Pose Mii - Picture-Perfect Posing (Platinum Medal)": pose_mii,
            "Laser Hockey - The Puck Stops Here (Platinum Medal)": laser_hockey,
            "Table Tennis - Serve It Up (Platinum Medal)": table_tennis,
            "Fishing - But Her Aim Is Getting Better (Platinum Medal)": fishing,
            "Billiards - Take the Cue (Platinum Medal)": billiards,
            "Charge! - Special Delivery (Platinum Medal)": charge,
            "Tanks! - Tank! Tank! Tank! (Platinum Medal)": tanks,
        }
        for name, region in platinum_regions.items():
            region.add_locations(get_location_names_with_ids([name]), WiiPlayLocation)

def create_events(world: "WiiPlayWorld") -> None:
    main_menu = world.get_region("Main Menu")
    main_menu.add_event(
        "Victory!", "Victory!",
        location_type=WiiPlayLocation, item_type=items.WiiPlayItem,
    )

def get_location_names_with_ids(location_names: list[str]) -> dict[str, int]:
    return {location_name: location_table[location_name].id for location_name in location_names}