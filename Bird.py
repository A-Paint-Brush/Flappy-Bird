from os.path import normpath
from Global import *
import Wiggle
import Physics
import math
import pygame
import Time


class Bird(pygame.sprite.Sprite):
    def __init__(self, resolution, ground_size):
        super().__init__()
        self.costumes = tuple(pygame.image.load(normpath("./Images/{}".format(file))).convert_alpha() for file in ("flap down.png", "flap middle.png", "flap up.png"))
        self.costume_index = -1
        self.costume_switch_delay = 0.2
        self.costume_timer = Time.Time()
        self.costume_timer.reset_timer()
        self.image = self.costumes[0]
        self.calc_costume_num = lambda: round((4 * 1 / 4) * abs(((self.costume_index - 4 / 2) % 4) - 4 / 2) - 1 + 1)
        self.x = 70
        self.y = 200
        # region Physics Variables
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

    def update_y_pos(self, value):
        """
        Change both the y position with rotation offset (which is needed for collision detection) and the y position
        without rotation offset by the same amount.
        """
        self.y += value
        self.real_y += value

    def init_gravity_physics(self):
        self.physics = Physics.PreciseAcceleration(acceleration=self.gravity_speed)

    def wiggle_tick(self):
        self.y = self.vertical_span + round(self.physics.get_y_pos())
        self.real_y = self.y
        self.rect = pygame.Rect(self.x, self.y, *self.image.get_size())

    def tick(self):
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

    def move_collide(self, amount, pipe_group, collide=True):
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
            # Break the movement into spans of 1 pixels, and do a mask collision after every pixel movement.
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

    def jump(self):
        self.direction = "up"
        self.physics = Physics.PreciseDeceleration(self.gravity_speed, self.jump_speed)

    def calc_angle(self, speed, pipe_group, collide=True):
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
        prev_angle = abs(self.angle)
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

    def set_angle(self, new_angle):
        self.image = self.costumes[self.calc_costume_num()]  # Reset surface to un-rotated image
        self.angle = new_angle
        self.image = pygame.transform.rotate(self.image, self.angle)  # Rotate surface
        new_size = self.image.get_bounding_rect()
        cropped_surface = pygame.Surface((new_size.width, new_size.height))
        cropped_surface.set_colorkey(BLACK)
        cropped_surface.blit(self.image, (0, 0), area=new_size)
        self.image = cropped_surface  # Crop the unnecessary extra space added by the rotation
        # Calculate the offset needed to center the image after the rotation
        self.offset_x = round((self.starting_rect.width - new_size.width) / 2)
        self.offset_y = round((self.starting_rect.height - new_size.height) / 2)
        self.x = self.constant_x + self.offset_x
        self.y = self.real_y + self.offset_y
        self.rect = pygame.Rect(self.x, self.y, new_size.width, new_size.height)
        self.mask = pygame.mask.from_surface(self.image)

    def tick_costume(self, force_update=False):
        if self.costume_timer.get_time() > self.costume_switch_delay:
            self.costume_timer.reset_timer()
            self.costume_index += 1
            self.costume_index %= 4
            # Updating the image is unnecessary once the game is started because set_angle() will do it.
            if force_update:
                self.image = self.costumes[self.calc_costume_num()]
                self.mask = pygame.mask.from_surface(self.image)

    def collision_detection(self, ground_pos):
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

    def draw(self, surface, show_hit_box=False):
        surface.blit(self.image, (self.x, self.y))
        if show_hit_box:
            pygame.draw.rect(surface, (0, 0, 0), self.rect, 1)
            self.mask.to_surface(surface, setcolor=YELLOW, unsetcolor=BLACK)
