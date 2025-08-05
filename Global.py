from contextlib import suppress
from typing import *
from os import path
import platform
import pygame.transform
with suppress(ImportError):
    from ctypes import windll
cjk_fonts = ("microsoftjhenghei", "notosanscjktc", "notofontscjk")
WHITE = (255, 255, 255)
RED = (255, 0, 0)
ORANGE = (255, 160, 20)
YELLOW = (222, 216, 149)
GREEN = (202, 255, 112)
BLUE = (26, 134, 219)
CYAN = (112, 197, 206)
PURPLE = (177, 29, 209)
GREY1 = (240, 240, 240)
GREY2 = (218, 218, 218)
GREY3 = (209, 209, 209)
GREY4 = (205, 205, 205)
GREY5 = (166, 166, 166)
GREY6 = (96, 96, 96)
BLACK = (0, 0, 0)
TRANSPARENT = (1, 1, 1)  # The color used as the transparent color-key throughout the project.


def find_abs_path(rel_path: str) -> str:
    """Returns absolute version of the relative path given regardless of working directory."""
    return path.abspath(path.join(path.dirname(__file__), path.normpath(rel_path)))


def collide_function(sprite1: pygame.sprite.Sprite, sprite2: pygame.sprite.Sprite) -> bool:
    result = pygame.sprite.collide_mask(sprite1, sprite2)
    return result is not None


def resize_surf(display_surf: pygame.Surface,
                size: Union[List[Union[int, float]], Tuple[Union[int, float], Union[int, float]]],
                size_only: bool = False) -> Union[pygame.Surface, Tuple[Union[int, float], Union[int, float]]]:
    current_size = display_surf.get_size()
    if current_size[0] * (size[1] / current_size[1]) < size[0]:
        new_size = (current_size[0] * (size[1] / current_size[1]), size[1])
    else:
        new_size = (size[0], current_size[1] * (size[0] / current_size[0]))
    if size_only:
        return new_size
    else:
        return pygame.transform.scale(display_surf, new_size)


def dilate_coordinates(pos: Tuple[int, int], fixed_size: Tuple[int, int], current_size: List,
                       resized_surf: Tuple[int, int]) -> Tuple[float, float]:
    offset_pos = ((current_size[0] - resized_surf[0]) / 2, (current_size[1] - resized_surf[1]) / 2)
    return (offset_pos[0] + (resized_surf[0] * (pos[0] / fixed_size[0])),
            offset_pos[1] + (resized_surf[1] * (pos[1] / fixed_size[1])))


def resize_mouse_pos(pos: Tuple[int, int],
                     fixed_size: Tuple[int, int],
                     current_size: List,
                     resized_surf: Tuple[int, int]) -> Tuple[float, float]:
    offset_pos = (pos[0] - ((current_size[0] - resized_surf[0]) / 2),
                  pos[1] - ((current_size[1] - resized_surf[1]) / 2))
    return (fixed_size[0] * (offset_pos[0] / resized_surf[0])), \
           (fixed_size[1] * (offset_pos[1] / resized_surf[1]))


def draw_rounded_rect(surface: pygame.Surface,
                      pos: Tuple[int, int],
                      size: Tuple[Union[int, float], Union[int, float]],
                      radius: int,
                      color: Tuple[int, int, int]) -> None:
    positions = ([pos[0] + radius, pos[1] + radius],
                 [pos[0] + size[0] - radius, pos[1] + radius],
                 [pos[0] + radius, pos[1] + size[1] - radius],
                 [pos[0] + size[0] - radius, pos[1] + size[1] - radius])
    for position in positions:
        pygame.draw.circle(surface, color, position, radius, 0)
    pygame.draw.rect(surface, color, [pos[0], pos[1] + radius, size[0], size[1] - radius * 2], 0)
    pygame.draw.rect(surface, color, [pos[0] + radius, pos[1], size[0] - radius * 2, size[1]], 0)


def draw_button(surface: pygame.Surface,
                x: int,
                y: int,
                width: int,
                height: int,
                border: int,
                fg: Tuple[int, int, int],
                bg: Tuple[int, int, int],
                font: pygame.font.Font,
                text: str) -> None:
    current_size = font.size(text)
    new_size = (width - height - border * 2, height - border * 2)
    text_surf = font.render(text, True, fg)
    if current_size[0] * (new_size[1] / current_size[1]) < new_size[0]:
        text_width = current_size[0] * (new_size[1] / current_size[1])
        text_height = new_size[1]
    else:
        text_width = new_size[0]
        text_height = current_size[1] * (new_size[0] / current_size[0])
    text_surf = pygame.transform.scale(text_surf, (text_width, text_height))
    corner_radius = height / 2
    positions = ([x + corner_radius, y + corner_radius],
                 [x + width - corner_radius, y + corner_radius])
    for position in positions:
        pygame.draw.circle(surface, BLACK, position, corner_radius, 0)
    pygame.draw.rect(surface, BLACK, [x + corner_radius, y, width - corner_radius * 2, height], 0)
    positions = ([x + corner_radius + border, y + corner_radius],
                 [x + width - corner_radius - border, y + corner_radius])
    for position in positions:
        pygame.draw.circle(surface, bg, position, corner_radius - border, 0)
    pygame.draw.rect(surface, bg, [x + corner_radius + border, y + border, width - corner_radius * 2 - border * 2,
                                   height - border * 2], 0)
    surface.blit(text_surf, (surface.get_size()[0] / 2 - text_width / 2, surface.get_size()[1] / 2 - text_height / 2))


def draw_vtp_rounded_rect(surface: pygame.Surface,
                          pos: Tuple[int, int],
                          size: Tuple[int, int],
                          color: Tuple[int, int, int]) -> None:
    # v.t.p. = vertical two-point
    y_positions = (pos[1] + size[0] / 2, pos[1] + size[1] - size[0] / 2)
    for y in y_positions:
        pygame.draw.circle(surface, color, (pos[0] + size[0] / 2, y), size[0] / 2)
    pygame.draw.rect(surface, color, (pos[0], pos[1] + size[0] / 2, size[0], size[1] - size[0]), 0)


def draw_triangle(surface: pygame.Surface,
                  pos: Tuple[int, int],
                  size: Tuple[int, int],
                  color: Tuple[int, int, int],
                  flip: bool) -> None:
    # Draws upward triangle if flip is False.
    vertices = ((pos[0], pos[1] if flip else pos[1] + size[1] - 1),
                (pos[0] + size[0] - 1, pos[1] if flip else pos[1] + size[1] - 1),
                (pos[0] + round(size[0] / 2), pos[1] + size[1] - 1 if flip else pos[1]))
    pygame.draw.polygon(surface, color, vertices)


def draw_cross(surface: pygame.Surface,
               pos: Tuple[int, int],
               size: Tuple[int, int],
               width: int,
               color: Tuple[int, int, int]) -> None:
    lines = ((pos, (pos[0] + size[0] - 1, pos[1] + size[1] - 1)),
             ((pos[0] + size[0] - 1, pos[1]), (pos[0], pos[1] + size[1] - 1)))
    for line in lines:
        pygame.draw.line(surface, color, line[0], line[1], width=width)


def word_wrap_text(string: str, width: int, font: pygame.font.Font, br: str = "-") -> List[str]:
    lines, break_locations = [[]], []
    for index, char in enumerate(string):
        if char == " ":
            break_locations.append(len(lines[-1]))
            lines[-1].append(char)
            continue
        elif char == "\n":
            break_locations.clear()
            lines.append([])
            continue
        if font.size("".join(lines[-1] + [char, br]))[0] <= width:
            lines[-1].append(char)
        else:
            if break_locations:
                last_word = lines[-1][break_locations[-1] + 1:]
                lines[-1] = lines[-1][:break_locations[-1]]
                break_locations.clear()
                lines.append(last_word)
                lines[-1].append(char)
            else:
                if lines and lines[-1]:
                    if lines[-1][-1].isascii():  # Chinese characters do not need a dash on line-breaking.
                        lines[-1].append(br)
                lines.append([char])
    return ["".join(line) for line in lines]


def configure_dpi() -> None:
    """If current OS is Windows, attempts to configure the Python process to be DPI aware."""
    if platform.system() == "Windows":
        if not post_win8_config_dpi():
            pre_win8_config_dpi()


def post_win8_config_dpi() -> bool:
    try:
        windll.shcore.SetProcessDpiAwareness(2)
    except (NameError, OSError, AttributeError):
        return False
    else:
        return True


def pre_win8_config_dpi() -> bool:
    try:
        windll.shcore.SetProcessDPIAware()
    except (NameError, OSError, AttributeError):
        return False
    else:
        return True
