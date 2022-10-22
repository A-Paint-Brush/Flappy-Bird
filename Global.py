import pygame
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CYAN = (112, 197, 206)
YELLOW = (222, 216, 149)


def collide_function(sprite1, sprite2):
    result = pygame.sprite.collide_mask(sprite1, sprite2)
    return result is not None
