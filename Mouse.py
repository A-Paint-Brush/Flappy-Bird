import pygame


class Cursor(pygame.sprite.Sprite):
    # Cursor class used for Mask collision detection between the mouse cursor and a Sprite group.
    def __init__(self):
        super().__init__()
        self.x = 0
        self.y = 0
        self.width = 1
        self.height = 1
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.mask = pygame.mask.Mask(size=(self.width, self.height), fill=True)

    def update_pos(self, new_x, new_y):
        self.x = new_x
        self.y = new_y
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
