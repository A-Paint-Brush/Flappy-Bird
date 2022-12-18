"""
This file is only for testing centered rotation in pygame. It can be safely deleted because it is not imported by the
rest of the project files.
"""
from os.path import normpath
import pygame
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (222, 216, 149)


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
            self.bird.draw_mask(self.screen)
            pygame.display.update()
        pygame.quit()


class Bird:
    def __init__(self, resolution):
        self.resolution = resolution
        self.image = pygame.image.load(normpath("../Images/flap middle.png")).convert_alpha()
        self.surface = self.image
        self.width, self.height = self.image.get_size()
        self.x = round(self.resolution[0] / 2)
        self.y = round(self.resolution[1] / 2 - self.height / 2)
        self.constant_x = self.x
        self.constant_y = self.y
        self.rect = pygame.Rect(*self._get_pos(), *self._get_size())
        self.mask = pygame.mask.from_surface(self.image)
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
            new_size = self.surface.get_bounding_rect()
            cropped_surface = pygame.Surface((new_size.width, new_size.height))
            cropped_surface.set_colorkey(BLACK)
            cropped_surface.blit(self.surface, (0, 0), area=new_size)
            self.surface = cropped_surface
            self.x = self.constant_x + round((self.starting_rect.width - new_size.width) / 2)
            self.y = self.constant_y + round((self.starting_rect.height - new_size.height) / 2)
            self.rect = pygame.Rect(self.x, self.y, new_size.width, new_size.height)
            self.mask = pygame.mask.from_surface(self.surface)

    def _get_pos(self):
        return self.x, self.y

    def _get_size(self):
        return self.width, self.height

    def draw(self, surface):
        surface.blit(self.surface, self._get_pos())

    def draw_hit_box(self, surface):
        pygame.draw.rect(surface, BLACK, self.rect, 1)

    def draw_mask(self, surface):
        self.mask.to_surface(surface, setcolor=YELLOW, unsetcolor=BLACK, dest=(self.resolution[0] / 2 - self.rect.width, self.y))


if __name__ == "__main__":
    Test()
