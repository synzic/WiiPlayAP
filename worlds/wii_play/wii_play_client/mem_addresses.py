class GameState:
    game_active_check = 0x91b3bac4    # Word
    file_loaded_check = 0x91b3bad4    # Word
    high_score_screen_state = 0x91b3bad8  # Word | 1=high score screen, 2=transitioning in, 4=default
    current_game = 0x91b3bae8         # Word | 0=Shooting Range, 1=Find Mii, 2=Table Tennis,
                                       #        3=Pose Mii, 4=Laser Hockey, 5=Billiards,
                                       #        6=Fishing, 7=Charge!, 8=Tanks!

    # For both, 0 = Not in state, 1 = In state
    pause_state = 0x804F0E60 # Word | Also counts menu state as paused
    menu_state = 0x80B20604 # Word | ONLY Menu state

class HighScores:
    shooting_range = 0x80842b58  # Word
    find_mii       = 0x80842b6c  # Word
    table_tennis   = 0x80842b80  # Word
    pose_mii       = 0x80842b94  # Word
    laser_hockey   = 0x80842ba8  # Word
    billiards      = 0x80842bbc  # Word
    fishing        = 0x80842bd0  # Word
    charge         = 0x80842be4  # Word
    tanks          = 0x80842bf8  # Word

class Medals:
    # Byte | 0x01=Bronze, 0x02=Silver, 0x03=Gold, 0x04=Platinum
    shooting_range = 0x80842c0c
    find_mii       = 0x80842c0d
    table_tennis   = 0x80842c0e
    pose_mii       = 0x80842c0f
    laser_hockey   = 0x80842c10
    billiards      = 0x80842c11
    fishing        = 0x80842c12
    charge         = 0x80842c13
    tanks          = 0x80842c14

class UnlockFlags:
    # Byte | Only reliable while in the minigame select menu
    shooting_range = 0x91d19d64
    find_mii       = 0x91d19d65
    table_tennis   = 0x91d19d66
    pose_mii       = 0x91d19d67
    laser_hockey   = 0x91d19d68
    billiards      = 0x91d19d69
    fishing        = 0x91d19d6a
    charge         = 0x91d19d6b
    tanks          = 0x91d19d6c

class TanksAddresses:
    current_mission = 0x91d27ffc   # Word | Stored as mission number + 1
    game_state      = 0x91d28020   # Word | 0x08=Mission Complete, 0x09=Mission Failed, etc.
    total_destroyed = 0x91d28100   # Word
    extra_lives     = 0x91d281fc   # Word

class ShootingRangeAddresses:
    level_completed_flag = 0x91e40de4  # Byte
    current_level         = 0x91e40de8  # Word
    game_state            = 0x91e40df4  # Word
    total_destroyed        = 0x91e40fd0  # Word

class BilliardsAddresses:
    total_shots       = 0x91b4502c   # Word
    fouls             = 0x91b45030   # Word
    max_sunk_one_shot = 0x91b45034   # Word
    final_score       = 0x91b7ba08   # Word

class FishingAddresses:
    score             = 0x91b6b09c   # Word
    total_caught      = 0x91b6b0b4   # Word
    game_state        = 0x91b6b12c   # Word | 0=before start, 2=fishing, 3=caught, 4=ending
    last_fish_name_length = 0x920c803f  # Byte | see fish-length table below
    last_fish_name = 0x920caaf9  # 30 bytes ASCII
"""
Current Length of Fish Name
0x07=Nibbler
0x09=Small Fry
0x0b=Touchy Fish
0x0c=Mystery Fish
0x0e=Plain Ol' Fish
0x10=King of the Pond
"""