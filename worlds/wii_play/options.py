from dataclasses import dataclass
from Options import *

class GoalType(Choice):
    """Choose your win condition:
    - Gold Medals: Earn a Gold medal in all 9 minigames.
    - Platinum Medals: Earn a Platinum medal in all 9 minigames (Platinum Medals must be enabled).
    - Medal Hunt: Collect a target number of medals set in Medal Hunt Amount.
    - Tanks: Defeat Mission 100 in Tanks!.
    """
    display_name = "Goal Type"
    option_gold_medals = 0
    option_platinum_medals = 1
    option_medal_hunt = 2
    option_tanks_100 = 3
    default = 0

class MedalHunt(Range):
    """Choose how many medals you need to get to goal if goal type is Medal Hunt."""
    display_name = "Medal Hunt Amount"
    range_start = 10
    range_end = 36
    default = 20

class PlatinumMedals(Toggle):
    """Choose whether you want Platinum medals enabled or disabled.

    (WARNING: These medals are **very** hard to collect! Your gameplay has to be near perfect!)
    """
    display_name = "Platinum Medals"

class Missionsanity(Choice):
    """Adds a location check for every individual mission / stage.

    This can add checks to Pose Mii, and Tanks!

    (WARNING: Tanks! Missionsanity can add up to 100 checks!)
    """
    display_name = "Missionsanity"
    option_pose_mii = 0
    option_tanks = 1
    option_both = 2
    option_none = 3
    default = 3

class TanksMissionsanity(Range):
    """If Tanks! Missionsanity is enabled, which Tanks! mission should be the highest mission that has checks?"""
    display_name = "Tanks Missionsanity"
    range_start = 20
    range_end = 100
    default = 30

class FindMiiChallengesanity(Toggle):
    """Toggle extra checks for challenges in Find Mii."""
    display_name = "Find Mii Challengesanity"

class Fishsanity(Toggle):
    """Adds checks for each type of fish in Fishing (excluding Small Fry). How wonderful!"""
    display_name = "Fishsanity"

class Foulsanity(Toggle):
    """Adds checks for committing fouls in Billards"""
    display_name = "Foulsanity"

class StartingGames(Range):
    """How many games are unlocked from the start."""
    display_name = "Starting Games Count"
    range_start = 1
    range_end = 3
    default = 2

wii_play_option_groups = [
    OptionGroup("Goal", [
        GoalType,
        MedalHunt,
    ]),
    OptionGroup("Checks", [
        PlatinumMedals,
        Missionsanity,
        TanksMissionsanity,
        FindMiiChallengesanity,
        Fishsanity,
        Foulsanity,
    ]),
    OptionGroup("Starting Games", [
        StartingGames,
    ])
]

@dataclass
class WiiPlayOptions(PerGameCommonOptions):
    goal_type: GoalType
    medal_hunt: MedalHunt
    platinum_medals: PlatinumMedals
    missionsanity: Missionsanity
    tanks_missionsanity: TanksMissionsanity
    find_mii_challengesanity: FindMiiChallengesanity
    fishsanity: Fishsanity
    foulsanity: Foulsanity
    starting_games: StartingGames

    start_inventory_from_pool: StartInventoryPool
