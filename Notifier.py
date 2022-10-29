from os.path import normpath
from Global import *
import Physics
import pygame


class ToastNotifier(pygame.sprite.Sprite):
    def __init__(self, resolution, y_pos, message_text):
        super().__init__()
        self.font = pygame.font.Font(normpath("./Fonts/Arial.ttf"), 18)
        self.icon_img = pygame.Surface((50, 50))  # Icon placeholder
        self.icon_img.fill(BLACK)
        self.image_padding = 15
        self.x = resolution[0]
        self.y = y_pos
        self.line_height = self.font.size("|")[1]
        self.width = 320
        self.corner_radius = 15
        self.body_text = word_wrap_text(message_text,
                                        self.width - self.corner_radius * 2 - self.icon_img.get_size()[0] - self.image_padding,
                                        self.font)
        self.height = self.line_height * len(self.body_text) + self.corner_radius * 2
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(WHITE)
        self.image.set_colorkey(WHITE, pygame.RLEACCEL)
        draw_rounded_rect(self.image, 0, 0, self.width, self.height, self.corner_radius, GREY)
        self.image.blit(self.icon_img, (self.corner_radius, self.corner_radius))
        for line_number, line_text in enumerate(self.body_text):
            text_surf = self.font.render(line_text, True, BLACK)
            self.image.blit(text_surf, (self.corner_radius + self.icon_img.get_size()[0] + self.image_padding,
                                        self.corner_radius + self.line_height * line_number))
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        # region Physics Variables
        self.direction = "left"
        self.deceleration = -165
        self.speed = 330
        self.physics = Physics.EulerDeceleration(self.deceleration, self.speed)
        # endregion

    def update(self):
        if self.direction == "left":
            movement = self.physics.calc()
            if movement > 0:
                self.x -= movement
            else:
                self.direction = "idle"
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def get_size(self):
        return self.width, self.height


class ToastGroup(pygame.sprite.Group):
    def __init__(self, resolution):
        super().__init__()
        self.resolution = resolution
        self.toasts = []
        self.padding = 10

    def create_toast(self, toast_text):
        new_toast = ToastNotifier(self.resolution,
                                  self.padding * (len(self.toasts) + 1) + sum(toast.get_size()[1] for toast in self.toasts),
                                  toast_text)
        self.toasts.append(new_toast)
        self.add(new_toast)

    def get_toast_num(self):
        return len(self.toasts)
