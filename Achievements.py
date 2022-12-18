class Storage:
    def __init__(self):
        # Stores the ID of each achievement.
        self.titles = {0: "The Konami cheater.",
                       1: "You hacking, bro?",
                       2: "Feeling like rollin'?",
                       3: "Potato PC boi!"}
        self.body_text = {0: "Except in this game, it doesn't allow you to cheat. Instead you get *rainbow mode* :)\n"
                             "The effect is only visible when the game screen doesn't fit the window size, so if you "
                             "don't see anything different, drag the window wider or taller.",
                          1: "You discovered debug mode! ...But it doesn't allow you to no-clip, it only shows "
                             "hit-boxes and the FPS. Ha ha I fooled you, no hackers are allowed in my game >:)",
                          2: "Honestly, you typed in \"rickroll\". What were you expecting?",
                          3: "An FPS lower than 30 has been detected! Please try closing some applications on your "
                             "device. You can also consider throwing this device out of the window and buying a better "
                             "one ;)"}
        self.explanation_text = {0: "Type the Konami code anywhere in the game.",
                                 1: "Type the magic word anywhere in the game.",
                                 2: "Type \"rickroll\" anywhere in the game.",
                                 3: "Get an FPS lower than 30 anytime in the game."}
        # Stores the IDs of all acquired achievements.
        self.achievements = []

    def get_new_achievement(self, achievement_id):
        self.achievements.append(achievement_id)
        return self.titles[achievement_id], self.body_text[achievement_id]

    def get_achievement_list(self):
        return list(self.titles[i] for i in self.achievements)

    def has_achievement(self, achievement_id):
        return achievement_id in self.achievements
