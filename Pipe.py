from os.path import normpath
from Global import *
import random
import pygame
import Ground
import Time


class Pipe(Ground.Tile):
    def __init__(self, x_pos, resolution, ground_size):
        super().__init__(x_pos, resolution)
        self.pipe_image = pygame.image.load(normpath("./Images/Pipe.png")).convert_alpha()
        self.width, self.height = self.pipe_image.get_size()
        self.resolution = list(resolution)
        self.resolution[1] -= ground_size[1]
        self.x = x_pos
        self.y = 0
        # The shortest pipe length allowed: 86
        # Minimum value of bottom pipe y position: y = min_length + constant (constant > bird_height)
        # Maximum value of bottom pipe y position: y = resolution[1] - min_length
        # Y position of top pipe: bottom_pipe_y - constant
        self.gap_distance = 95
        self.min_length = 86
        self.bottom_pipe_pos = (0, random.randint(self.min_length + self.gap_distance, self.resolution[1] - self.min_length))
        self.top_pipe_pos = (0, self.bottom_pipe_pos[1] - self.gap_distance - self.height)
        self.image = pygame.Surface((self.width, self.resolution[1]))
        # Uses the RLEACCEL flag to improve the blit performance, since the surface is only modified on creation.
        self.image.set_colorkey(BLACK, pygame.RLEACCEL)
        self.image.fill(BLACK)
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

    def update(self, movement):
        self.x += movement
        self.rect = pygame.Rect(self.x, self.y, self.width, self.resolution[1])

    def init_flash(self):
        self.flash_timer.reset_timer()
        self.flash_timer.get_time()

    def flash_tick(self):
        prev_time = self.flash_timer.get_prev_time()
        delta_time = self.flash_timer.get_time() - prev_time
        self.image = self.original_surface.copy()
        self.brightness += round(self.flash_movement * delta_time)
        if self.brightness >= self.max_brightness:
            self.brightness = self.max_brightness - 1
            self.flash_movement = -self.flash_movement
        elif self.brightness <= 0:
            self.brightness = 0
        self.image.set_colorkey((self.brightness,) * 3, pygame.RLEACCEL)
        self.image.fill((self.brightness,) * 3, special_flags=pygame.BLEND_RGB_ADD)
        return self.brightness == 0


class PipeGroup(Ground.GroundGroup):
    def __init__(self, resolution, ground_size):
        super().__init__(resolution)
        self.resolution = resolution
        self.ground_size = ground_size
        self.temp = Pipe(-1, resolution, self.ground_size)
        self.pipe_distance = 170
        self.collide_init = False

    def generate(self):
        if self.collide_init:
            self.sprite_objects = [Pipe(x, self.resolution, self.ground_size) for x in range(self.resolution[0], -self.temp.get_size()[0], -(self.temp.get_size()[0] + self.pipe_distance))]
            self.add(self.sprite_objects)
        else:
            self.sprite_objects.append(Pipe(self.resolution[0], self.resolution, self.ground_size))
            self.add(self.sprite_objects[-1])

    def move(self, distance=None, bird=None):
        self.update(distance)
        result = pygame.sprite.spritecollideany(bird, self, collided=collide_function)
        if result is None:
            return False, None
        first_collision = result
        while result is not None:
            self.update(1)
            result = pygame.sprite.spritecollideany(bird, self, collided=collide_function)
        return True, first_collision

    def kill_colliding(self):
        if not self.collide_init:
            self.collide_init = True
        self.sprite_objects[:] = [pipe for pipe in self.sprite_objects if not pipe.check_collision()]
        if len(self.sprite_objects) == 0:
            self.generate()
            return None
        while self.sprite_objects[0].get_pos()[0] < self.resolution[0] - self.temp.get_size()[0] - self.pipe_distance:
            self.sprite_objects.insert(0, Pipe(self.sprite_objects[0].get_pos()[0] + self.temp.get_size()[0] + self.pipe_distance, self.resolution, self.ground_size))
            self.add(self.sprite_objects[0])

    def draw_hit_box(self, surface):
        for pipe in self.sprite_objects:
            pygame.draw.rect(surface, BLACK, pipe.get_rect(), 1)
