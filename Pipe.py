from os.path import normpath
from Global import *
import math
import random
import pygame
import Time


class Pipe(pygame.sprite.Sprite):
    def __init__(self, x_pos: int, resolution: Tuple[int, int], ground_size: Tuple[int, int]):
        super().__init__()
        self.pipe_image = pygame.image.load(normpath("Images/Sprites/pipe.png")).convert_alpha()
        self.width, self.height = self.pipe_image.get_size()
        self.resolution = list(resolution)
        self.resolution[1] -= ground_size[1]
        self.x = x_pos
        self.y = 0
        # The shortest pipe length allowed: 86
        # Minimum value of bottom pipe y position: y = min_length + constant (constant > bird_height)
        # Maximum value of bottom pipe y position: y = resolution[1] - min_length
        # Y position of top pipe: bottom_pipe_y - constant
        self.gap_distance = 145  # Production distance: 145, Debug distance: 400
        self.min_length = 66
        self.bottom_pipe_pos = (0, random.randint(self.min_length + self.gap_distance, self.resolution[1] - self.min_length))
        self.top_pipe_pos = (0, self.bottom_pipe_pos[1] - self.gap_distance - self.height)
        self.image = pygame.Surface((self.width, self.resolution[1]))
        # Uses the RLEACCEL flag to improve the blit performance, since the surface is only modified on creation.
        self.image.set_colorkey(TRANSPARENT, pygame.RLEACCEL)
        self.image.fill(TRANSPARENT)
        self.image.blit(self.pipe_image, self.bottom_pipe_pos)
        self.image.blit(pygame.transform.flip(self.pipe_image, False, True), self.top_pipe_pos)
        # region Brightness Variables
        self.original_surface = self.image.copy()
        self.brightness = 1
        self.max_brightness = 150
        self.flash_movement = 300
        self.flash_timer = Time.Time()
        # endregion
        self.rect = pygame.Rect(self.x, self.y, self.width, self.resolution[1])
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, movement: Union[int, float]) -> None:
        self.x += movement
        self.rect = pygame.Rect(self.x, self.y, self.width, self.resolution[1])

    def init_flash(self) -> None:
        self.flash_timer.reset_timer()

    def flash_tick(self) -> bool:
        delta_time = self.flash_timer.get_time()
        self.flash_timer.reset_timer()
        self.image = self.original_surface.copy()
        self.brightness += round(self.flash_movement * delta_time)
        if self.brightness >= self.max_brightness:
            self.brightness = self.max_brightness - 1
            self.flash_movement = -self.flash_movement
        elif self.brightness <= 0:
            self.brightness = 0
        self.image.set_colorkey((self.brightness + TRANSPARENT[0],) * 3)
        self.image.fill((self.brightness,) * 3, special_flags=pygame.BLEND_RGB_ADD)
        return self.brightness == 0

    def check_collision(self) -> bool:
        if self.x < -self.width:
            self.kill()
            return True
        else:
            return False

    def get_size(self) -> Tuple[int, int]:
        return self.width, self.height

    def get_pos(self) -> Tuple[int, int]:
        return self.x, self.y


class PipeGroup(pygame.sprite.Group):
    def __init__(self, resolution: Tuple[int, int], ground_size: Tuple[int, int]):
        super().__init__()
        self.resolution = resolution
        self.ground_size = ground_size
        self.temp = Pipe(-1, resolution, self.ground_size)
        self.sprite_objects = []
        self.pipe_distance = 213
        self.collide_init = False
        self.flash_pipe = None  # Stores the pipe object that has to be flashed.

    def set_flash_pipe(self, pipe_obj: Pipe) -> None:
        self.flash_pipe = pipe_obj

    def update_flash_pipe(self) -> None:
        if self.flash_pipe is not None:
            self.flash_pipe.flash_tick()

    def generate(self) -> None:
        if self.collide_init:
            self.sprite_objects = [Pipe(x, self.resolution, self.ground_size) for x in range(self.resolution[0], -self.temp.get_size()[0], -(self.temp.get_size()[0] + self.pipe_distance))]
            self.add(self.sprite_objects)
        else:
            self.sprite_objects.append(Pipe(self.resolution[0], self.resolution, self.ground_size))
            self.add(self.sprite_objects[-1])

    def move(self, distance: float = None,
             bird: pygame.sprite.Sprite = None) -> Tuple[bool, Union[pygame.sprite.Sprite, None]]:
        # The value must be converted to positive first, because floor() works differently on negative values.
        whole_steps = math.floor(abs(distance))  # Break the number into an integer and a float
        float_remainder = abs(distance) - whole_steps
        for step in range(whole_steps):
            # Repeat (integer amount) of times, 1 pixel at a time.
            # This ensures the pipe won't move a large amount of pixels in one frame when at a very low frame-rate,
            # and skip over the bird entirely without the collision detection catching it.
            self.update(-1)  # Move back one pixel if colliding.
            result = pygame.sprite.spritecollideany(bird, self, collided=collide_function)
            if result is not None:
                self.update(1)
                return True, result
        self.update(-float_remainder)  # Whatever is left will be less than one, so it can be safely added in one frame.
        result = pygame.sprite.spritecollideany(bird, self, collided=collide_function)
        if result is None:
            return False, None
        else:
            self.update(1)
            return True, result

    def kill_colliding(self) -> None:
        if not self.collide_init:
            self.collide_init = True
        self.sprite_objects[:] = [pipe for pipe in self.sprite_objects if not pipe.check_collision()]
        if len(self.sprite_objects) == 0:
            self.generate()
            return None
        while self.sprite_objects[0].get_pos()[0] < self.resolution[0] - self.temp.get_size()[0] - self.pipe_distance:
            self.sprite_objects.insert(0, Pipe(self.sprite_objects[0].get_pos()[0] + self.temp.get_size()[0] + self.pipe_distance, self.resolution, self.ground_size))
            self.add(self.sprite_objects[0])

    def draw_hit_box(self, surface: pygame.Surface) -> None:
        for pipe in self.sprite_objects:
            pygame.draw.rect(surface, BLACK, pipe.rect, 1)
