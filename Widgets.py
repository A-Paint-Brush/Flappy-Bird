from Global import *
import Mouse
import Time
import pygame


class BaseWidget(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

    def update(self, mouse_obj: Mouse.Cursor, keyboard_event: pygame.event.Event):
        pass


class AnimatedSurface(BaseWidget):
    def __init__(self,
                 x: Union[int, float],
                 y: Union[int, float],
                 surface: pygame.Surface,
                 callback: Union[Callable[[], None], None]):
        super().__init__()
        # region Setup
        self.real_x = x  # The x and y position without resize offset.
        self.real_y = y
        self.x = self.real_x
        self.y = self.real_y
        self.original_surface = surface
        self.original_width, self.original_height = self.original_surface.get_size()
        self.image = self.original_surface.copy()
        # endregion
        self.current_width = self.original_width
        self.current_height = self.original_height
        self.max_width = self.original_width + 60
        self.min_width = self.original_width
        self.reducing_fraction = 0.8
        self.aspect_ratio = self.original_height / self.original_width
        self.resize_state = "small"  # Literal["small", "large", "dilating", "shrinking"]
        self.callback_func = callback  # Stores the reference to the function to call when clicked.
        self.delta_timer = Time.Time()
        self.rect = pygame.Rect(self.x, self.y, self.original_width, self.original_height)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, mouse_obj: Mouse.Cursor, keyboard_event: pygame.event.Event) -> None:
        collide = pygame.sprite.collide_mask(self, mouse_obj)
        if collide is None:
            self.change_size("decrease")
        else:
            self.change_size("increase")
        if mouse_obj.get_button_state(1) and (self.callback_func is not None):
            self.callback_func()

    def set_size(self, new_size: float) -> None:
        self.current_width = round(new_size)
        self.current_height = round(self.current_width * self.aspect_ratio)
        offset_x = round((self.original_width - self.current_width) / 2)
        offset_y = round((self.original_height - self.current_height) / 2)
        self.x = self.real_x + offset_x
        self.y = self.real_y + offset_y
        self.image = pygame.transform.scale(self.original_surface, (self.current_width, self.current_height))
        self.rect = pygame.Rect(self.x, self.y, self.current_width, self.current_height)
        self.mask = pygame.mask.from_surface(self.image)

    def calc_physics(self, delta_time: float, mode: Literal["dilating", "shrinking"]) -> float:
        return self.original_width + (self.max_width - self.current_width if mode == "dilating" else self.current_width - self.min_width) * (self.reducing_fraction / (delta_time if delta_time > 1 else 1))

    def change_size(self, direction: Literal["increase", "decrease"]) -> None:
        if (self.resize_state == "small" and direction == "decrease") or (self.resize_state == "large" and direction == "increase"):
            return None
        skip_delta_time = False
        if self.resize_state in ("small", "large"):
            skip_delta_time = True
        self.resize_state = {"increase": "dilating", "decrease": "shrinking"}[direction]
        temp_width = self.calc_physics(1 if skip_delta_time else self.delta_timer.get_time(), self.resize_state)
        self.delta_timer.reset_timer()
        self.set_size(temp_width)
        if temp_width == self.max_width:
            self.resize_state = "large"
        elif temp_width == self.min_width:
            self.resize_state = "small"


class WidgetGroup(pygame.sprite.Group):
    def __init__(self, z_index: int):
        super().__init__()
        self.z_index = z_index
        self.child_widgets = []
