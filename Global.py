from typing import *
import pygame.transform
BLACK = (0, 0, 0)
ORANGE = (255, 160, 20)
GREY = (209, 209, 209)
WHITE = (255, 255, 255)
CYAN = (112, 197, 206)
YELLOW = (222, 216, 149)
BLUE = (26, 134, 219)
TRANSPARENT = (1, 1, 1)  # The color used as the transparent color in 'Surface.set_colorkey()' throughout the project.


def collide_function(sprite1: pygame.sprite.Sprite, sprite2: pygame.sprite.Sprite) -> bool:
    result = pygame.sprite.collide_mask(sprite1, sprite2)
    return result is not None


def resize_surf(display_surf: pygame.Surface, size: List) -> pygame.Surface:
    current_size = display_surf.get_size()
    new_size = [0, 0]
    if current_size[0] * (size[1] / current_size[1]) < size[0]:
        new_size[0] = current_size[0] * (size[1] / current_size[1])
        new_size[1] = size[1]
    else:
        new_size[0] = size[0]
        new_size[1] = current_size[1] * (size[0] / current_size[0])
    return pygame.transform.scale(display_surf, new_size)


def resize_mouse_pos(pos: Tuple[int, int],
                     fixed_size: Tuple[int, int],
                     current_size: List,
                     resized_surf: Tuple[int, int]) -> Tuple[float, float]:
    offset_pos = (pos[0] - ((current_size[0] - resized_surf[0]) / 2),
                  pos[1] - ((current_size[1] - resized_surf[1]) / 2))
    return (fixed_size[0] * (offset_pos[0] / resized_surf[0])),\
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
    pygame.draw.rect(surface, bg, [x + corner_radius + border, y + border, width - corner_radius * 2 - border * 2, height - border * 2], 0)
    surface.blit(text_surf, (surface.get_size()[0] / 2 - text_width / 2, surface.get_size()[1] / 2 - text_height / 2))


def word_wrap_text(string: str, width: int, font: pygame.font.Font) -> List[str]:
    # region Wrap words
    words = string.split(" ")
    shortened_words = []
    for w in words:
        if font.size(w)[0] > width:
            word_chunks = []
            current_word = list(w)
            while current_word:
                current_chunk = []
                overflow = True
                while font.size("".join(current_chunk + ["-"]))[0] <= width:
                    if not current_word:
                        overflow = False
                        break
                    current_chunk.append(current_word.pop(0))
                if overflow:
                    current_word.insert(0, current_chunk.pop())
                word_chunks.append("".join(current_chunk + ["-" if overflow else ""]))
            for chunk in word_chunks:
                shortened_words.append(chunk)
        else:
            shortened_words.append(w)
    words = shortened_words
    # endregion
    # region Wrap lines
    wrapped_lines = []
    current_line = []
    while words:
        overflow = True
        while font.size(" ".join(current_line))[0] <= width:
            if not words:
                overflow = False
                break
            next_word = words.pop(0)
            if next_word.count("\n") > 0:
                split = next_word.split("\n")
                current_line.append(split[0])
                if font.size(" ".join(current_line))[0] > width:
                    overflow = True
                else:
                    overflow = False
                words.insert(0, "\n".join(split[1:]))
                break
            else:
                current_line.append(next_word)
        if overflow:
            words.insert(0, current_line.pop())
        wrapped_lines.append(" ".join(current_line))
        current_line.clear()
    # endregion
    return wrapped_lines
