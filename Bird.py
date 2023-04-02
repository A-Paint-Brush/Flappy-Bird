from os.path import normpath
from Global import *
import Ground
import Mouse
import Physics
import Pipe
import Time
import Wiggle
import dataclasses
import pygame
import math


class Bird(pygame.sprite.Sprite):
    def __init__(self, resolution: Tuple[int, int], ground_size: Tuple[int, int]):
        super().__init__()
        # region Costume Data
        self.costumes = tuple(pygame.image.load(normpath("./Images/Sprites/{}".format(file))).convert_alpha() for file in ("flap down.png", "flap middle.png", "flap up.png"))
        self.image = self.costumes[0]
        self.costume_index = 0
        self.costume_dir = 1
        self.costume_switch_delay = 0.2
        self.costume_timer = Time.Time()
        self.costume_timer.reset_timer()
        # endregion
        # region Physics Variables
        self.x = 70
        self.y = 200
        self.gravity_speed = 1200
        self.physics = Wiggle.Wiggle()
        self.vertical_span = round((resolution[1] - ground_size[1]) / 2 - self.physics.max_vertical_movement() / 2)
        self.direction = "down"
        self.jump_speed = 370
        # endregion
        self.rect = pygame.Rect(self.x, self.y, *self.image.get_size())
        self.mask = pygame.mask.from_surface(self.image)
        # region Rotation Variables
        self.angle = 0
        self.constant_x = self.x
        self.real_y = self.y  # The y position without the rotation offset.
        self.offset_x = 0
        self.offset_y = 0
        self.starting_rect = self.rect.copy()
        # endregion

    def update_y_pos(self, value: Union[int, float]) -> None:
        """
        Change both the y position with rotation offset (which is needed for collision detection) and the y position
        without rotation offset by the same amount.
        """
        self.y += value
        self.real_y += value

    def init_gravity_physics(self) -> None:
        self.physics = Physics.PreciseAcceleration(acceleration=self.gravity_speed)

    def wiggle_tick(self) -> None:
        self.y = self.vertical_span + round(self.physics.get_y_pos())
        self.real_y = self.y
        self.rect = pygame.Rect(self.x, self.y, *self.image.get_size())

    def tick(self) -> Tuple[Union[int, float], Union[int, float]]:
        if self.direction == "down":
            movement = self.physics.calc()
            if movement[1] > self.gravity_speed:
                total_movement = self.gravity_speed * movement[2]
                speed = self.gravity_speed
            else:
                total_movement = movement[0]
                speed = movement[1]
        elif self.direction == "up":
            movement = self.physics.calc()
            if movement[1] < 0:
                total_movement = 0
                self.physics = Physics.PreciseAcceleration(acceleration=self.gravity_speed)
                self.direction = "down"
                speed = 0
            else:
                total_movement = -movement[0]
                speed = movement[1]
        return speed, total_movement

    def move_collide(self, amount: Union[int, float], pipe_group: Pipe.PipeGroup, collide: bool) -> Union[Tuple[bool, Union[None, pygame.sprite.Sprite]], None]:
        if not collide:
            self.update_y_pos(amount)
            return None
        # Do collision detection with the rotation from the previous frame.
        value = -1 if amount < 0 else +1
        whole_steps = math.floor(abs(amount))
        float_remainder = abs(amount) - whole_steps
        bounds = self.image.get_bounding_rect()
        for step in range(whole_steps):
            self.update_y_pos(value * 1)
            # Break the movement into spans of 1 pixel, and do a mask collision after every pixel movement.
            self.rect = pygame.Rect(self.x, self.y, bounds.width, bounds.height)
            result = pygame.sprite.spritecollideany(self, pipe_group, collided=collide_function)
            if result is not None:
                self.update_y_pos(-value * 1)  # Move in the opposite direction for 1 pixel if colliding.
                return True, result
        self.update_y_pos(value * float_remainder)
        self.rect = pygame.Rect(self.x, self.y, bounds.width, bounds.height)
        result = pygame.sprite.spritecollideany(self, pipe_group, collided=collide_function)
        if result is None:
            return False, None
        else:
            self.update_y_pos(-value * float_remainder)
            return True, result

    def jump(self) -> None:
        self.direction = "up"
        self.physics = Physics.PreciseDeceleration(self.gravity_speed, self.jump_speed)

    def calc_angle(self, speed: Union[int, float], pipe_group: Pipe.PipeGroup, collide: bool) -> Union[Tuple[bool, Union[pygame.sprite.Sprite, None]], None]:
        # x = a' + {(b'-a')/[(b-a)/(c-a)]}
        if speed == 0:
            angle = 0
        else:
            if self.direction == "up":
                # Speed Range: self.jump_speed ~ 1
                # Angle: -(315 ~ 360)
                angle = 315 + ((360 - 315) / ((1 - self.jump_speed) / ((speed - self.jump_speed) or 1)))
            elif self.direction == "down":
                # Speed Range: 1 ~ self.gravity_speed
                # angle: -(0~90)
                angle = 0 + ((90 - 0) / (((self.gravity_speed - 1) or 1) / (speed - 1)))
        if not collide:
            self.set_angle(-round(angle))
            return None
        prev_angle = abs(round(self.angle))
        angle = round(angle)
        while prev_angle != angle:
            prev_angle += (1 if prev_angle < angle else -1)
            self.set_angle(-prev_angle)
            result = pygame.sprite.spritecollideany(self, pipe_group, collided=collide_function)
            if result is not None:
                prev_angle += (1 if prev_angle > angle else -1)  # Rotate in the opposite direction for 1 degree if colliding.
                self.set_angle(-prev_angle)
                return True, result
        return False, None

    def set_angle(self, new_angle: int) -> None:
        self.image = self.costumes[self.costume_index]  # Reset surface to un-rotated image
        self.angle = new_angle
        self.image = pygame.transform.rotate(self.image, self.angle)  # Rotate surface
        new_size = self.image.get_bounding_rect()
        cropped_surface = pygame.Surface((new_size.width, new_size.height))
        cropped_surface.fill(TRANSPARENT)
        cropped_surface.set_colorkey(TRANSPARENT)
        cropped_surface.blit(self.image, (0, 0), area=new_size)
        self.image = cropped_surface  # Crop the unnecessary extra space added by the rotation
        # Calculate the offset needed to center the image after the rotation
        self.offset_x = round((self.starting_rect.width - new_size.width) / 2)
        self.offset_y = round((self.starting_rect.height - new_size.height) / 2)
        self.x = self.constant_x + self.offset_x
        self.y = self.real_y + self.offset_y
        self.rect = pygame.Rect(self.x, self.y, new_size.width, new_size.height)
        self.mask = pygame.mask.from_surface(self.image)

    def increment_costume_num(self) -> None:
        self.costume_index += self.costume_dir
        if self.costume_index == 0 or self.costume_index == len(self.costumes) - 1:
            self.costume_dir = -self.costume_dir

    def tick_costume(self, force_update: bool) -> None:
        time = self.costume_timer.get_time()
        if time > self.costume_switch_delay:
            compensation = time - self.costume_switch_delay
            self.increment_costume_num()
            if compensation > self.costume_switch_delay:
                for i in range(math.floor(compensation / self.costume_switch_delay)):
                    self.increment_costume_num()  # Increment costume.
                compensation %= self.costume_switch_delay
            self.costume_timer.force_elapsed_time(compensation)
            # If you are going to call a different method that will update self.image right after calling this method,
            # pass "False" to the force_update parameter to omit performing the redundant image update.
            if force_update:
                self.image = self.costumes[self.costume_index]
                self.mask = pygame.mask.from_surface(self.image)

    def collision_detection(self, ground_pos: Tuple[Union[int, float], Union[int, float]]) -> Literal[0, 1, 2]:
        """
        Returns an int according to the current collision status.

        | 0: No collision
        | 1: Ground collision
        | 2: Ceiling collision
        """
        if self.y + self.rect.height > ground_pos[1]:
            corrected_y = ground_pos[1] - self.rect.height
            self.update_y_pos(-(self.y - corrected_y))
            self.rect = pygame.Rect(self.x, self.y, self.rect.width, self.rect.height)
            return 1
        elif self.rect.y < 0:
            self.update_y_pos(-self.y)
            self.rect = pygame.Rect(self.x, self.y, self.rect.width, self.rect.height)
            return 2
        else:
            return 0

    def get_rect(self) -> pygame.Rect:
        return self.rect

    def get_mask(self) -> pygame.mask.Mask:
        return self.mask


class BirdManager(pygame.sprite.Group):
    def __init__(self, resolution: Tuple[int, int], z_index: int):
        super().__init__()
        self.resolution = resolution
        self.spawned = False
        self.bird_object = None
        self.clicked = False
        self.z_index = z_index

    def click(self, state_data: dataclasses.dataclass, pipe_group: Pipe.PipeGroup, mouse_object: Mouse.Cursor,
              mouse_initiated: bool) -> None:
        if mouse_initiated:
            if not self.z_index == mouse_object.get_z_index():
                return None
            elif not mouse_object.get_button_state(1):
                self.clicked = False
                return None
        if not mouse_initiated or (mouse_initiated and not self.clicked):
            if mouse_initiated:
                self.clicked = True
            if state_data.game_state == "waiting":
                state_data.game_state = "started"
                pipe_group.generate()
                self.bird_object.init_gravity_physics()
                self.bird_object.jump()
            elif state_data.game_state == "started":
                self.bird_object.jump()
            elif state_data.game_state == "dying":
                pass
        if mouse_initiated:
            mouse_object.increment_z_index()  # It's not possible to fail to interact with the bird :)

    def spawn_bird(self, state_data: dataclasses.dataclass, ground_group: Ground.GroundGroup) -> None:
        if state_data.game_state == "menu":
            self.spawned = True
            self.bird_object = Bird(self.resolution, ground_group.get_size())
            self.add(self.bird_object)
            state_data.game_state = "waiting"

    def die(self, state_data: dataclasses.dataclass) -> None:
        state_data.game_state = "dying"
        self.bird_object.jump()

    def update(self,
               ground_group: Ground.GroundGroup,
               pipe_group: Pipe.PipeGroup,
               state_data: dataclasses.dataclass) -> None:
        if state_data.game_state == "menu":
            pass
        elif state_data.game_state == "waiting":
            self.move_ground_tiles(ground_group)
            self.bird_object.wiggle_tick()
            self.bird_object.tick_costume(force_update=True)
        elif state_data.game_state == "started":
            collision_type, collided_pipe = self.update_all_related_objects(ground_group, pipe_group)
            if collision_type in (1, 2, 3):
                collided_pipe.init_flash()
                pipe_group.set_flash_pipe(collided_pipe)
                self.die(state_data)
            elif collision_type == 4:
                self.die(state_data)
        elif state_data.game_state == "dying":
            speed, movement = self.bird_object.tick()
            self.bird_object.move_collide(movement, None, collide=False)
            self.bird_object.calc_angle(speed, None, collide=False)  # Collision detection is not needed after death.
            pipe_group.update_flash_pipe()

    def update_all_related_objects(self,
                                   ground_group: Ground.GroundGroup,
                                   pipe_group: Pipe.PipeGroup) -> Tuple[int, Union[None, Pipe.Pipe]]:
        self.bird_object.tick_costume(True)
        speed, movement = self.bird_object.tick()
        vertical_collide = self.bird_object.move_collide(movement, pipe_group, True)
        if vertical_collide[0]:
            return 1, vertical_collide[1]
        rotation_collide = self.bird_object.calc_angle(speed, pipe_group, True)
        if rotation_collide[0]:
            return 2, rotation_collide[1]
        amount = self.move_ground_tiles(ground_group)
        pipe_collide = pipe_group.move(amount, self.bird_object)
        if pipe_collide[0]:
            return 3, pipe_collide[1]
        pipe_group.kill_colliding()
        ground_collide = self.bird_object.collision_detection(ground_group.get_pos())
        if ground_collide == 1:
            return 4, None
        return 0, None

    @staticmethod
    def move_ground_tiles(ground_group: Ground.GroundGroup) -> Union[int, float]:
        amount = ground_group.move()
        ground_group.reset_pos()
        return amount

    def draw_(self, surface: pygame.Surface, debug: bool) -> None:
        self.draw(surface)
        if debug:
            pygame.draw.rect(surface, BLACK, self.bird_object.get_rect(), 1)
            self.bird_object.get_mask().to_surface(surface, setcolor=YELLOW, unsetcolor=BLACK)
