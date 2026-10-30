import asyncio
import logging
import traceback
from collections import deque
from typing import Dict, Set, Optional, Any

from .WiiPlayInterface import WiiPlayInterface, ConnectionState
from .mem_addresses import *

from NetUtils import ClientStatus, JSONMessagePart

tracker_loaded = False
try:
    from worlds.tracker.TrackerClient import TrackerGameContext as SuperContext, \
        TrackerCommandProcessor as SuperCommandProcessor

    tracker_loaded = True
except ModuleNotFoundError:
    from CommonClient import CommonContext as SuperContext, ClientCommandProcessor as SuperCommandProcessor
from NetUtils import ClientStatus

from ..items import item_table, wiiplay_fillers
from ..locations import LOCATION_NAME_TO_ID

logger = logging.getLogger("Client")

ID_TO_NAME = {data.id: name for name, data in item_table.items()}
LOCATION_ID_TO_NAME = {loc_id: name for name, loc_id in LOCATION_NAME_TO_ID.items()}

CONSUMABLE_STORAGE_CATEGORY = "wii_play_consumables"
LOCATION_STORAGE_CATEGORY = "wii_play_locations"
HIGH_SCORE_STORAGE_CATEGORY = "wii_play_high_scores" 
CLIENT_VERSION = "0.0.2"
COMPATIBLE_VERSIONS = ("0.0.1",)

GAMES = ("Shooting Range", "Find Mii", "Table Tennis", "Pose Mii",
         "Laser Hockey", "Billiards", "Fishing", "Charge!", "Tanks!")

MEDAL_ATTR = {g: g.lower().replace(" ", "_").rstrip("!") for g in GAMES}

def _build_medal_location_ids():
    suffixes = {1: "Bronze Medal", 2: "Silver Medal", 3: "(Gold Medal)", 4: "(Platinum Medal)"}
    result = {}
    for game in GAMES:
        for tier, suffix in suffixes.items():
            for name, loc_id in LOCATION_NAME_TO_ID.items():
                if name.startswith(f"{game} - ") and name.endswith(suffix):
                    result[(game, tier)] = loc_id
    return result

MEDAL_LOCATION_IDS = _build_medal_location_ids()

FOUL_LOCATIONS = {
    1: "Billiards - Your 1st Foul",
    3: "Billiards - Natural Fouler! (3 Fouls)",
    6: "Billiards - Ooh, it's not looking good. (6 Fouls)",
    10: "Billiards - How do you do it? (10 Fouls)",
}

FISH_LOCATIONS = {
    0x07: "Fishing - Catch Nibbler",
    0x0b: "Fishing - Catch Touchy Fish",
    0x0c: "Fishing - Catch Mystery Fish",
    0x0e: "Fishing - Catch Plain Ol' Fish",
    0x10: "Fishing - Catch King of the Pond",
}

status_messages = {
    ConnectionState.DISCONNECTED: "Disconnected",
    ConnectionState.CONNECTED: "Connected but no specific state found...",
    ConnectionState.IN_MENU: "In Menu",
    ConnectionState.SHOOTING_RANGE: "In Shooting Range",
    ConnectionState.FIND_MII: "In Find Mii",
    ConnectionState.TABLE_TENNIS: "In Table Tennis",
    ConnectionState.POSE_MII: "In Pose Mii",
    ConnectionState.LASER_HOCKEY: "In Laser Hockey",
    ConnectionState.BILLIARDS: "In Billiards",
    ConnectionState.FISHING: "In Fishing",
    ConnectionState.CHARGE: "In Charge!",
    ConnectionState.TANKS: "In Tanks!",
}

class WiiPlayCommandProcessor(SuperCommandProcessor):
    ctx: "WiiPlayContext"

    def __init__(self, ctx: "WiiPlayContext"):
        super().__init__(ctx)

    def _cmd_status(self):
        """Display the current dolphin connection status."""
        logger.info(f"Connection Status: {status_messages[self.ctx.connection_state]}")

    def _cmd_debug_mode(self):
        """Toggle client debugging on and off (Default off)"""
        if not self.ctx.DEBUGGING:
            self.ctx.DEBUGGING = True
            logger.info("Debugging on")
        else:
            self.ctx.DEBUGGING = False
            logger.info("Debugging off")


# noinspection PyDeprecation
# noinspection PyAttributeOutsideInit
class WiiPlayContext(SuperContext):
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

        self.start_process = True
        self.game_session_active = False

        self.queued_consumable_indices: Set[int] = set()
        self.handled_consumable_indices: Set[int] = set()
        # Set when a Get/SetReply for handled consumables has been applied this session.
        self._consumables_load_event = asyncio.Event()

        self.filler_to_give = deque()
        self.traps_to_give = deque()

        self.DEBUGGING: bool = False
        self.last_debug_messages = deque(maxlen=5)
        self.medal_levels = {}
        self.tanks_100_cleared = False
        self.goal_sent = False
        self.last_error_message = None
        self.saved_high_scores: dict[str, int] = {}
        self._high_scores_load_event = asyncio.Event()
        self.progress_restored = False
        self.restore_warned = False
        self.guest_warned = False


    def debug_log(self, message: str) -> None:
        """Sends messages to the client if debugging is on"""

        if self.DEBUGGING:
            if message not in self.last_debug_messages:
                self.last_debug_messages.append(message)
                logger.info(f"[Wii Play Debug] {message}")

    def update_connection_status(self):
        self.connection_state = self.game_interface.get_connection_state()

    def make_gui(self):
        ui = super().make_gui()
        ui.base_title = f"Archipelago Wii Play Client (Version {CLIENT_VERSION}) | AP Version"
        return ui

    async def server_auth(self, password_requested: bool = False):
        if password_requested and not self.password:
            await super(WiiPlayContext, self).server_auth(password_requested)
        await self.get_username()
        await self.send_connect()

    async def disconnect(self, allow_autoreconnect: bool = False):
        await super().disconnect(allow_autoreconnect)
        self.game_interface.dolphin_client.disconnect()
        self.clear_local_item_state()
        self.clear_local_location_state()

    def clear_local_item_state(self):
        self.unlocked_games.clear()
        self.progress_restored = False
        self.saved_high_scores.clear()
        self._high_scores_load_event.clear()

    def clear_local_location_state(self):
        self.checked_locations.clear()
        self.locations_checked.clear()


    def log_colour(self, text: str, color: str):
        """Logs the message in full color"""

        if self.ui is not None:
            message: JSONMessagePart = {"type": "color", "text": text, "color": color.casefold()}
            self.ui.print_json([message])

    async def mark_consumable_handled(self, item_index: Optional[int]) -> None:
        """Mark a consumable (1 time or trap) item as handled so the client doesn't use it again"""

        if item_index is None:
            return

        self.queued_consumable_indices.discard(item_index)
        self.handled_consumable_indices.add(item_index)
        # Save after the effect is applied so a disconnect mid-queue doesn't eat the item.
        await self.save_handled_consumables()
        self.debug_log(f"Saved handled consumable index {item_index}")

    # --- Consumable persistence (filler + traps) ---
    # These are one-shot items tracked by AP received-item index and saved to server storage
    # so reconnects don't hand them out again. Key is scoped per slot.

    @property
    def high_score_storage_key(self) -> Optional[str]:
        """Returns a key which is linked to the game and the slot name"""

        if self.seed is None or self.slot is None:
            return None
        return f"{HIGH_SCORE_STORAGE_CATEGORY}_{self.slot}"

    async def load_high_scores(self)-> None:
        key = self.high_score_storage_key
        if key is None:
            return
        self._high_scores_load_event.clear()
        await self.send_msgs([{"cmd": "Set", 
                               "key": key, 
                               "default": {}, 
                               "want_reply": False,
                               "operations": [{"operation": "default", "value": {}}]}])
        self.set_notify(key)
        await self.send_msgs([{"cmd": "Get",
                               "keys": [key]}])
        
    def _on_high_scores_update(self, value: Any) -> None:
        if isinstance(value, dict):
            for game, score in value.items():
                self.saved_high_scores[game] = max(self.saved_high_scores.get(game, 0), int(score))
        self._high_scores_load_event.set()

    async def save_high_scores(self) -> None:
        key = self.high_score_storage_key
        if key is None:
            return
        await self.send_msgs([{"cmd": "Set",
                          "key": key,
                          "default": {},
                          "want_reply": False,
                          "operations": [{"operation": "replace", "value": dict(self.saved_high_scores)}]}])

    @property
    def consumable_storage_key(self) -> Optional[str]:
        """Returns a key which is linked to the game and the slot name"""

        if self.seed is None or self.slot is None:
            return None
        return f"{CONSUMABLE_STORAGE_CATEGORY}_{self.slot}"

    def _on_consumables_storage_update(self, value: Any) -> None:
        """Apply server storage for handled filler/trap indices and drop any stale queue entries."""
        if value is None:
            self.handled_consumable_indices = set()
        elif isinstance(value, list):
            self.handled_consumable_indices = {int(index) for index in value}
        else:
            logger.warning(f"Unexpected handled consumables value type: {type(value)}")
            return

        handled = self.handled_consumable_indices
        self.filler_to_give = deque(
            entry for entry in self.filler_to_give
            if not (isinstance(entry, tuple) and entry[0] in handled)
        )
        self.traps_to_give = deque(
            entry for entry in self.traps_to_give
            if not (isinstance(entry, tuple) and entry[0] in handled)
        )
        self.queued_consumable_indices -= handled
        self._consumables_load_event.set()
        self.debug_log(f"Loaded {len(self.handled_consumable_indices)} handled consumables")

    async def save_handled_consumables(self) -> None:
        """Saves the handled consumables to the AP Data Storage to retrieve upon future connection"""

        key = self.consumable_storage_key
        if key is None:
            return
        await self.send_msgs([{
            "cmd": "Set",
            "key": key,
            "default": [],
            "want_reply": True,
            "operations": [{
                "operation": "replace",
                "value": sorted(self.handled_consumable_indices)
            }]
        }])
        self.debug_log(f"Saving handled consumables: {sorted(self.handled_consumable_indices)}")

    async def load_handled_consumables(self, initialise: bool = False) -> None:
        """Load handled filler/trap indices from AP storage before queuing ReceivedItems."""
        key = self.consumable_storage_key
        if key is None or self._consumables_load_event.is_set():
            return

        self._consumables_load_event.clear()
        if initialise:
            # First connect for this seed/slot: create the key if missing, then subscribe to updates.
            await self.send_msgs([{
                "cmd": "Set",
                "key": key,
                "default": [],
                "want_reply": False,
                "operations": [{"operation": "default", "value": 0}],
            }])
            self.set_notify(key)
        else:
            await self.send_msgs([{"cmd": "Get", "keys": [key]}])

        try:
            await asyncio.wait_for(self._consumables_load_event.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            logger.warning("Timed out loading handled consumables from server storage")
            self._consumables_load_event.set()

    async def _handle_received_items_consumables(self, args: dict) -> None:
        """Gets called when the client receives a ReceivedItems package, handles both consumables and
        regular items"""

        # Wait for storage before queuing — otherwise reconnects re-fire already-handled items.
        await self.load_handled_consumables()

        start_index = args["index"]

        self.debug_log(
            f"ReceivedItems packet start={start_index}, count={len(args['items'])}, "
            f"handled_consumables={len(self.handled_consumable_indices)}"
        )

        for offset, item in enumerate(args["items"]):
            item_index = start_index + offset

            if item_index in self.handled_consumable_indices or item_index in self.queued_consumable_indices:
                self.debug_log(f"Skipping already queued/handled consumable index {item_index}")
                continue

            item_id = item.item if hasattr(item, "item") else item[0]
            item_name = ID_TO_NAME.get(item_id)

            if not item_name:
                self.debug_log(f"Skipping unknown item id {item_id} at index {item_index}")
                continue

            if item_name in wiiplay_fillers:
                self.filler_to_give.append((item_index, item_name))
                self.queued_consumable_indices.add(item_index)
                logger.info(f"Queued filler: {item_name}")
                self.debug_log(f"Filler queue size is now {len(self.filler_to_give)}")

            elif "Trap" in item_name:
                self.traps_to_give.append((item_index, item_name))
                self.queued_consumable_indices.add(item_index)
                logger.info(f"Queued trap: {item_name}")
                self.debug_log(f"Trap queue size is now {len(self.traps_to_give)}")

        await self.handle_received_items()

    def on_package(self, cmd: str, args: dict):
        """This function handles the packets coming from the AP Server, see the network_package.md in ap docs"""

        # We use super().on_package(cmd, args) to inherit the default behaviour from a text client
        super().on_package(cmd, args)

        if cmd == "Connected":
            ap_locations_checked = args["checked_locations"]
            self.locations_checked.update(ap_locations_checked)
            self.seed = self.server_seed_name

            self.slot_data = args.get("slot_data", {})

            self.goal = self.slot_data.get("goal")
            self.medal_hunt = self.slot_data.get("medal_hunt")
            self.plat_medals = self.slot_data.get("plat_medals")
            self.missionsanity = self.slot_data.get("missionsanity")
            self.tanks_missionsanity = self.slot_data.get("tanks_missionsanity")
            self.find_mii_challengesanity = self.slot_data.get("find_mii_challengesanity")
            self.fishsanity = self.slot_data.get("fishsanity")
            self.foulsanity = self.slot_data.get("foulsanity")
            self.starting_games = self.slot_data.get("starting_games")

            generation_version = self.slot_data.get("version", "0.0.1")

            # Client World mismatch handler
            if generation_version in COMPATIBLE_VERSIONS:
                logger.info(
                    f"This seed was generated on {generation_version}, however client version {CLIENT_VERSION} is compatible!"
                )
            elif CLIENT_VERSION != generation_version:
                logger.error(
                    f"\n=========================================\n"
                    f"VERSION MISMATCH DETECTED!\n"
                    f"Seed was generated on version: {generation_version}\n"
                    f"Your Client version: {CLIENT_VERSION}. This version is not compatible with version generated on!\n"
                    f"Please update, downgrade your client, or regenerate the seed as things may break!\n"
                    f"========================================="
                )
            else:
                logger.info(f"Version check passed! (v{CLIENT_VERSION})")

            asyncio.create_task(self.load_handled_consumables(initialise=True))
            asyncio.create_task(self.load_high_scores())

        elif cmd in ("Retrieved", "SetReply"):
            consumable_key = self.consumable_storage_key
            score_key = self.high_score_storage_key

            if cmd == "Retrieved":
                keys_dict = args.get("keys", {})

                if consumable_key and consumable_key in keys_dict:
                    self._on_consumables_storage_update(args["keys"][consumable_key])

                if score_key and score_key in keys_dict:
                    self._on_high_scores_update(keys_dict[score_key])

            elif cmd == "SetReply":
                if consumable_key and args.get("key") == consumable_key:
                    self._on_consumables_storage_update(args.get("value"))

                if score_key and args.get("key") == score_key:
                    self._on_high_scores_update(args.get("value"))

        elif cmd == "ReceivedItems":
            asyncio.create_task(self._handle_received_items_consumables(args))



    def reset_game_session_state(self, game_active: bool = False) -> None:
        """Reset runtime-only state when the game process/title exits or restarts."""
        self.start_process = True
        self.game_session_active = game_active
        self.progress_restored = False

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
            item_name: str | None = ID_TO_NAME.get(item_id)
            if index not in self.items_handled:
                if item_name is None:
                    continue

                if item_name in games:
                    self.unlocked_games.add(item_name)


    async def handle_unlocked_games(self):
        """Handles the unlocking of games

        A 2D array is used to link the game name to its unlock address, from there it will loop through the array and
        check if the game is unlocked. If it's not unlocked it will force the value to be 0, if it is, it'll be 1.

        This blocks the game from unlocking the game as well."""

        value_to_game = {
            0: "Shooting Range",
            1: "Find Mii",
            2: "Table Tennis",
            3: "Pose Mii",
            4: "Laser Hockey",
            5: "Billiards",
            6: "Fishing",
            7: "Charge!",
            8: "Tanks!",
            9: None
        }

        current_selected = self.game_interface.dolphin_client.read_byte(GameState.cursor_selected)
        if current_selected not in value_to_game:
            return

        if current_selected != 9 and value_to_game[current_selected] not in self.unlocked_games:
            # Try to move to next available game
            to_move_to = next(
                (value for value, game in value_to_game.items() if game in self.unlocked_games and value > current_selected),
                None
            )

            if to_move_to is None:
                # Reset and find a new number, no new games are available
                to_move_to = next(
                    (value for value, game in value_to_game.items() if game in self.unlocked_games),
                    None
                )

            if to_move_to is not None:
                self.game_interface.dolphin_client.write_byte(GameState.cursor_selected, to_move_to)
            else:
                self.game_interface.dolphin_client.write_byte(GameState.cursor_selected, 8)


    async def dolphin_sync_task(self):
        """The main loop managing the connection to Dolphin and game-state logic routing"""

        while not self.exit_event.is_set():
            try:
                # Handle initial connection hook
                if not self.game_interface.dolphin_client.is_hooked():
                    if self.game_session_active:
                        self.reset_game_session_state(game_active=True)
                    await self.game_interface.dolphin_client.attempt_to_hook()

                if self.game_interface.dolphin_client.is_hooked():
                    if not self.game_interface.dolphin_client.check_region():
                        self.game_interface.dolphin_client.check_region()
                        await asyncio.sleep(1)
                        continue

                if not self.server or not self.server.socket or self.server.socket.closed:
                    message = "Waiting for player to connect to Archipelago server..."
                    self.start_process = True
                    if self.last_error_message != message:
                        logger.info(message)
                        self.last_error_message = message
                    await asyncio.sleep(1)
                    continue

                if not self.slot:
                    await asyncio.sleep(1)
                    continue

                if self.start_process:
                    self.start_process = False

                self.last_error_message = None

                # Route Game State Execution
                self.update_connection_status()

                if self.game_interface.dolphin_client.is_hooked():

                    if self.connection_state == ConnectionState.IN_MENU:
                        await self.handle_in_menu()
                    elif self.connection_state in (ConnectionState.SHOOTING_RANGE, ConnectionState.FIND_MII,
                                                   ConnectionState.TABLE_TENNIS, ConnectionState.POSE_MII,
                                                   ConnectionState.LASER_HOCKEY, ConnectionState.BILLIARDS,
                                                   ConnectionState.FISHING, ConnectionState.CHARGE, ConnectionState.TANKS):
                        await self.handle_in_game()
                    else:
                        await asyncio.sleep(1)
                        continue

                await asyncio.sleep(0.1)

            except Exception as e:
                if "Dolphin" in str(e):
                    logger.error(f"Dolphin Connection Error: {e}")
                    self.update_connection_status()
                    self.update_connection_status()
                else:
                    logger.error(f"Sync Task Error:\n{traceback.format_exc()}")
                await asyncio.sleep(3)

    async def handle_in_menu(self):
        await self.handle_unlocked_games()
        if not await self.guest_check():
            return
        if not self.progress_restored:
            if not await self.restore_progress():
                return
        await self.check_medals()
        await self.check_high_scores()
        await self.check_goal()
        await self.process_queue(self.filler_to_give, self.apply_filler)

    async def handle_in_game(self):
        if not await self.guest_check():
            return
        if not self.progress_restored:
            if not self.restore_warned:
                logger.info("Progress will not be synced until you return to the main menu.")
                self.restore_warned = True
            return
        await self.check_medals()
        await self.check_high_scores()
        if self.connection_state == ConnectionState.BILLIARDS:
            await self.check_fouls()
        elif self.connection_state == ConnectionState.TANKS:
            await self.check_tanks()
        elif self.connection_state == ConnectionState.FISHING:
            await self.check_fish()
        await self.check_goal()
        if self.ready_to_handle():
            await self.process_queue(self.filler_to_give, self.apply_filler)

    async def send_new_checks(self, location_ids: set[int]) -> None:
        # only send checks that aren't already checked
        new = {
            loc for loc in location_ids
            if loc in self.missing_locations and loc not in self.locations_checked
        }
        if not new:
            return
        self.locations_checked.update(new)
        await self.send_msgs([{"cmd": 'LocationChecks', "locations": tuple(new)}])

    def read_medal_levels(self) -> None:
        # the medal bytes only store the highest tier, having gold means you have silver and bronze
        client = self.game_interface.dolphin_client
        levels = {}
        for game in GAMES:
            value = client.read_byte(getattr(Medals, MEDAL_ATTR[game]))
            levels[game] = value if 0 <= value <= 4 else 0
        return levels

    async def check_medals(self) -> None:
        levels = self.read_medal_levels()
        self.medal_levels = levels

        ids = set()
        for game, level in levels.items():
            for tier in range(1, level + 1):
                loc = MEDAL_LOCATION_IDS.get((game, tier))
                if loc is not None:
                    ids.add(loc)
        await self.send_new_checks(ids)

    async def check_goal(self) -> None:
        if self.goal_sent or self.goal is None:
            return

        levels = self.medal_levels
        have_all = len(levels) == len(GAMES)
        plat = bool(self.plat_medals)

        if self.goal == 0:
            done = have_all and all(level >= 3 for level in levels.values())
        elif self.goal == 1:
            done = have_all and all(level >= 4 for level in levels.values())
        elif self.goal == 2:
            cap = 4 if plat else 3
            done = sum(min(level, cap) for level in levels.values()) >= self.medal_hunt
        elif self.goal == 3:
            done = self.tanks_100_cleared
        else:
            done = False

        if done:
            self.goal_sent = True
            logger.info("Wii played (Goal)!")
            await self.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])

    async def check_tanks(self) -> None:
        client = self.game_interface.dolphin_client
        state = client.read_word(TanksAddresses.game_state)
        if state not in (0x06, 0x08): #0x06 tank won, 0x08 mission complete
            return
        mission = client.read_word(TanksAddresses.current_mission) + 1  # stored as mission - 1
        if not 1 <= mission <= 100:
            return

        name = f"Tanks! - Mission {mission} Complete"
        await self.send_new_checks({LOCATION_NAME_TO_ID[name]})
        if mission == 100:
            self.tanks_100_cleared = True

    async def check_fouls(self) -> None:
        fouls = self.game_interface.dolphin_client.read_word(BilliardsAddresses.fouls)
        ids = {LOCATION_NAME_TO_ID[name] for need, name in FOUL_LOCATIONS.items() if fouls >= need}
        await self.send_new_checks(ids)

    async def check_fish(self) -> None:
        client = self.game_interface.dolphin_client
        if client.read_word(FishingAddresses.game_state) != 3:
            return
        length = client.read_byte(FishingAddresses.last_fish_name_length)
        name = FISH_LOCATIONS.get(length)
        if name is not None:
            await self.send_new_checks({LOCATION_NAME_TO_ID[name]})

    async def apply_filler(self, name: str) -> bool:
        client = self.game_interface.dolphin_client

        if name == "Filler":
            return True

        if name == "Extra Life - Tanks!":
            if self.connection_state != ConnectionState.TANKS:
                return False
            lives = client.read_word(TanksAddresses.extra_lives)
            client.write_word(TanksAddresses.extra_lives, lives + 1)
            return True

        if name == "+10 Rally Bonus! - Table Tennis":
            if self.connection_state != ConnectionState.TABLE_TENNIS:
                return False
            rally_bonus = client.read_word(TennisAddresses.current_rally)
            if rally_bonus < 1:
                return False
            client.write_word(TennisAddresses.current_rally, rally_bonus + 20)
            return True

        if name == "+1 Point! - Laser Hockey":
            if self.connection_state != ConnectionState.LASER_HOCKEY:
                return False
            hockey_score = client.read_word(HockeyAddresses.hockey_score)
            client.write_word(HockeyAddresses.hockey_score, hockey_score + 1)
            return True

        if name == "Feeling sleepy...":
            if self.connection_state != ConnectionState.IN_MENU:
                return False
            current_menu_pose = client.read_word(SleepyAddresses.menu_pose_1)
            if current_menu_pose != 0:
                return False
            async def sleepy_loop():
                while self.connection_state == ConnectionState.IN_MENU:
                    client.write_word(SleepyAddresses.menu_pose_1, 7)
                    client.write_word(SleepyAddresses.menu_pose_2, 7)
                    await asyncio.sleep(0.02)

            asyncio.create_task(sleepy_loop())
            return True
        return False

    async def process_queue(self, queue, apply_fn) -> None:
        for entry in list(queue):
            index, name = entry
            if await apply_fn(name):
                queue.remove(entry)
                await self.mark_consumable_handled(index)

    def using_guest_mii(self) -> bool:
        client = self.game_interface.dolphin_client
        single_player = client.read_word(RequiredAddreses.player_count_check) == 1
        guest = 1 <= client.read_word(RequiredAddreses.last_selected_mii) <= 6
        return single_player and guest

    async def guest_check(self) -> bool:
        if self.using_guest_mii():
            self.guest_warned = False
            return True
        if not self.guest_warned:
            logger.warning("Wii Play requires single player mode and a Guest Mii! Checks will not send until you switch.")
            self.guest_warned = True
        self.progress_restored = False
        return False

    def medal_levels_from_ap(self) -> dict[str, int]:
        checked = self.checked_locations | self.locations_checked
        levels = {}
        for game in GAMES:
            level = 0
            for tier in range(1,5):
                if MEDAL_LOCATION_IDS.get((game, tier)) in checked:
                    level = tier
            levels[game] = level
        return levels

    async def restore_progress(self) -> bool:
        if not self._high_scores_load_event.is_set():
            return False
        client = self.game_interface.dolphin_client
        levels = self.medal_levels_from_ap()
        for game in GAMES:
            attr = MEDAL_ATTR[game]
            client.write_byte(getattr(Medals, attr), levels[game])
            client.write_word(getattr(HighScores, attr), self.saved_high_scores.get(game, 0))
        self.progress_restored = True
        logger.info("Medals and high scores have been restored from Archipelago.")
        return True

    async def check_high_scores(self) -> None:
        client = self.game_interface.dolphin_client
        changed = False
        for game in GAMES:
            score = client.read_word(getattr(HighScores, MEDAL_ATTR[game]))
            if score > self.saved_high_scores.get(game, 0):
                self.saved_high_scores[game] = score
                changed = True
        if changed:
            await self.save_high_scores()