"""
This is the file I used for testing while experimenting with ways to work around the bug in pygame that causes the event
queue to block 'pygame.event' methods while the mouse button is held down on the title bar of the window. The purpose of
the moving squares are to help me clearly see if the window is frozen, and also because they are fun :)
"""
from typing import *
from random import *
import pygame


class Window:
    def __init__(self):
        pygame.init()
        self.min_resolution = (650, 450)
        self.resolution = self.min_resolution
        self.game_run = True
        self.force_refresh = True
        temp_square = Square((0, 0), (0, 0, 0), self.resolution)
        colors = ((255, 160, 20),
                  (202, 255, 153),
                  (67, 138, 255),
                  (255, 49, 56),
                  (255, 35, 244),
                  (85, 255, 28),
                  (255, 173, 227))
        self.object_group = pygame.sprite.RenderUpdates()
        for square in range(500):  # Create square objects.
            self.object_group.add(Square((randint(0, self.resolution[0] - temp_square.get_size()[0] - 1),
                                          randint(0, self.resolution[1] - temp_square.get_size()[1] - 1)),
                                         choice(colors),
                                         self.resolution))
        self.counter_group = pygame.sprite.RenderUpdates()
        self.counter_group.add(FpsCounter(self.resolution))
        self.clock = pygame.time.Clock()
        pygame.display.set_caption("Flying Squares")
        self.screen = pygame.display.set_mode(self.resolution, pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
        while self.game_run:
            self.clock.tick()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_run = False
                elif event.type == pygame.VIDEORESIZE:
                    self.resolution = (self.min_resolution[0] if event.w < self.min_resolution[0] else event.w,
                                       self.min_resolution[1] if event.h < self.min_resolution[1] else event.h)
                    self.screen = pygame.display.set_mode(self.resolution,
                                                          pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
                    self.force_refresh = True
                elif event.type == pygame.VIDEOEXPOSE:
                    self.force_refresh = True
            self.object_group.update(self.resolution)
            self.counter_group.update(str(round(self.clock.get_fps())), self.resolution)
            self.screen.fill((0, 127, 0))
            rect_list = self.object_group.draw(self.screen)
            rect_list += self.counter_group.draw(self.screen)
            if self.force_refresh:
                self.force_refresh = False
                pygame.display.update()
            else:
                pygame.display.update(rect_list)
        pygame.quit()


class Square(pygame.sprite.Sprite):
    def __init__(self, position: Tuple[int, int], color: Tuple[int, int, int], resolution: Tuple[int, int]):
        super().__init__()
        # region Sprite Data
        self.resolution = resolution
        self.width = 40
        self.height = 40
        self.x, self.y = position
        # endregion
        # region Physics Variables
        self.x_speed = randint(-300, 300)
        self.y_speed = randint(-300, 300)
        self.prev_time = pygame.time.get_ticks()
        # endregion
        # region Sprite Attributes
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(color)
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        # endregion

    def get_size(self) -> Tuple[int, int]:
        return self.width, self.height

    def get_time(self) -> float:
        new_ticks = pygame.time.get_ticks()
        delta_time = new_ticks - self.prev_time
        self.prev_time = new_ticks
        return delta_time / 1000

    def update(self, new_resolution: Tuple[int, int]) -> None:
        # region Update x position
        self.resolution = new_resolution
        time = self.get_time()
        self.x += self.x_speed * time
        if self.x + self.width >= self.resolution[0]:
            self.x_speed = -self.x_speed
            self.x = self.resolution[0] - self.width - 1
        elif self.x < 0:
            self.x_speed = -self.x_speed
            self.x = 0
        # endregion
        # region Update y position
        self.y += self.y_speed * time
        if self.y + self.height >= self.resolution[1]:
            self.y_speed = -self.y_speed
            self.y = self.resolution[1] - self.height - 1
        elif self.y < 0:
            self.y_speed = -self.y_speed
            self.y = 0
        # endregion
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)


class FpsCounter(pygame.sprite.Sprite):
    def __init__(self, resolution: Tuple[int, int]):
        super().__init__()
        # region Sprite Data
        self.resolution = None
        self.font = pygame.font.SysFont("Arial", 22)
        self.h_pad = 10
        self.text = "--"
        self.width = None
        self.height = None
        self.x = None
        self.y = None
        # endregion
        # region Sprite Attributes
        self.image = None
        self.rect = None
        # endregion
        self.update(self.text, resolution)

    def get_rect(self) -> pygame.Rect:
        return self.rect

    def update(self, fps_text: str, resolution: Tuple[int, int]) -> None:
        self.resolution = resolution
        self.text = "{} fps".format(fps_text)
        self.width, self.height = self.font.size(self.text)
        self.x = self.resolution[0] - self.width - self.h_pad
        self.y = 5
        self.image = self.font.render(self.text, True, (0, 0, 0))
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)


if __name__ == "__main__":
    Window()
