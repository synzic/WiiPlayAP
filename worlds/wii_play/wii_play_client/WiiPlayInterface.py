from .dolphin_connection import *
from .mem_addresses import *
from enum import Enum

class ConnectionState(Enum):
    DISCONNECTED = 0
    CONNECTED = 1
    IN_MENU = 2

class WiiPlayInterface:
    dolphin_client: DolphinClient
    connection_state: str
    logger: Logger

    def __init__(self, logger: Logger):
        self.logger = logger
        self.dolphin_client = DolphinClient(logger)


    def get_current_game(self) -> str | None:
        """Returns the string of the current game

        Returns None if no game active"""

        in_menu = bool(self.dolphin_client.read_word(GameState.menu_state))

        if not in_menu:
            current_game = self.dolphin_client.read_word(GameState.current_game)

            int_to_game = {
                0: "Shooting Range",
                1: "Find Mii",
                2: "Table Tennis",
                3: "Pose Mii",
                4: "Laser Hockey",
                5: "Billiards",
                6: "Fishing",
                7: "Charge!",
                8: "Tanks!"
            }

            return int_to_game[current_game]

        return None

    def in_menu(self) -> bool:
        """Returns a bool depending on if the player is in the menu"""

        return bool(self.dolphin_client.read_word(GameState.menu_state))


    def is_paused(self) -> bool:
        """Returns a bool depending on if the player is paused and NOT in the menu"""

        in_menu = bool(self.dolphin_client.read_word(GameState.menu_state))
        is_paused = bool(self.dolphin_client.read_word(GameState.pause_state))

        return is_paused and not in_menu