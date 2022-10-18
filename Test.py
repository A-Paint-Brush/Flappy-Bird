from os.path import normpath
from Colors import *
import pygame
"""
This file is only for testing rotation-centering in pygame. It can be safely deleted because it is not imported by the
rest of the project files.
"""


class Test:
    def __init__(self):
        self.resolution = (480, 360)
        self.fps = 60
        self.game_run = True
        pygame.display.set_caption("Centered Rotation Test")
        self.screen = pygame.display.set_mode(self.resolution)
        self.bird = Bird(self.resolution)
        self.clock = pygame.time.Clock()
        while self.game_run:
            self.clock.tick(self.fps)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_run = False
            self.screen.fill(WHITE)
            self.bird.tick()
            self.bird.draw(self.screen)
            self.bird.draw_hit_box(self.screen)
            pygame.display.update()
        pygame.quit()


class Bird:
    def __init__(self, resolution):
        self.image = pygame.image.load(normpath("./Images/flap middle.png")).convert_alpha()
        self.surface = self.image
        self.width, self.height = self.image.get_size()
        self.x = round(resolution[0] / 2 - self.width / 2)
        self.y = round(resolution[1] / 2 - self.height / 2)
        self.constant_x = self.x
        self.constant_y = self.y
        self.rect = pygame.Rect(*self._get_pos(), *self._get_size())
        self.starting_rect = self.rect
        self.angle = 0
        self.angle_tick = 2
        self.tick_count = 0

    def tick(self):
        self.tick_count += 1
        if self.tick_count > self.angle_tick:
            self.tick_count = 0
            self.angle -= 3
            self.angle %= 360
            self.surface = pygame.transform.rotate(self.image, self.angle)
            new_size = self.surface.get_size()
            self.x = self.constant_x + round((self.starting_rect.width - new_size[0]) / 2)
            self.y = self.constant_y + round((self.starting_rect.height - new_size[1]) / 2)
            self.rect = pygame.Rect(*self._get_pos(), *self.surface.get_size())

    def _get_pos(self):
        return self.x, self.y

    def _get_size(self):
        return self.width, self.height

    def draw(self, surface):
        surface.blit(self.surface, self._get_pos())

    def draw_hit_box(self, surface):
        bounds = self.surface.get_bounding_rect()
        pygame.draw.rect(surface, BLACK, [self.x + bounds.topleft[0], self.y + bounds.topleft[1], bounds.width, bounds.height], 1)


if __name__ == "__main__":
    Test()
