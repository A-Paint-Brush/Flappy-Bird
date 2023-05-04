from typing import *
import threading
import platform
import queue
import enum
import csv
import os
status_codes = enum.Enum("status_codes", ["success", "error"])
global_app_data = {"Windows": "%programdata%/Flappy Bird",
                   "Darwin": "/Library/Flappy Bird",
                   "Linux": "/var/lib/Flappy Bird"}
user_app_data = {"Windows": "%appdata%/Flappy Bird",
                 "Darwin": "~/Library/Flappy Bird",
                 "Linux": "~/.flappy_bird"}


def get_platform_data_path(purpose: Literal["global", "user"]) -> str:
    current_os = platform.system()
    location = ""
    fail_message = "The application cannot decide on a location to store global (user-independent) application data " \
                   "on this OS. Please edit the source-code and insert a path you would like this game to use at " \
                   "Storage.py:row 21:column 61, then relaunch the game."
    if purpose == "global":
        location = global_app_data.get(current_os, "")
    elif purpose == "user":
        location = user_app_data.get(current_os, "~/.flappy_bird")
    if not location:
        raise NotImplementedError(fail_message)
    return os.path.expandvars(os.path.expanduser(os.path.normpath(location)))


class Achievements:
    def __init__(self):
        # Stores the ID of each achievement.
        self.titles = {0: "The Konami code",
                       1: "The magic word",
                       2: "Feeling like rollin'?"}
        self.body_text = {0: "Except in this game, it doesn't allow you to cheat. Instead you get *rainbow mode* :)\n"
                             "The effect is only visible when the game screen doesn't fit the window size, so if you "
                             "don't see anything different, drag the window wider or taller.",
                          1: "You discovered debug mode! ...But it doesn't allow you to no-clip, it only shows "
                             "hit-boxes and the FPS.",
                          2: "Honestly, you typed in \"rickroll\". What were you expecting?"}
        self.explanation_text = {0: "Type the Konami code anywhere in the game.",
                                 1: "Type the magic word anywhere in the game.",
                                 2: "Type \"rickroll\" anywhere in the game."}
        # Stores the IDs of all acquired achievements.
        self.achievements = []

    def get_new_achievement(self, achievement_id: int) -> Tuple[str, str]:
        self.achievements.append(achievement_id)
        return self.titles[achievement_id], self.body_text[achievement_id]

    def get_achievement_list(self) -> List[str]:
        return [self.titles[i] for i in self.achievements]

    def has_achievement(self, achievement_id: int) -> bool:
        return achievement_id in self.achievements


class HelpFile:
    def __init__(self):
        self.file_path = os.path.normpath("./Help/Instructions.txt")
        self.encoding = "utf-8"
        self.error_text = ("Failed to load instructions :(\n\nThis could be because the help file has been "
                           "moved/deleted, the OS or an anti-virus program is blocking this game from accessing it, or "
                           "due to a hardware error (such as a faulty hard-disk).")
        self.data_queue = queue.Queue()
        self.io_thread = threading.Thread(target=self.start_file_read, daemon=True)
        self.io_thread.start()

    def start_file_read(self) -> None:
        if not os.path.isfile(self.file_path):
            self.data_queue.put((status_codes["error"], None))
            return None
        try:
            with open(self.file_path, "r", encoding=self.encoding) as file:
                text_data = file.read()
        except OSError:
            self.data_queue.put((status_codes["error"], None))
        else:
            self.data_queue.put((status_codes["success"], text_data))

    def is_running(self) -> bool:
        return self.io_thread.is_alive()

    def get_data(self) -> str:
        """Only call this after 'HelpFile.is_done' returns True."""
        status, data = self.data_queue.get()
        if status == status_codes["success"]:
            return data
        elif status == status_codes["error"]:
            return self.error_text


class ScoreDB:
    def __init__(self):
        self.dir_path = get_platform_data_path("global")
        self.file_path = os.path.join(self.dir_path, "scoreboard.csv")
        self.encoding = "utf-8"
        self.fields = ("player-name", "score")
        self.data_queue = queue.Queue()
        self.io_thread: Optional[threading.Thread] = None

    def is_busy(self) -> bool:
        return self.io_thread.is_alive()

    def get_data(self) -> Tuple[enum.Enum, Optional[List[Dict[str, str]]]]:
        if not self.io_thread.is_alive():
            return self.data_queue.get()

    def write_config_file(self) -> bool:
        try:
            if not os.path.isdir(self.dir_path):
                os.mkdir(self.dir_path)
            with open(self.file_path, "w", encoding=self.encoding, newline="") as file:
                writer = csv.DictWriter(file, self.fields)
                writer.writeheader()
        except (OSError, NotImplementedError):
            return False
        else:
            return True

    def start_fetch_scores(self) -> None:
        self.io_thread = threading.Thread(target=self.fetch_scores)
        self.io_thread.start()

    def fetch_scores(self) -> None:
        if not os.path.isfile(self.file_path) and not self.write_config_file():
            # Scoreboard DB not found and cannot be created. Return 'success' so the game can try to write the current
            # score to the DB.
            self.data_queue.put((status_codes["success"], []))
        try:
            with open(self.file_path, "r", encoding=self.encoding, newline="") as file:
                reader = csv.DictReader(file, self.fields)
                try:
                    next(reader)  # Skip header
                except StopIteration:  # Unexpected EOF.
                    if self.write_config_file():  # Attempt to over-write the malformed file.
                        # Overwrite successful, DB is now empty.
                        self.data_queue.put((status_codes["success"], []))
                    else:
                        # DB file is still corrupted, return error.
                        self.data_queue.put((status_codes["error"], None))
                    return None
                else:
                    csv_data = list(reader)
        except OSError:
            self.data_queue.put((status_codes["error"], None))
        else:
            self.data_queue.put((status_codes["success"], csv_data))

    def start_write_score(self, player_name: str, score: int) -> None:
        self.io_thread = threading.Thread(target=self.write_score, args=(player_name, score))
        self.io_thread.start()

    def write_score(self, player_name: str, score: int) -> None:
        """Starts the write operation to insert the data given to the beginning of the DB."""
        if not os.path.isfile(self.file_path) and not self.write_config_file():
            return None
        try:
            with open(self.file_path, "r", encoding=self.encoding, newline="") as file:
                reader = csv.DictReader(file, self.fields)
                csv_data = list(reader)
            if not csv_data or csv_data[0] != {self.fields[0]: self.fields[0], self.fields[1]: self.fields[1]}:
                return None  # Malformed data.
            csv_data.insert(1, {self.fields[0]: player_name, self.fields[1]: score})
            with open(self.file_path, "w", encoding=self.encoding, newline="") as file:
                writer = csv.DictWriter(file, self.fields)
                writer.writerows(csv_data)
        except OSError:
            return None
