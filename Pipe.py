from os.path import normpath
from Global import *
import Counters
import Time
import math
import random
import pygame
if TYPE_CHECKING:
    import Bird


class Pipe(pygame.sprite.Sprite):
    def __init__(self, x_pos: int, resolution: Tuple[int, int], ground_size: Tuple[int, int]):
        super().__init__()
        self.pipe_image = pygame.image.load(normpath("Images/Sprites/pipe.png")).convert_alpha()
        self.width, self.height = self.pipe_image.get_size()
        self.resolution = list(resolution)
        self.resolution[1] -= ground_size[1]
        self.x = x_pos
        self.y = 0
        self.gap_distance = 145
        self.min_length = 66
        self.bottom_pipe_pos = (0, random.randint(self.min_length + self.gap_distance,
                                                  self.resolution[1] - self.min_length))
        self.top_pipe_pos = (0, self.bottom_pipe_pos[1] - self.gap_distance - self.height)
        self.bird_passed = False
        self.image = pygame.Surface((self.width, self.resolution[1]))
        # Use the RLEACCEL flag to improve blit performance, since the surface is only modified on creation.
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

    def flash_pause(self) -> None:
        self.flash_timer.pause()

    def flash_unpause(self) -> None:
        if self.flash_timer.is_paused():
            self.flash_timer.unpause()

    def check_collision(self) -> bool:
        if self.x < -self.width:
            self.kill()
            return True
        else:
            return False

    def check_passed(self, bird: "Bird.Bird") -> bool:
        if self.bird_passed:
            return False
        pipe_mid = self.x + self.width / 2
        bird_mid = bird.x + bird.get_rect().width / 2
        if pipe_mid <= bird_mid:
            self.bird_passed = True
            return True

    def get_size(self) -> Tuple[int, int]:
        return self.width, self.height

    def get_pos(self) -> Tuple[int, int]:
        return self.x, self.y


class PipeGroup(pygame.sprite.Group):
    def __init__(self,
                 resolution: Tuple[int, int],
                 ground_size: Tuple[int, int],
                 font_height: int = 70,
                 kerning: int = 5):
        super().__init__()
        self.resolution = resolution
        self.ground_size = ground_size
        self.temp = Pipe(-1, resolution, self.ground_size)
        self.score = Counters.Score(font_height, kerning)
        self.sprite_objects: List[Pipe] = []
        self.pipe_distance = 213
        self.collide_init = False
        self.flash_pipe: Optional[Pipe] = None  # Stores the pipe object that has to be flashed.

    def set_flash_pipe(self, pipe_obj: pygame.sprite.Sprite) -> None:
        self.flash_pipe = pipe_obj

    def update_flash_pipe(self) -> None:
        if self.flash_pipe is not None:
            self.flash_pipe.flash_tick()

    def pause_flash(self) -> None:
        if self.flash_pipe is not None:
            self.flash_pipe.flash_pause()

    def unpause_flash(self) -> None:
        if self.flash_pipe is not None:
            self.flash_pipe.flash_unpause()

    def generate(self) -> None:
        if self.collide_init:
            self.sprite_objects = [
                Pipe(x, self.resolution, self.ground_size) for x in range(self.resolution[0], -self.temp.get_size()[0],
                                                                          -(self.temp.get_size()[0]
                                                                            + self.pipe_distance))
            ]
            self.add(self.sprite_objects)
        else:
            self.sprite_objects.append(Pipe(self.resolution[0], self.resolution, self.ground_size))
            self.add(self.sprite_objects[-1])

    def move(self, distance: float, bird: "Bird.Bird") -> Optional[pygame.sprite.Sprite]:
        pipe_width = self.temp.get_size()[0]
        shift_count, remainder = divmod(abs(distance), pipe_width)
        shift_count = math.floor(shift_count)
        shift_amount = math.copysign(pipe_width, distance)
        remainder = math.copysign(remainder, distance)
        for i in range(shift_count + 1):
            temp_amount = remainder if i == shift_count else shift_amount
            if temp_amount == 0:
                continue
            self.update(temp_amount)
            result = pygame.sprite.spritecollideany(bird, self, collided=collide_function)
            if result is not None:
                opposite_amount = -math.copysign(1, temp_amount)
                collided = 0
                while collided is not None:
                    self.update(opposite_amount)
                    collided = pygame.sprite.spritecollideany(bird, self, collided=collide_function)
                return result
        self.check_score(bird)

    def check_score(self, bird: "Bird.Bird") -> None:
        for pipe in self.sprite_objects:
            if pipe.check_passed(bird):
                self.score.change_score(1, "change")
                break

    def kill_colliding(self) -> None:
        if not self.collide_init:
            self.collide_init = True
        self.sprite_objects[:] = [pipe for pipe in self.sprite_objects if not pipe.check_collision()]
        if len(self.sprite_objects) == 0:
            self.generate()
            return None
        while self.sprite_objects[0].get_pos()[0] < self.resolution[0] - self.temp.get_size()[0] - self.pipe_distance:
            self.sprite_objects.insert(0, Pipe(self.sprite_objects[0].get_pos()[0]
                                               + self.temp.get_size()[0]
                                               + self.pipe_distance, self.resolution, self.ground_size))
            self.add(self.sprite_objects[0])

    def draw_hit_box(self, surface: pygame.Surface) -> None:
        for pipe in self.sprite_objects:
            pygame.draw.rect(surface, BLACK, pipe.rect, 1)

    def get_score_obj(self) -> Counters.Score:
        return self.score
