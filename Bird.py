from os.path import normpath
import Wiggle
import Physics
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
        self.jump_speed = 700
        # endregion
        self.rect = pygame.Rect(self.x, self.y, *self.image.get_size())
        # region Rotation Variables
        self.angle = 0
        self.constant_x = self.x
        self.prev_y = self.y  # The y position without the rotation offset
        self.starting_size = (self.rect.width, self.rect.height)
        # endregion
        self.mask = pygame.mask.from_surface(self.image)

    def update_y_pos(self, value):
        self.y += value
        self.prev_y += value

    def init_gravity_physics(self):
        self.physics = Physics.PreciseAcceleration(acceleration=self.gravity_speed)

    def wiggle_tick(self):
        self.y = self.vertical_span + round(self.physics.get_y_pos())
        self.prev_y = self.y
        self.rect = pygame.Rect(self.x, self.y, *self.image.get_size())

    def tick(self):
        if self.direction == "down":
            movement = self.physics.calc()
            if movement[1] > self.gravity_speed:
                self.update_y_pos(round(self.gravity_speed * movement[2]))
                speed = self.gravity_speed
            else:
                self.update_y_pos(round(movement[0]))
                speed = movement[1]
        elif self.direction == "up":
            movement = self.physics.calc()
            if movement[1] < 0:
                self.physics = Physics.PreciseAcceleration(acceleration=self.gravity_speed)
                self.direction = "down"
                speed = 0
            else:
                self.update_y_pos(-round(movement[0]))
                speed = movement[1]
        return speed

    def jump(self):
        self.direction = "up"
        self.physics = Physics.PreciseDeceleration(self.gravity_speed, self.jump_speed)

    def calc_angle(self, speed):
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
        return self.set_angle(-round(angle))

    def set_angle(self, new_angle):
        self.image = self.costumes[self.calc_costume_num()]
        self.angle = new_angle
        self.image = pygame.transform.rotate(self.image, self.angle)
        old_size = self.starting_size
        new_size = self.image.get_size()
        self.x = self.constant_x + (old_size[0] - new_size[0]) // 2
        self.y = self.prev_y + (old_size[1] - new_size[1]) // 2
        bounds = self.image.get_bounding_rect()
        self.rect = pygame.Rect(self.x + bounds.topleft[0], self.y + bounds.topleft[1], bounds.width, bounds.height)
        self.mask = pygame.mask.from_surface(self.image)
        return new_size

    def tick_costume(self, force_update=False):
        if self.costume_timer.get_time() > self.costume_switch_delay:
            self.costume_timer.reset_timer()
            self.costume_index += 1
            self.costume_index %= 4
            if force_update:
                self.image = self.costumes[self.calc_costume_num()]

    def collision_detection(self, ground_pos):
        """Returns an int according to the current collision status.

        0: No collision
        1: Ground collision
        2: Ceiling collision
        """
        bounds = self.image.get_bounding_rect()
        collide_rect = pygame.Rect(self.x + bounds.topleft[0], self.y + bounds.topleft[1], bounds.width, bounds.height)
        if collide_rect.y + collide_rect.height > ground_pos[1]:
            corrected_y = ground_pos[1] - collide_rect.height
            self.update_y_pos(-(collide_rect.y - corrected_y))
            self.rect = pygame.Rect(collide_rect.x, self.y + bounds.topleft[1], collide_rect.width, collide_rect.height)
            return 1
        elif collide_rect.y < -collide_rect.height:
            self.update_y_pos(-self.image.get_size()[1] - collide_rect.y)
            self.rect = pygame.Rect(collide_rect.x, self.y + bounds.topleft[1], collide_rect.width, collide_rect.height)
            return 2
        else:
            return 0

    def draw(self, surface, show_hit_box=False):
        surface.blit(self.image, (self.x, self.y))
        if show_hit_box:
            pygame.draw.rect(surface, (0, 0, 0), self.rect, 1)
