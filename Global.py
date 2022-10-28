import pygame
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CYAN = (112, 197, 206)
YELLOW = (222, 216, 149)


def collide_function(sprite1, sprite2):
    result = pygame.sprite.collide_mask(sprite1, sprite2)
    return result is not None


def resize_surf(display_surf, size):
    current_size = display_surf.get_size()
    new_size = [0, 0]
    if current_size[0] * (size[1] / current_size[1]) < size[0]:
        new_size[0] = current_size[0] * (size[1] / current_size[1])
        new_size[1] = size[1]
    else:
        new_size[0] = size[0]
        new_size[1] = current_size[1] * (size[0] / current_size[0])
    return pygame.transform.scale(display_surf, new_size)


def resize_mouse_pos(pos, fixed_size, current_size):
    return fixed_size[0] * (pos[0] / current_size[0]), fixed_size[1] * (pos[1] / current_size[1])
