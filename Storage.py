from typing import *
import threading
import queue
import enum
import os


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
        self.status_codes = enum.Enum("status_codes", ["success", "error"])
        self.error_text = ("Failed to load instructions :(\n\nThis could be because the help file has been "
                           "moved/deleted, the OS or an anti-virus program is blocking this game from accessing it, or "
                           "due to a hardware error (such as a faulty hard-disk).")
        self.data_queue = queue.Queue()
        self.io_thread = threading.Thread(target=self.start_file_read, daemon=True)
        self.io_thread.start()

    def start_file_read(self) -> None:
        if not os.path.isfile(self.file_path):
            self.data_queue.put((self.status_codes["error"], None))
            return None
        try:
            with open(self.file_path, "r", encoding=self.encoding) as file:
                text_data = file.read()
        except OSError:
            self.data_queue.put((self.status_codes["error"], None))
        else:
            self.data_queue.put((self.status_codes["success"], text_data))

    def is_running(self) -> bool:
        return self.io_thread.is_alive()

    def get_data(self) -> str:
        """Only call this after 'HelpFile.is_done' returns True."""
        status, data = self.data_queue.get()
        if status == self.status_codes["success"]:
            return data
        elif status == self.status_codes["error"]:
            return self.error_text
