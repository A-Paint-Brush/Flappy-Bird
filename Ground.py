from os.path import normpath
import pygame


class Tile(pygame.sprite.Sprite):
    def __init__(self, x_pos, resolution):
        super().__init__()
        self.image = pygame.image.load(normpath("./Images/Ground.png"))
        self.width, self.height = self.image.get_size()
        self.x = x_pos
        self.y = resolution[1] - self.height
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def get_size(self):
        return self.width, self.height

    def get_pos(self):
        return self.x, self.y

    def draw(self, surface):
        surface.blit(self.image, (self.x, self.y))

    def update(self, movement):
        self.x += movement
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def check_collision(self):
        if self.x < -self.width:
            self.kill()
            return True
        else:
            return False
