from Global import *
import Physics
import Time
import math
import pygame
if TYPE_CHECKING:
    import Ground
    import Mouse
    import Pipe


class Bird(pygame.sprite.Sprite):
    def __init__(self, resolution: Tuple[int, int], ground_size: Tuple[int, int]):
        super().__init__()
        # region Costume Data
        self.costumes = tuple(pygame.image.load(find_abs_path("./Images/Sprites/{}".format(file)))
                              .convert_alpha() for file in ("flap down.png", "flap middle.png", "flap up.png"))
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
        self.wiggle = Physics.Wiggle()
        self.vertical_span = round((resolution[1] - ground_size[1]) / 2 - self.wiggle.max_vertical_movement() / 2)
        self.physics_timer = Time.Time()
        self.terminal_velocity = 700
        self.jump_speed = -360
        self.gravity_accel = 950
        self.current_speed = 0
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

    def wiggle_tick(self) -> None:
        self.y = self.vertical_span + self.wiggle.get_y_pos()
        self.real_y = self.y
        self.rect = pygame.Rect(self.x, self.y, *self.image.get_size())

    def calculate_movement(self) -> Tuple[Union[int, float], Union[int, float]]:
        delta_time = self.physics_timer.get_time()
        self.physics_timer.reset_timer()
        self.current_speed += self.gravity_accel * delta_time
        if self.current_speed > self.terminal_velocity:
            self.current_speed = self.terminal_velocity
        movement = self.current_speed * delta_time
        return self.current_speed, movement

    def move(self, amount: Union[int, float], pipe_group: Optional["Pipe.PipeGroup"],
             ground_pos: Optional[Tuple[Union[int, float],
                                        Union[int, float]]]) -> Tuple[Literal[0, 1, 2], Optional[pygame.sprite.Sprite]]:
        if pipe_group is None:
            self.update_y_pos(amount)
            return 0, None
        shift_count, remainder = divmod(abs(amount), self.rect.height)
        shift_count = math.floor(shift_count)  # To remove the trailing ".0"
        shift_amount = math.copysign(self.rect.height, amount)
        remainder = math.copysign(remainder, amount)
        for i in range(shift_count + 1):
            temp_amount = remainder if i == shift_count else shift_amount
            if temp_amount == 0:
                continue
            self.update_y_pos(temp_amount)
            self.rect = pygame.Rect(self.x, self.y, self.rect.width, self.rect.height)
            result = pygame.sprite.spritecollideany(self, pipe_group, collided=collide_function)
            if result is not None:  # Resolve collision
                opposite_amount = -math.copysign(1, temp_amount)  # 1 pixel in opposite direction
                collided = 0
                while collided is not None:
                    self.update_y_pos(opposite_amount)
                    self.rect = pygame.Rect(self.x, self.y, self.rect.width, self.rect.height)
                    collided = pygame.sprite.spritecollideany(self, pipe_group, collided=collide_function)
                return 1, result
            result = self.y_bounds_collision(ground_pos)
            if result == 1:
                return 2, None
        return 0, None

    def jump(self) -> None:
        if self.wiggle is not None:
            self.physics_timer.reset_timer()
            self.wiggle = None
        self.current_speed = self.jump_speed

    def calc_angle(self, speed: Union[int, float],
                   pipe_group: Optional["Pipe.PipeGroup"]) -> Optional[pygame.sprite.Sprite]:
        if speed <= 0:
            # Speed: 0 ~ self.jump_speed
            # Angle: 0 ~ 45
            angle = 45 * (self.current_speed / self.jump_speed)
        else:
            # Speed Range: 1 ~ self.terminal_velocity
            # angle: -(1 ~ 90)
            angle = -90 * (self.current_speed / self.terminal_velocity)
        self.set_angle(angle)
        if pipe_group is not None:
            return pygame.sprite.spritecollideany(self, pipe_group, collided=collide_function)

    def set_angle(self, new_angle: float) -> None:
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

    def tick_costume(self, force_update: bool = False) -> None:
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

    def pause(self) -> None:
        self.costume_timer.pause()
        if self.wiggle is not None:
            self.wiggle.pause()
        else:
            self.physics_timer.pause()

    def unpause(self) -> None:
        if self.costume_timer.is_paused():
            self.costume_timer.unpause()
            if self.wiggle is not None:
                self.wiggle.unpause()
            else:
                self.physics_timer.unpause()

    def y_bounds_collision(self, ground_pos: Tuple[Union[int, float], Union[int, float]]) -> Literal[0, 1, 2]:
        """
        Returns an integer based on the vertical collision state of the bird. If the bird is colliding with the ground,
        1 will be returned. 2 will be returned if the bird is colliding with the ceiling. If neither is true, 0 is
        returned.
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

    def below_screen(self, resolution: Tuple[int, int]) -> bool:
        """Returns True if the bird has fallen out of the screen."""
        return self.y > resolution[1]

    def get_rect(self) -> pygame.Rect:
        return self.rect

    def get_mask(self) -> pygame.mask.Mask:
        return self.mask


class BirdManager(pygame.sprite.Group):
    def __init__(self, resolution: Tuple[int, int], z_index: int):
        super().__init__()
        self.resolution = resolution
        self.spawned = False
        self.bird_object: Optional[Bird] = None
        self.clicked = False
        self.z_index = z_index

    def process_user_events(self, state_data: Callable[..., Optional[str]], pipe_group: "Pipe.PipeGroup",
                            mouse_object: "Mouse.Cursor", mouse_initiated: bool) -> None:
        if mouse_initiated:
            conditions = (not self.z_index == mouse_object.get_z_index(), not mouse_object.get_button_state(1))
            if any(conditions):
                if conditions[1]:
                    self.clicked = False
                return None
        if not mouse_initiated or (mouse_initiated and not self.clicked):
            self.clicked = True if mouse_initiated else self.clicked  # Don't change value if 'self.clicked' is False.
            if state_data() == "waiting":
                state_data("started")
                pipe_group.generate()
                self.bird_object.jump()
            elif state_data() == "started":
                self.bird_object.jump()
        if mouse_initiated:
            mouse_object.increment_z_index()  # It's not possible to fail to interact with the bird :)

    def spawn_bird(self, state_data: Callable[..., Optional[str]],
                   ground_group: "Ground.GroundGroup") -> None:
        if state_data() == "menu":
            self.spawned = True
            self.bird_object = Bird(self.resolution, ground_group.get_size())
            self.add(self.bird_object)
            state_data("waiting")

    def update(self, ground_group: "Ground.GroundGroup", pipe_group: "Pipe.PipeGroup",
               state_data: Callable[..., Optional[str]], dying_binding: Callable[[], None],
               game_over_binding: Callable[[], None]) -> None:
        if state_data() == "waiting":
            self.move_ground_tiles(ground_group)
            self.bird_object.wiggle_tick()
            self.bird_object.tick_costume(True)
        elif state_data() == "started":
            collision_type, collided_pipe = self.update_all(ground_group, pipe_group)
            if collision_type:
                if collision_type == 1:  # Cause of death was colliding with a pipe
                    collided_pipe.init_flash()
                    pipe_group.set_flash_pipe(collided_pipe)
                state_data("dying")
                dying_binding()
                self.bird_object.jump()
        elif state_data() == "dying":
            speed, movement = self.bird_object.calculate_movement()
            self.bird_object.move(movement, None, None)  # Collision detection is not needed after death.
            self.bird_object.calc_angle(speed, None)
            pipe_group.update_flash_pipe()  # Updates the pipe that killed the bird if the bird was killed by a pipe.
            if self.spawned and self.bird_object.below_screen(self.resolution):
                self.spawned = False
                game_over_binding()

    def update_all(self, ground_group: "Ground.GroundGroup",
                   pipe_group: "Pipe.PipeGroup") -> Tuple[Literal[0, 1, 2], Optional[pygame.sprite.Sprite]]:
        """Returns a two-item tuple with the first item being the integer 0 if not colliding with anything, 1 if
        colliding with a pipe, and 2 if colliding with the ground. When the first item is the integer 1, the second item
        will contain the pipe instance that the bird is colliding with, else it would be None."""
        self.bird_object.tick_costume()
        speed, movement = self.bird_object.calculate_movement()
        for i, cf in enumerate((lambda: self.bird_object.calc_angle(speed, pipe_group),
                                lambda: self.bird_object.move(movement, pipe_group, ground_group.get_pos()),
                                lambda: pipe_group.move(self.move_ground_tiles(ground_group), self.bird_object))):
            collision = cf()
            if i == 1 and collision[0] != 0:
                return collision
            elif i in (0, 2) and collision is not None:
                return 1, collision
        pipe_group.kill_colliding()
        return 0, None

    def pause(self) -> None:
        if self.bird_object is not None:
            self.bird_object.pause()

    def unpause(self) -> None:
        if self.bird_object is not None:
            self.bird_object.unpause()

    @staticmethod
    def move_ground_tiles(ground_group: "Ground.GroundGroup") -> float:
        amount = ground_group.move()
        ground_group.reset_pos()
        return amount

    def advanced_draw(self, surface: pygame.Surface, debug: bool) -> None:
        self.draw(surface)
        if debug:
            pygame.draw.rect(surface, BLACK, self.bird_object.get_rect(), 1)
            self.bird_object.get_mask().to_surface(surface, setcolor=WHITE, unsetcolor=BLACK)
