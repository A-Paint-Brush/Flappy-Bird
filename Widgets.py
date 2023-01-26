from Global import *
import math
import Mouse
import Time
import pygame


class BaseWidget(pygame.sprite.Sprite):
    def __init__(self, widget_name: str = "!base_widget"):
        super().__init__()
        self.widget_name = widget_name

    def update(self, mouse_obj: Mouse.Cursor, keyboard_event: pygame.event.Event) -> None:
        pass

    def get_widget_name(self) -> str:
        return self.widget_name


class AnimatedSurface(BaseWidget):
    def __init__(self,
                 x: Union[int, float],
                 y: Union[int, float],
                 surface: pygame.Surface,
                 callback: Optional[Callable[[], None]],
                 widget_name: str = "!animated_surf"):
        super().__init__(widget_name)
        # region Sprite Data
        self.real_x = x  # The x and y position without resize offset.
        self.real_y = y
        self.x = self.real_x
        self.y = self.real_y
        self.original_surface = surface
        self.original_width, self.original_height = self.original_surface.get_size()
        self.image = self.original_surface.copy()
        self.current_width = self.original_width
        self.current_height = self.original_height
        self.max_width = self.original_width + 60
        self.min_width = self.original_width
        self.aspect_ratio = self.original_height / self.original_width
        # endregion
        # region Flash Animation Data
        self.brightness = 1
        self.max_brightness = 100
        self.brighten_step = 330
        self.flash_state = "idle"  # Literal["idle", "brighten", "darken"]
        self.flash_timer = Time.Time()
        # endregion
        # region Resize Animation Data
        self.difference = self.max_width - self.min_width
        self.reducing_fraction = 0.2
        self.resize_state = "small"  # Literal["small", "large", "dilating", "shrinking"]
        self.delta_timer = Time.Time()
        self.delta_timer.reset_timer()
        # endregion
        self.lock = True
        self.mouse_down = False
        self.callback_func = callback  # Stores the reference to the function to call when clicked.
        self.rect = pygame.Rect(self.x, self.y, self.original_width, self.original_height)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, mouse_obj: Mouse.Cursor, keyboard_event: pygame.event.Event) -> None:
        # region Tick Size
        collide = pygame.sprite.collide_mask(self, mouse_obj)
        if collide is None:
            if not mouse_obj.get_button_state(1):
                # Cancel click if mouse is released after being dragged off the button.
                self.mouse_down = False
            self.lock = True
            self.change_size("decrease")
        else:
            if mouse_obj.get_button_state(1) and (not self.lock):
                self.mouse_down = True
            elif (not mouse_obj.get_button_state(1)) and self.mouse_down:
                self.mouse_down = False
                if self.callback_func is not None:
                    self.flash_timer.reset_timer()
                    self.flash_state = "brighten"  # Start flash animation.
                    self.callback_func()  # Fire button-click event.
            if not mouse_obj.get_button_state(1):
                self.lock = False
            self.change_size("increase")
        # endregion
        # region Tick Brightness
        delta_time = self.flash_timer.get_time()
        self.flash_timer.reset_timer()
        if self.flash_state != "idle":
            if self.flash_state == "brighten":
                self.brightness += self.brighten_step * delta_time
                if self.brightness >= self.max_brightness:
                    self.brightness = self.max_brightness
                    self.flash_state = "darken"
            elif self.flash_state == "darken":
                self.brightness -= self.brighten_step * delta_time
                if self.brightness <= 1:
                    self.brightness = 1
                    self.flash_state = "idle"
            # Obtain the button surface that is at the correct size, but not brightened.
            if self.resize_state == "small":
                # Copy from original surface if resizing is not needed.
                self.image = self.original_surface.copy()
            elif self.resize_state == "large":
                # Scale original surface to max size.
                self.image = pygame.transform.scale(self.original_surface,
                                                    (self.max_width, self.max_width * self.aspect_ratio))
            # If button is currently changing size, the surface will already be the un-brightened version.
            self.image.fill((self.brightness,) * 3, special_flags=pygame.BLEND_RGB_ADD)
            # endregion

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

    def calc_physics(self, delta_time: float, direction: Literal["increase", "decrease"]) -> float:
        self.difference *= math.pow(self.reducing_fraction, delta_time)
        if self.resize_state == "dilating" and direction == "decrease" or \
                self.resize_state == "shrinking" and direction == "increase":
            self.difference = self.max_width - self.min_width - self.difference
            self.resize_state = "shrinking" if self.resize_state == "dilating" else "dilating"
        new_width = None
        if direction == "increase":
            new_width = self.max_width - self.difference
        elif direction == "decrease":
            new_width = self.min_width + self.difference
        if round(new_width) == self.min_width:
            self.resize_state = "small"
            self.difference = self.max_width - self.min_width
        elif round(new_width) == self.max_width:
            self.resize_state = "large"
            self.difference = self.max_width - self.min_width
        return new_width

    def change_size(self, direction: Literal["increase", "decrease"]) -> None:
        if (self.resize_state, direction) in (("small", "decrease"), ("large", "increase")):  # Guard clause
            self.delta_timer.reset_timer()
            return None
        if self.resize_state == "small":
            self.resize_state = "dilating"
        elif self.resize_state == "large":
            self.resize_state = "shrinking"
        self.set_size(self.calc_physics(self.delta_timer.get_time(), direction))
        self.delta_timer.reset_timer()


class WidgetCanvas(BaseWidget):
    def __init__(self,
                 x: float,
                 y: float,
                 width: int,
                 height: int,
                 widget_name: str = "!widget_canvas"):
        super().__init__(widget_name)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        # Using per-pixel alpha is necessary because we don't know what colors the surface returned by
        # `pygame.font.Font.render` might contain, and the surfaces of most child widgets will contain text.
        self.image = pygame.Surface((width, height), flags=pygame.SRCALPHA)
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.child_widgets = {}

    def add_widget(self, widget_obj: BaseWidget) -> None:
        if widget_obj.get_widget_name() in self.child_widgets:
            raise WidgetAppendError(widget_obj)
        else:
            self.child_widgets[widget_obj.get_widget_name()] = widget_obj

    def update(self, mouse_obj: Mouse.Cursor, keyboard_event: pygame.event.Event) -> None:
        abs_pos = mouse_obj.get_pos()
        rel_mouse = mouse_obj.copy()
        rel_mouse.set_pos(abs_pos[0] - self.x, abs_pos[1] - self.y)
        for widget in self.child_widgets.values():
            widget.update(rel_mouse, keyboard_event)
        self.render_widgets()

    def render_widgets(self) -> None:
        self.image.fill((0, 0, 0, 0))
        for w in self.child_widgets.values():
            self.image.blit(w.image, w.rect)


class WidgetGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.child_canvases = {}

    def add_widget_canvas(self, canvas_obj: WidgetCanvas):
        if canvas_obj.get_widget_name() in self.child_canvases:
            raise CanvasAppendError(canvas_obj)
        else:
            self.child_canvases[canvas_obj.get_widget_name()] = canvas_obj
            self.add(canvas_obj)


class WidgetAppendError(Exception):
    def __init__(self, widget: BaseWidget):
        super().__init__("The WidgetCanvas already contains a widget with the ID '{}'".format(widget.get_widget_name()))
        self.failed_widget = widget

    def get_failed_widget(self) -> BaseWidget:
        return self.failed_widget


class CanvasAppendError(Exception):
    def __init__(self, canvas: WidgetCanvas):
        super().__init__("The WidgetGroup already contains a WidgetCanvas with the ID '{}'"
                         .format(canvas.get_widget_name()))
        self.failed_canvas = canvas

    def get_failed_canvas(self) -> WidgetCanvas:
        return self.failed_canvas
