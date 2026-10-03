import asyncio
import logging
import traceback
from collections import deque
from typing import Dict, Set, Optional, Any

from .WiiPlayInterface import WiiPlayInterface, ConnectionState
from .mem_addresses import *

from NetUtils import ClientStatus, JSONMessagePart
from CommonClient import CommonContext, ClientCommandProcessor
from NetUtils import ClientStatus
from ..items import item_table
from ..locations import LOCATION_NAME_TO_ID

logger = logging.getLogger("Client")

ID_TO_NAME = {data.id: name for name, data in item_table.items()}
LOCATION_ID_TO_NAME = {loc_id: name for name, loc_id in LOCATION_NAME_TO_ID.items()}

id_to_name = {data.id: name for name, data in item_table.items()}
CLIENT_VERSION = "0.0.1"

class WiiPlayCommandProcessor(ClientCommandProcessor):
    ctx: "WiiPlayContext"

    def __init__(self, ctx: "WiiPlayContext"):
        super().__init__(ctx)


# noinspection PyDeprecation
# noinspection PyAttributeOutsideInit
class WiiPlayContext(CommonContext):
    tags = {"AP"}
    game = "Wii Play"
    game_interface: WiiPlayInterface
    command_processor = WiiPlayCommandProcessor
    connection_state = ConnectionState.DISCONNECTED
    items_handling = 0b111
    want_slot_data = True
    items_handled = set()

    def __init__(self, server_address: str, password: str):
        super().__init__(server_address, password)
        self.game_interface = WiiPlayInterface(logger)

        # Unlocked Items Sets
        self.unlocked_games: set[str] = set()

        # Slot Data Stuff
        self.goal: int = 0

    def log_colour(self, text: str, color: str):
        """Logs the message in full color"""

        if self.ui is not None:
            message: JSONMessagePart = {"type": "color", "text": text, "color": color.lower()}
            self.ui.print_json([message])

    def on_package(self, cmd: str, args: dict):
        """This function handles the packets coming from the AP Server, see the network_package.md in ap docs"""

        # We use super().on_package(cmd, args) to inherit the default behaviour from a text client
        super().on_package(cmd, args)

        if cmd == "Connected":
            ap_locations_checked = args["checked_locations"]
            self.locations_checked.update(ap_locations_checked)

            self.slot_data = args.get("slot_data", {})

            self.goal = self.slot_data.get("goal")

    def ready_to_handle(self) -> bool:
        """Evaluates whether the game is ready to receive items that effect the player in game
        Items like Menu unlocks do not need to check for this"""

        is_paused = self.game_interface.is_paused()
        in_menu = self.game_interface.in_menu()

        return not is_paused and not in_menu

    async def handle_received_items(self):
        """Handles the received non-consumable items

        Adds them to different lists for specific functions to take over unlock handling"""


        games = ("Shooting Range", "Find Mii", "Table Tennis", "Pose Mii",
                 "Laser Hockey", "Billiards", "Fishing", "Charge!", "Tanks!")

        for index, network_item in enumerate(self.items_received):
            item_id = network_item.item
            item_name: str | None = id_to_name.get(item_id)
            if index not in self.items_handled:
                if item_name is None:
                    continue

                if item_name.removesuffix(" Unlock") in games:
                    self.unlocked_games.add(item_name)


    async def handle_unlocked_games(self):
        """Handles the unlocking of games

        A 2D array is used to link the game name to its unlock address, from there it will loop through the array and
        check if the game is unlocked. If it's not unlocked it will force the value to be 0, if it is, it'll be 1.

        This blocks the game from unlocking the game as well."""

        mode_address_pair = [
            ["Shooting Range", UnlockFlags.shooting_range],
            ["Find Mii", UnlockFlags.find_mii],
            ["Table Tennis", UnlockFlags.table_tennis],
            ["Pose Mii", UnlockFlags.pose_mii],
            ["Laser Hockey", UnlockFlags.laser_hockey],
            ["Billiards", UnlockFlags.billiards],
            ["Fishing", UnlockFlags.fishing],
            ["Charge!", UnlockFlags.charge],
            ["Tanks!", UnlockFlags.tanks]
        ]

        for pair in mode_address_pair:
            game = pair[0]
            unlock_addr = pair[1]

            # If we have the game, set the value to 1, else 0
            value = 1 if game in self.unlocked_games else 0

            self.game_interface.dolphin_client.write_word(unlock_addr, value)