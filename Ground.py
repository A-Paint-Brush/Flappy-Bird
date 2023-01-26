from typing import *
from os.path import normpath
import pygame
import Time


class Ground(pygame.sprite.Sprite):
    def __init__(self, resolution: Tuple[int, int]):
        super().__init__()
        self.tile_image = pygame.image.load(normpath("./Images/Ground.png")).convert_alpha()
        self.tile_width, self.tile_height = self.tile_image.get_size()
        self.tile_count = 1
        while self.tile_width * self.tile_count < resolution[0] + self.tile_width:
            self.tile_count += 1
        self.tile_count += 1
        self.width = self.tile_width * self.tile_count
        self.height = self.tile_height
        self.image = pygame.Surface((self.width, self.height))
        for x in range(self.tile_count):
            self.image.blit(self.tile_image, (self.tile_width * x, 0))
        self.x = 0
        self.y = resolution[1] - self.height
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def get_tile_size(self) -> Tuple[int, int]:
        return self.tile_width, self.tile_height

    def get_pos(self) -> Tuple[int, int]:
        return self.x, self.y

    def get_rect(self) -> pygame.Rect:
        return self.rect

    def update(self, movement: float) -> None:
        self.x += movement
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def set_x(self, x: float) -> None:
        self.x = x
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)


class GroundGroup(pygame.sprite.Group):
    def __init__(self, resolution: Tuple[int, int]):
        super().__init__()
        self.resolution = resolution
        self.delta_x = -100  # Production movement: -100, Debug movement: -40
        self.ground_object = Ground(self.resolution)
        self.add(self.ground_object)
        self.frame_timer = Time.Time()
        self.frame_timer.reset_timer()

    def get_size(self) -> Tuple[int, int]:
        return self.ground_object.get_tile_size()

    def get_pos(self) -> Tuple[int, int]:
        return self.ground_object.get_pos()

    def move(self) -> float:
        movement = (self.delta_x * self.frame_timer.get_time())
        self.update(movement)
        self.frame_timer.reset_timer()
        return movement

    def reset_pos(self) -> None:
        # if x < 0: x = -(|x| % width)
        if self.ground_object.get_pos()[0] < 0:
            self.ground_object.set_x(-(abs(self.ground_object.get_pos()[0]) % self.ground_object.get_tile_size()[0]))
