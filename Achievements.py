from typing import *


class Storage:
    def __init__(self):
        # Stores the ID of each achievement.
        self.titles = {0: "The Konami cheater.",
                       1: "You hacking, bro?",
                       2: "Feeling like rollin'?"}
        self.body_text = {0: "Except in this game, it doesn't allow you to cheat. Instead you get *rainbow mode* :)\n"
                             "The effect is only visible when the game screen doesn't fit the window size, so if you "
                             "don't see anything different, drag the window wider or taller.",
                          1: "You discovered debug mode! ...But it doesn't allow you to no-clip, it only shows "
                             "hit-boxes and the FPS. Ha ha I fooled you, no hackers are allowed in my game >:)",
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
        return list(self.titles[i] for i in self.achievements)

    def has_achievement(self, achievement_id: int) -> bool:
        return achievement_id in self.achievements
