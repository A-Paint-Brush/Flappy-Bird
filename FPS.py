from os.path import normpath
from Global import *
import pygame
import Time


class Counter(pygame.sprite.Sprite):
    def __init__(self, resolution):
        super().__init__()
        self.resolution = resolution
        self.font = pygame.font.Font(normpath("./Fonts/Arial.ttf"), 20)
        self.frame_timer = Time.Time()
        self.frame_timer.reset_timer()
        self.fps_data = []
        self.storage_length = 10  # The number of entries to keep in the list.
        self.x = 0
        self.y = 0
        self.image = None
        self.rect = None
        self.update_text("-- FPS")

    def push_data(self):
        data = self.frame_timer.get_time()
        self.frame_timer.reset_timer()
        self.fps_data.append(data)

    def calc_data(self):
        return round(1 / (sum(self.fps_data) / len(self.fps_data)))

    def update_text(self, new_text):
        self.image = self.font.render(new_text, True, BLACK)
        self.x = self.resolution[0] - self.image.get_size()[0]
        self.rect = pygame.Rect(self.x, self.y, *self.image.get_size())

    def tick(self):
        self.push_data()
        if len(self.fps_data) <= self.storage_length:
            return None
        else:
            self.fps_data.pop(0)
            fps = self.calc_data()
            self.update_text("{} FPS".format(fps))
            return fps

    def stop(self):
        self.fps_data.clear()
        self.update_text("-- FPS")

    def draw(self, surface):
        surface.blit(self.image, (self.x, self.y))
