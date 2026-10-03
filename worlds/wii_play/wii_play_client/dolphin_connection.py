from logging import Logger
from typing import Any
import psutil
import dolphin_memory_engine as dme
import asyncio

GAME_VERSION = None

# I'm repurposing a lot of code from my goat ElectroStarz. Thanks :)

STANDARD_DOLPHIN_PROCESS_NAMES = frozenset({
    "dolphin",
    "dolphinqt2",
    "dolphin-emu",
    "dolphin-emu-qt2",
    "dolphin-emu-wx",
})

FORK_DOLPHIN_PROCESS_NAMES = frozenset({
    "slippi dolphin",
    "slippi-dolphin",
    "slippi_dolphin",
    "dolphinmpn",
    "dolphin mpn",
    "dolphin-mpn",
    "primehack",
    "ishiiruka",
})

SUPPORTED_DOLPHIN_PROCESS_NAMES = STANDARD_DOLPHIN_PROCESS_NAMES | FORK_DOLPHIN_PROCESS_NAMES

class DolphinException(Exception):
    pass

class DolphinClient:
    def __init__(self, logger: Logger):
        self.dme = dme
        self.logger = logger
        self.attempt = 1
        self.told_region = False
        self.told_fork_warning = False


    @staticmethod
    def get_running_dolphin_processes() -> list[str]:
        """Return the names of running supported Dolphin processes."""
        running_processes = []

        # Iterate through all running processes across the OS
        for proc in psutil.process_iter(['name']):
            try:
                process_name = proc.info['name']
                if process_name is None:
                    continue

                # Windows adds .exe; normalise it and compare case-insensitively
                # so the same aliases work on Windows, macOS, and Linux.
                normalised_name = process_name.casefold().removesuffix(".exe")
                if normalised_name in SUPPORTED_DOLPHIN_PROCESS_NAMES:
                    running_processes.append(process_name)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        return running_processes

    @classmethod
    def check_for_dolphin(cls):
        dolphin_count = len(cls.get_running_dolphin_processes())

        if dolphin_count > 1:
            return 2
        elif dolphin_count == 1:
            return 1
        else:
            return 0

    async def attempt_to_hook(self):
        fork_processes = [
            process_name
            for process_name in self.get_running_dolphin_processes()
            if process_name.casefold().removesuffix(".exe") in FORK_DOLPHIN_PROCESS_NAMES
        ]
        if fork_processes and not self.told_fork_warning:
            self.logger.warning(
                "Detected Dolphin fork: %s. Wii Play is developed and tested with standard Dolphin, "
                "memory addresses or client behaviour may not work correctly. Please report back if things work or don't.",
                ", ".join(fork_processes),
            )
            self.told_fork_warning = True

        if not self.dme.is_hooked():
            self.logger.info(f"Attempting to hook: Attempt {self.attempt}")
            self.dme.hook()

        if self.dme.is_hooked():
            self.logger.info("Hooked successfully!")
            self.attempt = 1  # Reset counter on success
        else:
            dolphin_status = self.check_for_dolphin()

            if dolphin_status == 0:
                self.logger.info("Failed to hook! Dolphin isn't running!")
            elif dolphin_status == 1:
                self.logger.info("Failed to hook! Wii Play isn't running!")
            elif dolphin_status == 2:
                self.logger.info("Failed to hook! Too many Dolphin instances are running!")

            self.attempt += 1
            await asyncio.sleep(5)

    def check_region(self):
        global GAME_VERSION

        byte = self.read_bytes(0x80000000, 6)
        decoded = byte.decode("utf-8", errors="ignore")

        if decoded == "RHAE01":
            detected_version = "NTSC-U"
        else:
            GAME_VERSION = None
            self.told_region = False
            self.logger.info(f"Unsupported or unreadable game ID: {decoded!r}")
            return False

        if GAME_VERSION != detected_version:
            self.told_region = False

        GAME_VERSION = detected_version
        if not self.told_region:
            self.logger.info(f"{detected_version} Detected!")
            self.told_region = True

        return True

    def is_hooked(self):
        if self.dme.is_hooked():
            return True
        else:
            return False

    def _assert_hooked(self):
        if not self.dme.is_hooked():
            raise DolphinException("Not hooked to Dolphin")

    def disconnect(self):
        global GAME_VERSION

        if self.dme.is_hooked():
            self.dme.un_hook()
        GAME_VERSION = None
        self.told_region = False
        self.told_fork_warning = False

    def read_byte(self, address: Any) -> Any:
        self._assert_hooked()
        result = self.dme.read_byte(address)
        return result

    def read_bytes(self, address: Any, bytes_to_read: int) -> Any:
        self._assert_hooked()
        result = self.dme.read_bytes(address, bytes_to_read)
        return result

    def read_word(self, address: Any) -> Any:
        self._assert_hooked()
        result = self.dme.read_word(address)
        return result

    def read_float(self, address: Any) -> Any:
        self._assert_hooked()
        result = self.dme.read_float(address)
        return result

    def read_string(self, address: int, size: int) -> str:
        self._assert_hooked()
        byte = self.dme.read_bytes(address, size)
        # Decode and strip out the invisible null bytes
        decoded = byte.decode("utf-8", errors="ignore").rstrip('\x00')
        return decoded

    def write_string(self, address: Any, string: str) -> Any:
        self._assert_hooked()
        encoded = string.encode("utf-8")
        self.dme.write_bytes(address, encoded)

    def write_byte(self, address: Any, data: Any):
        self._assert_hooked()
        self.dme.write_byte(address, data)

    def write_bytes(self, address: Any, data: Any) -> Any:
        self._assert_hooked()
        self.dme.write_bytes(address, data)

    def write_float(self, address: Any, data: Any):
        self._assert_hooked()
        self.dme.write_float(address, data)

    def write_word(self, address: Any, data: Any):
        self._assert_hooked()
        self.dme.write_word(address, data)

    def follow_pointers(self, address: Any, pointers: list):
        self._assert_hooked()
        result = self.dme.follow_pointers(address, list(pointers))
        return result

    def read_pointer(self, address: Any, pointers: list[int], data_type: str, length: int = 4) -> Any:
        """
        Resolves a pointer path and extracts the final value using structural pattern matching.
        Supported types: 'string', 'byte', 'bytes', 'float', 'word'
        This function is only used when the address at the pointer isn't used multiple times within the function
        """
        self._assert_hooked()

        resolved_addr = self.dme.follow_pointers(address, list(pointers))

        match data_type.lower().strip():
            case "string":
                return self.read_string(resolved_addr, length)
            case "byte":
                return self.read_byte(resolved_addr)
            case "bytes":
                return self.read_bytes(resolved_addr, length)
            case "float":
                return self.read_float(resolved_addr)
            case "word":
                return self.read_word(resolved_addr)
            case _:
                raise ValueError(f"Unsupported data type: {data_type}")

    def write_pointer(self, address: Any, pointers: list[int], data_type: str, data: Any) -> None:
        """
        Resolves a pointer path and writes the value to the final address based on a type string.
        Supported types: 'string', 'byte', 'bytes', 'float', 'word'
        This function is only used when the address at the pointer isn't used multiple times within the function
        """
        self._assert_hooked()

        resolved_addr = self.dme.follow_pointers(address, list(pointers))

        match data_type.lower().strip():
            case "string":
                self.write_string(resolved_addr, str(data))
            case "byte":
                self.write_byte(resolved_addr, data)
            case "bytes":
                self.write_bytes(resolved_addr, data)
            case "float":
                self.write_float(resolved_addr, float(data))
            case "word":
                self.write_word(resolved_addr, data)
            case _:
                raise ValueError(f"Unsupported data type for writing: {data_type}")