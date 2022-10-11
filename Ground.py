from os.path import normpath
import pygame


class Tile(pygame.sprite.Sprite):
    def __init__(self, x_pos, fixed_resolution):
        super().__init__()
        self.delta_x = 2
        self.image = pygame.image.load(normpath("./Images/Ground.png"))
        self.width, self.height = self.image.get_size()
        self.x = x_pos
        self.y = fixed_resolution[1] - self.height
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def get_size(self):
        return self.width, self.height

    def get_pos(self):
        return self.x, self.y

    def get_speed(self):
        return self.delta_x

    def update(self):
        self.x -= self.delta_x
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def check_collision(self):
        if self.x < -self.width:
            self.kill()
            return True
        else:
            return False
