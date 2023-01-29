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


class Button(AnimatedSurface):
    def __init__(self,
                 x: Union[int, float],
                 y: Union[int, float],
                 width: int,
                 height: int,
                 border: int,
                 fg: Tuple[int, int, int],
                 bg: Tuple[int, int, int],
                 font: pygame.font.Font,
                 text: str,
                 callback: Optional[Callable[[], None]],
                 widget_name: str = "!button"):
        button_surf = pygame.Surface((width, height), flags=pygame.SRCALPHA)
        button_surf.fill((0, 0, 0, 0))
        draw_button(button_surf, 0, 0, width, height, border, fg, bg, font, text)
        super().__init__(x, y, button_surf, callback, widget_name)


class WordWrappedText:
    def __init__(self, text: str, fg: Tuple[int, int, int], width: int, font: pygame.font.Font):
        self.text_lines = word_wrap_text(text, width, font)
        self.line_height = font.size("|")[1]
        self.image = pygame.Surface((width, self.line_height * len(self.text_lines)), flags=pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))
        for index, text in enumerate(self.text_lines):
            size = font.size(text)
            surface = font.render(text, True, fg)
            self.image.blit(surface, (width / 2 - size[0] / 2, index * self.line_height))

    def get_surface(self) -> pygame.Surface:
        return self.image


class Checkbox(BaseWidget):
    def __init__(self,
                 x: Union[int, float],
                 y: Union[int, float],
                 label_text: str,
                 text_color: Tuple[int, int, int],
                 bg: Tuple[int, int, int],
                 width: int,
                 font: pygame.font.Font,
                 padding: int,
                 border: int,
                 widget_name: str = "!checkbox"):
        super().__init__(widget_name)
        self.x = x
        self.y = y
        self.button_length = 35
        self.button_radius = 10
        self.text_lines = word_wrap_text(label_text, width - padding * 3 - self.button_length, font)
        self.line_height = font.size("|")[1]
        self.checked = False
        self.image = pygame.Surface((width,
                                     padding * 2 + self.line_height * len(self.text_lines)), flags=pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))
        draw_rounded_rect(self.image, 0, 0, *self.image.get_size(), self.button_radius, bg)
        for index, text in enumerate(self.text_lines):
            surface = font.render(text, True, text_color)
            self.image.blit(surface, (padding * 2 + self.button_length, padding + self.line_height * index))
        self.rect = pygame.Rect(self.x, self.y, *self.image.get_size())
        self.__button = Box(padding, padding, self.button_length, self.button_radius, border)

    def update(self, mouse_obj: Mouse.Cursor, keyboard_event: pygame.event.Event) -> None:
        abs_pos = mouse_obj.get_pos()
        rel_mouse = mouse_obj.copy()
        rel_mouse.set_pos(abs_pos[0] - self.x, abs_pos[1] - self.y)
        self.__button.update(rel_mouse)
        self.image.blit(self.__button.image, self.__button.rect)

    def get_data(self) -> bool:
        return self.__button.get_data()

    def get_size(self) -> Tuple[int, int]:
        return self.image.get_size()


class Box(pygame.sprite.Sprite):
    def __init__(self,
                 x: Union[int, float],
                 y: Union[int, float],
                 length: int,
                 radius: int,
                 border: int):
        super().__init__()
        self.length = length
        self.radius = radius
        self.border = border
        self.lock = True
        self.mouse_down = False
        self.checked = False
        self.x = x
        self.y = y
        self.image = pygame.Surface((length, length), flags=pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))
        self.normal_color = GREY
        self.active_color = CYAN
        self.current_color = self.normal_color
        draw_rounded_rect(self.image, 0, 0, length, length, radius, BLACK)
        draw_rounded_rect(self.image,
                          border,
                          border,
                          length - border * 2,
                          length - border * 2,
                          radius - border,
                          self.normal_color)
        self.rect = pygame.Rect(self.x, self.y, length, length)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, mouse_obj: Mouse.Cursor) -> None:
        collide = pygame.sprite.collide_mask(self, mouse_obj)
        if collide is None:
            if not mouse_obj.get_button_state(1):
                self.mouse_down = False
            self.lock = True
            self.current_color = self.normal_color
        else:
            if mouse_obj.get_button_state(1) and (not self.lock):
                self.mouse_down = True
            elif (not mouse_obj.get_button_state(1)) and self.mouse_down:
                self.mouse_down = False
                self.checked = not self.checked
            if not mouse_obj.get_button_state(1):
                self.lock = False
            self.current_color = self.active_color
        draw_rounded_rect(self.image,
                          self.border,
                          self.border,
                          self.length - self.border * 2,
                          self.length - self.border * 2,
                          self.radius - self.border,
                          self.current_color)
        if self.checked:
            pygame.draw.lines(self.image, BLACK, False, ((5, self.length / 2 + 3),
                                                         (self.length / 2 - 5, self.length - 5),
                                                         (self.length - 5, 5)), 3)

    def get_data(self) -> bool:
        return self.checked


class RadioGroup:
    def __init__(self, default: int = 0):
        super().__init__()
        self.default = default
        self.counter_id = 0
        self.selected_id = default
        self.children = []

    def add_radio_button(self, *args) -> None:
        radio_button = RadioButton(self.counter_id, self.update_selection, self.counter_id == self.default, *args)
        self.children.append(radio_button)
        self.counter_id += 1

    def update_selection(self, new_id: int) -> None:
        self.selected_id = new_id
        for index, radio_button in enumerate(self.children):
            if index != self.selected_id:
                radio_button.unselect()

    def get_children(self) -> list:
        return self.children

    def get_button_num(self) -> int:
        return len(self.children)

    def get_selected(self) -> int:
        return self.selected_id


class RadioButton(Checkbox):
    def __init__(self,
                 radio_id: int,
                 callback: Callable[[int], None],
                 selected: bool,
                 x: Union[int, float],
                 y: Union[int, float],
                 label_text: str,
                 text_color: Tuple[int, int, int],
                 bg: Tuple[int, int, int],
                 width: int,
                 font: pygame.font.Font,
                 padding: int,
                 border: int,
                 widget_name: str = "!radio_button"):
        super().__init__(x, y, label_text, text_color, bg, width, font, padding, border, widget_name)
        self.id = radio_id
        self.button_length = 35
        self.button_radius = 15
        self.__button = Circle(padding, padding, self.button_radius, border, radio_id, callback, selected)

    def update(self, mouse_obj: Mouse.Cursor, keyboard_event: pygame.event.Event) -> None:
        abs_pos = mouse_obj.get_pos()
        rel_mouse = mouse_obj.copy()
        rel_mouse.set_pos(abs_pos[0] - self.x, abs_pos[1] - self.y)
        self.__button.update(rel_mouse)
        self.image.blit(self.__button.image, self.__button.rect)

    def unselect(self) -> None:
        self.__button.unselect()

    def get_size(self) -> Tuple[int, int]:
        return self.image.get_size()


class Circle(pygame.sprite.Sprite):
    def __init__(self,
                 x: Union[int, float],
                 y: Union[int, float],
                 radius: int,
                 border: int,
                 radio_id: int,
                 on_click: Callable[[int], None],
                 selected: bool = False):
        super().__init__()
        self.id = radio_id
        self.x = x
        self.y = y
        self.radius = radius
        self.border = border
        self.callback = on_click
        self.normal_color = GREY
        self.active_color = CYAN
        self.current_color = self.normal_color
        self.selected = selected
        self.lock = True
        self.mouse_down = False
        self.image = pygame.Surface((radius * 2, radius * 2), flags=pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))
        pygame.draw.circle(self.image, BLACK, (radius, radius), radius, 0)
        pygame.draw.circle(self.image, self.current_color, (radius, radius), radius - border, 0)
        self.rect = pygame.Rect(self.x, self.y, radius, radius)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, mouse_obj: Mouse.Cursor) -> None:
        collide = pygame.sprite.collide_mask(self, mouse_obj)
        if collide is None:
            if not mouse_obj.get_button_state(1):
                self.mouse_down = False
            self.lock = True
            self.current_color = self.normal_color
        else:
            if mouse_obj.get_button_state(1) and (not self.lock):
                self.mouse_down = True
            elif (not mouse_obj.get_button_state(1)) and self.mouse_down:
                self.mouse_down = False
                self.selected = True
                self.callback(self.id)
            if not mouse_obj.get_button_state(1):
                self.lock = False
            self.current_color = self.active_color
        pygame.draw.circle(self.image, self.current_color, (self.radius, self.radius), self.radius - self.border, 0)
        if self.selected:
            pygame.draw.circle(self.image, BLACK, (self.radius, self.radius), self.radius - 5, 0)

    def unselect(self) -> None:
        self.selected = False


class WidgetCanvas(BaseWidget):
    def __init__(self,
                 x: float,
                 y: float,
                 width: int,
                 height: int,
                 z_index: int = 1,
                 widget_name: str = "!widget_canvas"):
        super().__init__(widget_name)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.z_index = z_index
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
        if self.z_index == mouse_obj.get_z_index():
            pointer_events = True
            abs_pos = mouse_obj.get_pos()
            rel_mouse = mouse_obj.copy()
            rel_mouse.set_pos(abs_pos[0] - self.x, abs_pos[1] - self.y)
        else:
            pointer_events = False
            rel_mouse = Mouse.Cursor()
            rel_mouse.set_pos(-1, -1)  # Dummy mouse object to prevent collision.
        collide = self.rect.collidepoint(mouse_obj.get_pos())
        for widget in self.child_widgets.values():
            widget.update(rel_mouse, keyboard_event)
        self.render_widgets()
        if pointer_events and (not collide):
            mouse_obj.increment_z_index()

    def render_widgets(self) -> None:
        self.image.fill((0, 0, 0, 0))
        for w in self.child_widgets.values():
            self.image.blit(w.image, w.rect)


class WidgetGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.child_canvases = {}

    def add_widget_canvas(self, canvas_obj: WidgetCanvas) -> None:
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
