"""
This is a GUI toolkit for SDL that I made mainly for my own use, but feel free to use it in your project if you want.

|
How to use:

First, construct a 'Frame' class instance. Then, initialize each widget you want to use, and add the class object to the
frame via the 'Frame.add_widget' method. Note that radio buttons are a bit special, as you have to first create a
'RadioGroup' instance, then create radio buttons for the group with the 'RadioGroup.create_radio_button' method. After
that, you can pass the 'RadioGroup' object to the 'Frame.add_widget' method like a normal widget.

Every game tick, make sure to pass user events to the frame by calling the 'Frame.update' method and passing a
'Mouse.Cursor' object and a list of 'pygame.event.Event' objects as parameters. You should initialize a 'Mouse.Cursor'
object at the beginning of your code, and continuously call its 'mouse_enter', 'mouse_leave', 'reset_scroll',
'push_scroll', 'set_button_state', 'set_pos', and 'reset_z_index' methods at the correct times in the game-loop. The
list should contain all keyboard-related events that has appeared since the last time 'Frame.update' was called. This
can easily be achieved by declaring an empty list, then looping through the event queue every frame and appending
keyboard-related events to the end of the list, then clearing the list after passing it to the 'Frame.update' method.
After that, you can "blit" the frame to the display surface using the frame's 'image' and 'rect'
attributes.

As widgets solely rely on the data you pass to it to handle user events, make sure to correctly update the data you're
passing to the 'Frame.update' method to ensure widgets respond to hovers, clicks, scroll events, key-presses, and window
events correctly.

'UI_Demo.py' is a UI that demonstrates how to use this module. It was created for testing purposes during
development, but I'm sure it'll also help you on getting started.

|
Notes:

1. This module also needs 'Global.py', 'Mouse.py', and 'Time.py' to work. Include them in your project if you want to
   use this module.
2. Since this module needs access to window events, Pygame version >= 2.0.1 is required.
3. Apart from the 'Pygame' module, this file also requires the 'Pyperclip' module to be installed in order to access the
   clipboard. Make sure to install it with 'pip install pyperclip' if you don't already have it.
"""
from Global import *
import math
import Mouse
import Time
import os
import pygame
import pyperclip
os.environ["SDL_IME_SHOW_UI"] = "1"  # Enable showing the IME candidate list.


class BaseWidget(pygame.sprite.Sprite):
    def __init__(self, widget_name: str = "!base_widget"):
        """Base class for all widgets."""
        super().__init__()
        self.widget_name = widget_name
        self.parent = None

    def update(self, mouse_obj: Mouse.Cursor, keyboard_events: List[pygame.event.Event]) -> None:
        pass

    def get_widget_name(self) -> str:
        return self.widget_name

    def set_parent(self, parent_widget) -> None:
        self.parent = parent_widget

    def has_parent(self) -> bool:
        return self.parent is not None


class AnimatedSurface(BaseWidget):
    def __init__(self,
                 x: Union[int, float],
                 y: Union[int, float],
                 surface: pygame.Surface,
                 callback: Optional[Callable[[], None]],
                 widen_amount: int = 60,
                 widget_name: str = "!animated_surf"):
        """Animates a static surface image to dilate on mouse-hover and shrink on mouse-leave. When clicked, the surface
        flashes and calls the callback function given at initialization."""
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
        self.max_width = self.original_width + widen_amount
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

    def update(self, mouse_obj: Mouse.Cursor, keyboard_events: List[pygame.event.Event]) -> None:
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
        if round(new_width) == self.min_width and direction == "decrease":
            self.resize_state = "small"
            self.difference = self.max_width - self.min_width
        elif round(new_width) == self.max_width and direction == "increase":
            self.resize_state = "large"
            self.difference = self.max_width - self.min_width
        return new_width

    def change_size(self, direction: Literal["increase", "decrease"]) -> None:
        if (self.resize_state, direction) in (("small", "decrease"), ("large", "increase")):
            self.delta_timer.reset_timer()
            return None
        if self.resize_state == "small":
            self.resize_state = "dilating"
        elif self.resize_state == "large":
            self.resize_state = "shrinking"
        self.set_size(self.calc_physics(self.delta_timer.get_time(), direction))
        self.delta_timer.reset_timer()

    @staticmethod
    def calc_size(y_pos: int, og_width: int, og_height: int, widen_amount: int = 60) -> Tuple[float, float]:
        """Returns the top and bottom y coordinates of the button when it is at its max size."""
        aspect_ratio = og_height / og_width
        max_width = og_width + widen_amount
        min_height = og_width * aspect_ratio
        max_height = max_width * aspect_ratio
        min_top_y = y_pos - (max_height - min_height) / 2
        max_bottom_y = min_top_y + max_height
        return min_top_y, max_bottom_y


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
                 widen_amount: int = 60,
                 widget_name: str = "!button"):
        """Similar to AnimatedSurface, except it accepts a font object and a string in order to create the surface
        dynamically. The shape of the button is a two-cornered rounded rect."""
        button_surf = pygame.Surface((width, height), flags=pygame.SRCALPHA)
        button_surf.fill((0, 0, 0, 0))
        draw_button(button_surf, 0, 0, width, height, border, fg, bg, font, text)
        super().__init__(x, y, button_surf, callback, widen_amount, widget_name)


class Label(BaseWidget):
    def __init__(self,
                 x: Union[int, float],
                 y: Union[int, float],
                 text: Union[str, List[str]],
                 fg: Tuple[int, int, int],
                 width: int,
                 font: pygame.font.Font,
                 align: Literal["left", "center", "right"] = "center",
                 no_wrap: bool = False,
                 widget_name: str = "!label"):
        """Accepts text to be displayed, width in pixels, and a font object. The text will be word-wrapped to guarantee
        that it fits the requested width."""
        super().__init__(widget_name)
        self.x = x
        self.y = y
        self.text_lines = text if no_wrap else word_wrap_text(text, width, font)
        self.line_height = font.size("█")[1]
        self.rect = pygame.Rect(self.x, self.y, width, self.line_height * len(self.text_lines))
        self.image = pygame.Surface((self.rect.width, self.rect.height), flags=pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))
        for index, line in enumerate(self.text_lines):
            size = font.size(line)
            surface = font.render(line, True, fg)
            if align == "left":
                x = 0
            elif align == "center":
                x = width / 2 - size[0] / 2
            else:
                x = width - size[0]
            self.image.blit(surface, (x, index * self.line_height))

    def update_position(self, x: Union[int, float], y: Union[int, float]) -> None:
        self.x = x
        self.y = y
        self.rect = pygame.Rect(self.x, self.y, self.rect.width, self.rect.height)

    def get_size(self) -> Tuple[int, int]:
        return self.rect.size


class SplitLabel(BaseWidget):
    def __init__(self, x: Union[int, float], y: Union[int, float], lines: Tuple[str, str], wrap_widths: Tuple[int, int],
                 font: pygame.font.Font, fg: Tuple[int, int, int], bg: Tuple[int, int, int], radius: int, padding: int,
                 widget_name: str = "!split_label"):
        """Appears as a rounded rect with a line of word-wrapped text on either side horizontally. Great for displaying
        tables with two columns."""
        super().__init__(widget_name)
        self.x = x
        self.y = y
        self.width = 2 * radius + sum(wrap_widths) + padding
        self.wrapped_lines: List[Label] = []
        self.wrapped_lines.append(Label(radius, radius, lines[0], fg, wrap_widths[0], font, align="left"))
        label = Label(0, radius, lines[1], fg, wrap_widths[1], font, align="right")
        label.update_position(self.width - radius - label.get_size()[0], radius)
        self.wrapped_lines.append(label)
        self.height = 2 * radius + max(line.get_size()[1] for line in self.wrapped_lines)
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.image = pygame.Surface((self.width, self.height), flags=pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))
        draw_rounded_rect(self.image, (0, 0), (self.width, self.height), radius, bg)
        for line in self.wrapped_lines:
            self.image.blit(line.image, line.rect)


class ParagraphRect(BaseWidget):
    def __init__(self, x: Union[int, float], y: Union[int, float], width: int, radius: int, padding: int,
                 fg: Tuple[int, int, int], bg: Tuple[int, int, int], heading: str, body: str,
                 heading_font: pygame.font.Font, body_font: pygame.font.Font, widget_name: str = "!p_rect"):
        """Displays a heading and a word-wrapped paragraph in a rounded rect."""
        super().__init__(widget_name)
        self.x = x
        self.y = y
        self.width = width
        heading_label = Label(padding, padding, heading, fg, self.width - 2 * padding, heading_font,
                              align="left")
        body_label = Label(padding, heading_label.rect.bottom + padding, body, fg, self.width - 2 * padding,
                           body_font, align="left")
        self.height = body_label.rect.bottom + padding
        self.image = pygame.Surface((self.width, self.height), flags=pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))
        draw_rounded_rect(self.image, (0, 0), (self.width, self.height), radius, bg)
        self.image.blit(heading_label.image, heading_label.rect)
        self.image.blit(body_label.image, body_label.rect)
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def get_size(self) -> Tuple[int, int]:
        return self.width, self.height


class Checkbox(BaseWidget):
    def __init__(self,
                 x: Union[int, float],
                 y: Union[int, float],
                 label_text: str,
                 button_length: int,
                 border_radius: int,
                 text_color: Tuple[int, int, int],
                 bg: Tuple[int, int, int],
                 width: int,
                 font: pygame.font.Font,
                 padding: int,
                 border: int,
                 widget_name: str = "!checkbox"):
        """A simple checkbox with rounded corners both on the button and the surrounding rect. The caption text will be
        word-wrapped to fit the requested width."""
        super().__init__(widget_name)
        self.x = x
        self.y = y
        self.button_length = button_length
        self.button_radius = border_radius
        self.text_lines = word_wrap_text(label_text, width - padding * 3 - self.button_length, font)
        self.line_height = font.size("█")[1]
        self.checked = False
        self.image = pygame.Surface((width,
                                     padding * 2 + self.line_height * len(self.text_lines)), flags=pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))
        draw_rounded_rect(self.image, (0, 0), self.image.get_size(), self.button_radius, bg)
        for index, text in enumerate(self.text_lines):
            surface = font.render(text, True, text_color)
            self.image.blit(surface, (padding * 2 + self.button_length, padding + self.line_height * index))
        self.rect = pygame.Rect(self.x, self.y, *self.image.get_size())
        self.__button = Box(padding, padding, self.button_length, self.button_radius, border)

    def update(self, mouse_obj: Mouse.Cursor, keyboard_events: List[pygame.event.Event]) -> None:
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
        self.x = x
        self.y = y
        self.length = length
        self.radius = radius
        self.border = border
        self.lock = True
        self.mouse_down = False
        self.checked = False
        self.image = pygame.Surface((length, length))
        self.image.set_colorkey(TRANSPARENT)
        self.normal_color = GREY3
        self.active_color = CYAN
        self.current_color = self.normal_color
        self.render_surface()
        self.rect = pygame.Rect(self.x, self.y, length, length)
        self.mask = pygame.mask.from_surface(self.image)

    def render_surface(self) -> None:
        self.image.fill(TRANSPARENT)
        draw_rounded_rect(self.image, (0, 0), (self.length, self.length), self.radius, BLACK)
        draw_rounded_rect(self.image,
                          (self.border, self.border),
                          (self.length - self.border * 2, self.length - self.border * 2),
                          self.radius - self.border,
                          self.current_color)
        if self.checked:
            pygame.draw.lines(self.image, BLACK, False, ((5, self.length / 2 + 3),
                                                         (self.length / 2 - 5, self.length - 5),
                                                         (self.length - 5, 5)), 3)

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
        self.render_surface()  # Mask and rect updates are not needed, since the shape of the surface stays the same.

    def get_data(self) -> bool:
        return self.checked


class RadioGroup:
    def __init__(self, default: int = 0):
        """Used for managing a group of radio buttons. Create all needed radio buttons with the 'create_radio_button'
        method, then add this class instance to a frame when done."""
        super().__init__()
        self.default = default
        self.counter_id = 0
        self.selected_id = default
        self.children = []

    def create_radio_button(self,
                            x: Union[int, float],
                            y: Union[int, float],
                            label_text: str,
                            button_length: int,
                            border_radius: int,
                            selected_radius: int,
                            text_color: Tuple[int, int, int],
                            bg: Tuple[int, int, int],
                            width: int,
                            font: pygame.font.Font,
                            padding: int,
                            border: int,
                            widget_name: str = "!radio_button") -> None:
        radio_button = RadioButton(self.counter_id, self.update_selection, self.counter_id == self.default, x, y,
                                   label_text, button_length, border_radius, selected_radius, text_color, bg, width,
                                   font, padding, border, widget_name)
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
                 button_length: int,
                 border_radius: int,
                 selected_radius: int,
                 text_color: Tuple[int, int, int],
                 bg: Tuple[int, int, int],
                 width: int,
                 font: pygame.font.Font,
                 padding: int,
                 border: int,
                 widget_name: str = "!radio_button"):
        """A simple radio button widget. When a radio button is selected, all other radio-buttons in the same group will
         be unselected. The radio button which is selected by default is determined by the 'default' parameter passed to
         the RadioGroup class."""
        super().__init__(x, y, label_text, button_length, border_radius, text_color, bg, width, font, padding, border,
                         widget_name)
        self.id = radio_id
        self.button_radius = round(button_length / 2)
        self.__button = Circle(padding, padding, self.button_radius, border, selected_radius, radio_id, callback,
                               selected)

    def update(self, mouse_obj: Mouse.Cursor, keyboard_events: List[pygame.event.Event]) -> None:
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
                 selected_radius: int,
                 radio_id: int,
                 on_click: Callable[[int], None],
                 selected: bool = False):
        super().__init__()
        self.id = radio_id
        self.x = x
        self.y = y
        self.radius = radius
        self.border = border
        self.selected_radius = selected_radius
        self.callback = on_click
        self.normal_color = GREY3
        self.active_color = CYAN
        self.current_color = self.normal_color
        self.selected = selected
        self.lock = True
        self.mouse_down = False
        self.image = pygame.Surface((radius * 2, radius * 2))
        self.image.set_colorkey(TRANSPARENT)
        self.image.fill(TRANSPARENT)
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
            pygame.draw.circle(self.image, BLACK, (self.radius, self.radius), self.selected_radius, 0)

    def unselect(self) -> None:
        self.selected = False


class Entry(BaseWidget):
    def __init__(self,
                 x: Union[int, float],
                 y: Union[int, float],
                 width: int,
                 height: int,
                 padding: int,
                 font: pygame.font.Font,
                 fg: Tuple[int, int, int],
                 widget_name: str = "!entry"):
        """A simple text-box widget. Behaves virtually identical to the text-box widget of win32gui. Its copy-pasting
        functionality relies on the 'Pyperclip' module, so make sure to have it installed. Note that the environment
        variable 'SDL_IME_SHOW_UI' must be set to 1 for this widget to function correctly. This is done automatically
        when the module is imported."""
        super().__init__(widget_name)
        self.x = x
        self.y = y
        self.original_width = width
        self.height = height
        self.padding = padding
        self.font = font
        self.fg = fg
        self.border_thickness = 2
        self.text_input = False
        self.shift = False
        self.selecting = False
        self.start_select = True
        self.normal_border = BLACK
        self.active_border = BLUE
        self.current_border = self.normal_border
        self.block_select = False
        self.drag_pos = None
        self.drag_pos_recorded = False
        self.dnd_start_x = -1
        self.dnd_distance = 0
        self.dnd_x_recorded = False
        self.real_x = 0
        self.real_y = 0
        self.lock = True
        self.mouse_down = False
        self.text_canvas = EntryText(width - padding * 2, height - padding * 2, self.font, fg)
        self.ime_canvas = None
        self.caret_restore_pos = -1
        # (start sticky keys, start timer, has reset repeat, repeat timer)
        self.sticky_keys = {pygame.K_LEFT: [False,
                                            Time.Time(),
                                            False,
                                            Time.Time(),
                                            lambda: self.text_canvas.change_caret_pos("l")],
                            pygame.K_RIGHT: [False,
                                             Time.Time(),
                                             False,
                                             Time.Time(),
                                             lambda: self.text_canvas.change_caret_pos("r")],
                            pygame.K_BACKSPACE: [False,
                                                 Time.Time(),
                                                 False,
                                                 Time.Time(),
                                                 self.text_canvas.backspace],
                            pygame.K_DELETE: [False,
                                              Time.Time(),
                                              False,
                                              Time.Time(),
                                              self.text_canvas.delete]}
        self.start_delay = 0.5
        self.repeat_delay = 0.1
        self.scroll_hit_box = 30
        self.image = pygame.Surface((self.original_width, self.height))
        self.rect = pygame.Rect(self.x, self.y, self.original_width, self.height)

    def render_text_canvas(self) -> None:
        self.image.fill((0, 0, 0, 0))
        pygame.draw.rect(self.image, self.current_border, [0, 0, self.original_width, self.height], 0)
        pygame.draw.rect(self.image,
                         WHITE,
                         [self.border_thickness,
                          self.border_thickness,
                          self.original_width - self.border_thickness * 2,
                          self.height - self.border_thickness * 2],
                         0)
        self.image.blit(source=self.text_canvas.get_surface(),
                        dest=(self.padding, self.padding),
                        area=self.text_canvas.get_view_rect())

    def update_real_pos(self, real_pos: Tuple[Union[int, float], Union[int, float]]) -> None:
        self.real_x, self.real_y = real_pos

    def update(self, mouse_obj: Mouse.Cursor, keyboard_events: List[pygame.event.Event]) -> Tuple[bool, bool, bool]:
        collide = pygame.sprite.collide_rect(self, mouse_obj)
        if collide:
            if mouse_obj.get_button_state(1):
                if (not self.lock) and (self.ime_canvas is None):
                    self.mouse_down = True
                    self.text_input = True
                    self.text_canvas.focus_get()
                    self.parent.raise_widget_layer(self.widget_name)
            else:
                self.mouse_down = False
                self.lock = False
            self.current_border = self.active_border
            if (not self.text_canvas.dnd_event_ongoing()) and self.block_select:
                self.block_select = False
        else:
            if mouse_obj.get_button_state(1):
                self.mouse_down = True
                if self.lock:
                    self.stop_focus()
            else:
                self.mouse_down = False
                self.lock = True
            self.current_border = self.normal_border
            if (not self.text_canvas.dnd_event_ongoing()) and self.block_select:
                self.block_select = False
        abs_pos = mouse_obj.get_pos()
        rel_mouse = mouse_obj.copy()
        rel_mouse.set_pos(abs_pos[0] - (self.x + self.padding), abs_pos[1] - (self.y + self.padding))
        for event in keyboard_events:
            if event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
                if event.mod & pygame.KMOD_SHIFT:
                    self.shift = True
                else:
                    if self.shift:
                        self.shift = False
                        if not self.start_select:
                            self.text_canvas.end_selection()
                            self.start_select = True
                        elif self.text_canvas.selection_event_ongoing():
                            # Special case for handling a text selection event that was initiated by a HOME or END
                            # key-press.
                            self.text_canvas.end_selection()
            if event.type == pygame.WINDOWFOCUSLOST:
                self.stop_focus()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    self.text_canvas.add_text("\t".expandtabs(tabsize=4))
                elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_BACKSPACE, pygame.K_DELETE):
                    if not self.sticky_keys[event.key][0]:
                        if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                            if self.shift and self.start_select and \
                                    (not self.text_canvas.selection_event_ongoing()):
                                # The last one in the boolean expression is to make sure a selection event won't be
                                # triggered again if it has already been initiated by a HOME or END key-press.
                                self.text_canvas.start_selection()
                                self.start_select = False
                        self.sticky_keys[event.key][4]()
                        self.sticky_keys[event.key][0] = True
                        self.sticky_keys[event.key][1].reset_timer()
                elif event.key == pygame.K_HOME:
                    self.text_canvas.caret_home(self.shift)
                elif event.key == pygame.K_END:
                    self.text_canvas.caret_end(self.shift)
                elif event.key == pygame.K_RETURN:
                    if self.ime_canvas is not None:
                        self.stop_ime_input()
                elif event.mod & pygame.KMOD_CTRL:
                    if event.key == pygame.K_c:
                        self.text_canvas.copy_text()
                    elif event.key == pygame.K_v:
                        self.paste_text()
                    elif event.key == pygame.K_a:
                        self.text_canvas.select_all()
                    elif event.key == pygame.K_x:
                        if self.text_canvas.copy_text():
                            self.text_canvas.backspace()
                    elif event.key == pygame.K_z:
                        if self.shift:
                            self.text_canvas.redo()
                        else:
                            self.text_canvas.undo()
                    elif event.key == pygame.K_y:
                        self.text_canvas.redo()
            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_BACKSPACE, pygame.K_DELETE):
                    self.sticky_keys[event.key][0] = False
                    self.sticky_keys[event.key][2] = False
            elif event.type == pygame.TEXTINPUT:
                self.text_canvas.add_text(event.text)
            elif event.type == pygame.TEXTEDITING:
                if self.ime_canvas is None and self.text_canvas.has_focus() and event.text:
                    self.caret_restore_pos = self.text_canvas.get_caret_index()
                    self.text_canvas.focus_lose(False)
                    self.ime_canvas = EntryText(self.original_width - self.padding * 2,
                                                self.height - self.padding * 2,
                                                self.font,
                                                self.fg)
                    self.ime_canvas.focus_get()
                if self.ime_canvas is not None:
                    self.ime_canvas.ime_update_text(event.text, event.start)
                    width_diff = (self.padding
                                  + self.text_canvas.get_x()
                                  + self.text_canvas.calc_location_width()
                                  - self.text_canvas.get_caret_width()
                                  + self.ime_canvas.calc_text_size(self.ime_canvas.get_text())[0]
                                  + self.ime_canvas.get_caret_width()) - self.original_width
                    if width_diff > 0:
                        # (self.original_width + width_diff, self.height)
                        self.image = pygame.Surface((self.original_width + width_diff, self.height),
                                                    flags=pygame.SRCALPHA)
                    else:
                        self.image = pygame.Surface((self.original_width, self.height))
                    text_rect = pygame.Rect(self.real_x + self.padding + self.text_canvas.get_x()
                                            + self.text_canvas.calc_location_width()
                                            - self.text_canvas.get_caret_width() + self.ime_canvas.calc_ime_x_pos(),
                                            self.real_y + self.height - self.padding,
                                            0,
                                            0)
                    # It is unclear what effect the size of the rect has on the IME candidate list.
                    pygame.key.set_text_input_rect(self.parent.calc_resized_ime_rect(text_rect))
                    if not self.ime_canvas.get_text():
                        self.stop_ime_input()
        for key in self.sticky_keys.values():
            if key[0]:
                if key[1].get_time() > self.start_delay and (not key[2]):
                    key[2] = True
                    key[3].reset_timer()
            if key[2]:
                delta_time = key[3].get_time()
                if delta_time > self.repeat_delay:
                    compensation = delta_time - self.repeat_delay
                    key[4]()
                    if compensation > self.repeat_delay:
                        for i in range(math.floor(compensation / self.repeat_delay)):
                            key[4]()
                        compensation %= self.repeat_delay
                    key[3].force_elapsed_time(compensation)
        if mouse_obj.get_button_state(1):
            if self.drag_pos_recorded and self.text_canvas.mouse_collision(self.drag_pos):
                if mouse_obj.get_pos()[0] < self.x + self.scroll_hit_box:
                    self.text_canvas.move_view_by_pos("r")
                elif mouse_obj.get_pos()[0] > self.x + (self.original_width - self.scroll_hit_box):
                    self.text_canvas.move_view_by_pos("l")
            if self.text_canvas.mouse_collision(rel_mouse):
                if not self.drag_pos_recorded:
                    self.drag_pos_recorded = True
                    self.drag_pos = rel_mouse.copy()
                self.text_canvas.update_caret_pos(rel_mouse.get_pos())
                if not self.dnd_x_recorded:
                    self.dnd_x_recorded = True
                    self.dnd_start_x = rel_mouse.get_pos()[0]
                if self.text_canvas.text_block_selected() and (not self.text_canvas.dnd_event_ongoing()):
                    if abs(rel_mouse.get_pos()[0] - self.dnd_start_x) > self.dnd_distance:
                        self.text_canvas.start_dnd_event(rel_mouse)
                        if not self.block_select:
                            self.block_select = True
                if (not self.selecting) and \
                        (not self.text_canvas.dnd_event_ongoing()) and \
                        (not self.text_canvas.selection_rect_collide(rel_mouse.get_pos())):
                    self.text_canvas.start_selection()
                    self.selecting = True
        else:
            if self.text_canvas.mouse_collision(rel_mouse):
                if self.dnd_start_x != -1 and self.text_canvas.text_block_selected():
                    if self.text_canvas.selection_rect_collide(rel_mouse.get_pos()):
                        if abs(rel_mouse.get_pos()[0] - self.dnd_start_x) <= self.dnd_distance:
                            # Unselect text
                            self.text_canvas.cancel_dnd_event()
                            self.text_canvas.start_selection()
                            self.text_canvas.end_selection()
            if self.text_canvas.dnd_event_ongoing():
                self.text_canvas.end_dnd_event()
            if self.selecting:
                self.selecting = False
                if not mouse_obj.has_left():
                    self.text_canvas.update_caret_pos(rel_mouse.get_pos())
                self.text_canvas.end_selection()
            self.drag_pos_recorded = False
            self.drag_pos = None
            self.dnd_x_recorded = False
            self.dnd_start_x = -1
        self.text_canvas.update(False)
        self.render_text_canvas()
        if self.ime_canvas is not None:
            self.ime_canvas.update(True)
            self.image.blit(self.ime_canvas.get_surface(),
                            (self.padding
                             + self.text_canvas.get_x()
                             + self.text_canvas.calc_location_width()
                             - self.text_canvas.get_caret_width(),
                             self.padding))
        return collide, self.block_select, self.text_input

    def stop_focus(self) -> None:
        if self.ime_canvas is not None:
            # The IME text will be deleted.
            self.stop_ime_input()
        self.text_canvas.focus_lose()
        self.text_input = False

    def stop_ime_input(self):
        self.image = pygame.Surface((self.original_width, self.height))
        self.ime_canvas = None
        self.text_canvas.focus_get()
        self.text_canvas.set_caret_index(self.caret_restore_pos)
        self.caret_restore_pos = -1

    def paste_text(self) -> None:
        try:
            text = pyperclip.paste()
        except pyperclip.PyperclipException:
            return None
        if text:
            # The paste will be ignored if the Entry does not have keyboard focus.
            self.text_canvas.add_text("".join(c for c in text if c.isprintable()))

    def set_auto_typed_text(self, text: str) -> None:
        """Does the equivalent of clicking the entry, typing the text given, then pressing Ctrl+A."""
        self.text_input = True
        self.text_canvas.focus_get()
        self.parent.raise_widget_layer(self.widget_name)
        self.text_canvas.add_text(text)
        self.text_canvas.select_all()

    def get_pos(self) -> Tuple[int, int]:
        return self.x, self.y

    def get_entry_content(self) -> str:
        return self.text_canvas.get_text()


class EntryText:
    def __init__(self, width: int, height: int, font: pygame.font.Font, text_color: Tuple[int, int, int]):
        self.font = font
        self.text_color = text_color
        self.scroll_padding = 5
        self.x = 0
        self.y = 0
        self.view_width = width
        self.view_height = height
        self.caret_width = 2
        self.caret_height = height - 4
        self.caret_surf = pygame.Surface((self.caret_width, self.caret_height))
        self.caret_surf.fill(BLACK)
        self.caret_timer = Time.Time()
        self.caret_delay = 0.5
        self.scroll_amount = 70
        self.scroll_time = 0
        self.scroll_timer = Time.Time()
        self.scroll_timer.reset_timer()
        self.display_caret = True
        self.focus = False
        self.surface = pygame.Surface((self.caret_width, self.view_height))
        self.surface.fill(WHITE)
        self.text = ""
        self.undo_history = [""]
        self.redo_history = []
        self.caret_index = 0
        self.select_start = -1
        self.select_end = -1
        self.selecting = False
        self.select_rect = None
        self.dnd_event = False

    def record_undo(self) -> None:
        self.undo_history.append(self.text)

    def undo(self) -> None:
        if len(self.undo_history) and self.focus:
            temp = self.text
            while len(self.undo_history) and temp == self.text:
                temp = self.undo_history.pop()
            self.redo_history.append(temp)
            self.text = temp
            if self.caret_index > len(self.text):
                self.caret_index = len(self.text)
            current_width = self.calc_location_width()
            if current_width < self.view_width:
                self.x = 0
            elif self.x + current_width < self.view_width:
                self.move_view_by_caret("l")

    def redo(self) -> None:
        if len(self.redo_history) and self.focus:
            temp = self.text
            while len(self.redo_history) and temp == self.text:
                temp = self.redo_history.pop()
            self.undo_history.append(temp)
            self.text = temp
            if self.caret_index > len(self.text):
                self.caret_index = len(self.text)
            current_width = self.calc_location_width()
            if current_width < self.view_width:
                self.x = 0
            elif self.x + current_width < self.view_width:
                self.move_view_by_caret("l")

    def text_block_selected(self) -> bool:
        # Returns True if a block of text has already been selected, and the selection event has ENDED.
        return self.select_start != -1 and self.select_end != -1 and (not self.selecting)

    def selection_event_ongoing(self) -> bool:
        # Returns True if a selection event is *currently* ongoing.
        # (e.g. the shift key is still held down, or the left mouse button is still held down)
        return self.selecting

    def selection_rect_collide(self, position: Tuple[int, int]) -> bool:
        if (self.select_rect is not None) and (self.select_start != -1 and self.select_end != -1):
            rect = pygame.Rect(self.select_rect.x + self.x, self.select_rect.y, *self.select_rect.size)
            return rect.collidepoint(*position)
        else:
            return False

    def start_dnd_event(self, mouse_obj: Mouse.Cursor) -> None:
        if not self.dnd_event:
            if self.selection_rect_collide(mouse_obj.get_pos()) and \
                    (self.select_start != -1 and self.select_end != -1) and \
                    (not self.selecting):
                self.dnd_event = True

    def end_dnd_event(self) -> None:
        if self.dnd_event and (self.select_start != -1 and self.select_end != -1) and (not self.selecting):
            self.dnd_event = False
            if self.select_start <= self.caret_index <= self.select_end:
                self.select_start = -1
                self.select_end = -1
                self.select_rect = None
                return None
            selection = self.text[self.select_start:self.select_end]
            before_sel = self.text[:self.select_start]
            after_sel = self.text[self.select_end:]
            self.text = before_sel + after_sel
            if self.caret_index > self.select_end:
                temp_caret_idx = self.caret_index - len(selection)
            else:
                temp_caret_idx = self.caret_index
            before_sel = self.text[:temp_caret_idx]
            after_sel = self.text[temp_caret_idx:]
            self.text = before_sel + selection + after_sel
            self.select_start = -1
            self.select_end = -1
            self.select_rect = None
            self.record_undo()

    def cancel_dnd_event(self) -> None:
        self.dnd_event = False

    def dnd_event_ongoing(self) -> bool:
        return self.dnd_event

    def add_text(self, text: str) -> None:
        if not self.focus:
            return None
        overwrite = False
        if self.select_start != -1 or self.selecting:
            overwrite = True
            if self.selecting:
                if self.caret_index > self.select_start:
                    front = self.text[:self.select_start]
                    back = self.text[self.caret_index:]
                    self.caret_index = self.select_start + len(text)
                else:
                    front = self.text[:self.caret_index]
                    back = self.text[self.select_start:]
                    self.caret_index += len(text)
                self.select_start = self.caret_index
                self.select_end = -1
                self.select_rect = None
            else:
                front = self.text[:self.select_start]
                back = self.text[self.select_end:]
                self.caret_index = self.select_start + len(text)
                self.select_start = -1
                self.select_end = -1
                self.select_rect = None
            self.text = front + text + back
        else:
            temp = list(self.text)
            self.text = "".join(temp[:self.caret_index] + list(text) + temp[self.caret_index:])
        self.reset_caret()
        if not overwrite:
            self.caret_index += len(text)
        current_width = self.calc_location_width()
        if self.x + current_width > self.view_width:
            self.move_view_by_caret("l")
        self.record_undo()
        self.cancel_dnd_event()

    def backspace(self) -> None:
        if not self.focus:
            return None
        if self.select_start != -1 or self.selecting:
            if self.selecting:
                if self.caret_index > self.select_start:
                    front = self.text[:self.select_start]
                    back = self.text[self.caret_index:]
                    self.text = front + back
                    self.caret_index = self.select_start
                else:
                    front = self.text[:self.caret_index]
                    back = self.text[self.select_start:]
                    self.text = front + back
                self.select_start = self.caret_index
                self.select_end = -1
                self.select_rect = None
            else:
                self.text = self.text[:self.select_start] + self.text[self.select_end:]
                self.caret_index = self.select_start
                self.select_start = -1
                self.select_end = -1
                self.select_rect = None
        else:
            original_len = len(self.text)
            front = self.text[:self.caret_index]
            back = self.text[self.caret_index:]
            front = front[:-1]
            self.text = front + back
            if len(self.text) != original_len:
                self.caret_index -= 1
        if self.calc_text_size(self.text)[0] + self.caret_width < self.view_width:
            self.x = 0
        elif self.x + self.calc_text_size(self.text)[0] + self.caret_width < self.view_width:
            self.x = -(self.calc_text_size(self.text)[0] + self.caret_width + self.scroll_padding - self.view_width)
        self.record_undo()
        self.cancel_dnd_event()
        self.reset_caret()

    def delete(self) -> None:
        if not self.focus:
            return None
        if self.select_start != -1 or self.selecting:
            if self.selecting:
                if self.caret_index > self.select_start:
                    self.text = self.text[:self.select_start] + self.text[self.caret_index:]
                    self.caret_index = self.select_start
                else:
                    self.text = self.text[:self.caret_index] + self.text[self.select_start:]
                self.select_start = self.caret_index
                self.select_end = -1
                self.select_rect = None
            else:
                self.text = self.text[:self.select_start] + self.text[self.select_end:]
                self.caret_index = self.select_start
                self.select_start = -1
                self.select_end = -1
                self.select_rect = None
        else:
            front = self.text[:self.caret_index]
            back = self.text[self.caret_index:]
            back = back[1:]
            self.text = front + back
        if self.calc_text_size(self.text)[0] + self.caret_width < self.view_width:
            self.x = 0
        elif self.x + self.calc_text_size(self.text)[0] + self.caret_width < self.view_width:
            self.x = -(self.calc_text_size(self.text)[0] + self.caret_width + self.scroll_padding - self.view_width)
        self.record_undo()
        self.cancel_dnd_event()
        self.reset_caret()

    def copy_text(self) -> bool:
        """
        Returns True if there is text currently selected (which was just copied to the clipboard), False if otherwise.
        """
        if (self.select_start != -1 or self.selecting) and self.focus:
            if self.selecting:
                if self.caret_index > self.select_start:
                    selection = self.text[self.select_start:self.caret_index]
                else:
                    selection = self.text[self.caret_index:self.select_start]
            else:
                selection = self.text[self.select_start:self.select_end]
            try:
                pyperclip.copy(selection)
            except pyperclip.PyperclipException:
                pass
            return True
        else:
            return False

    def calc_location_width(self) -> float:
        return self.calc_text_size(self.text[:self.caret_index])[0] + self.caret_width

    def reset_caret(self) -> None:
        self.display_caret = True
        self.caret_timer.reset_timer()

    def update_caret_pos(self, mouse_pos) -> None:
        if not self.focus:
            return None
        text_index = -1
        width_counter = 0
        mouse_pos = (mouse_pos[0] + abs(self.x), mouse_pos[1])
        while width_counter < mouse_pos[0]:
            if text_index == len(self.text) - 1:
                break
            text_index += 1
            width_counter = self.calc_text_size(self.text[:text_index])[0]
        distances = (abs(mouse_pos[0]),
                     abs(self.calc_text_size(self.text[:text_index - 1])[0] - mouse_pos[0]),
                     abs(self.calc_text_size(self.text[:text_index])[0] - mouse_pos[0]),
                     abs(self.calc_text_size(self.text)[0] - mouse_pos[0]))
        self.caret_index = (0,
                            text_index - 1,
                            text_index,
                            len(self.text))[min(enumerate(distances), key=lambda x: x[1])[0]]
        if self.select_start != -1 or self.selecting:
            if self.selecting:
                start_pos = self.calc_text_size(self.text[:self.select_start])[0]
                end_pos = self.calc_text_size(self.text[:self.caret_index])[0]
            else:
                start_pos = self.calc_text_size(self.text[:self.select_start])[0]
                end_pos = self.calc_text_size(self.text[:self.select_end])[0]
            if start_pos < end_pos:
                self.select_rect = pygame.Rect(start_pos,
                                               0,
                                               abs(end_pos - start_pos) + self.caret_width,
                                               self.view_height)
            else:
                self.select_rect = pygame.Rect(end_pos,
                                               0,
                                               abs(end_pos - start_pos) + self.caret_width,
                                               self.view_height)

    def select_all(self) -> None:
        if self.focus:
            self.select_start = 0
            self.select_end = len(self.text)
            start_pos = self.calc_text_size(self.text[:self.select_start])[0]
            end_pos = self.calc_text_size(self.text[:self.select_end])[0]
            self.select_rect = pygame.Rect(start_pos, 0, end_pos - start_pos + self.caret_width, self.view_height)
            self.cancel_dnd_event()

    def start_selection(self) -> None:
        self.select_start = self.caret_index
        self.selecting = True

    def end_selection(self) -> None:
        self.select_end = self.caret_index
        self.selecting = False
        if self.select_start == self.select_end:
            self.select_start = -1
            self.select_end = -1
            self.select_rect = None
        else:
            if self.select_end < self.select_start:
                self.select_start, self.select_end = self.select_end, self.select_start
            start_pos = self.calc_text_size(self.text[:self.select_start])[0]
            end_pos = self.calc_text_size(self.text[:self.select_end])[0]
            self.select_rect = pygame.Rect(start_pos, 0, end_pos - start_pos + self.caret_width, self.view_height)

    def change_caret_pos(self, direction: Literal["l", "r"]) -> None:
        if not self.focus:
            return None
        if direction == "l":
            self.caret_index -= 1
            if self.caret_index < 0:
                self.caret_index = 0
        elif direction == "r":
            self.caret_index += 1
            if self.caret_index > len(self.text):
                self.caret_index = len(self.text)
        if self.selecting:
            if self.caret_index > self.select_start:
                start_pos = self.calc_text_size(self.text[:self.select_start])[0]
                end_pos = self.calc_text_size(self.text[:self.caret_index])[0]
            else:
                start_pos = self.calc_text_size(self.text[:self.caret_index])[0]
                end_pos = self.calc_text_size(self.text[:self.select_start])[0]
            if start_pos < end_pos:
                self.select_rect = pygame.Rect(start_pos,
                                               0,
                                               abs(end_pos - start_pos) + self.caret_width,
                                               self.view_height)
            else:
                self.select_rect = pygame.Rect(end_pos,
                                               0,
                                               abs(end_pos - start_pos) + self.caret_width,
                                               self.view_height)
        else:
            self.select_start = -1
            self.select_end = -1
            self.select_rect = None
        self.reset_caret()
        self.cancel_dnd_event()
        current_width = self.calc_location_width()
        if self.x + current_width < self.scroll_padding:
            self.move_view_by_caret("r")
        elif self.x + current_width > self.view_width - self.scroll_padding:
            self.move_view_by_caret("l")

    def ime_update_text(self, new_text: str, caret_pos: int) -> None:
        self.text = new_text
        self.caret_index = caret_pos

    def calc_ime_x_pos(self) -> float:
        if self.caret_index >= len(self.text):
            # Do not change the greater or equal to, because the caret pos reported by Pygame seems to go out of range
            # sometimes.
            return self.calc_text_size(self.text)[0]
        else:
            return self.calc_text_size(self.text[:self.caret_index])[0] \
                + self.calc_text_size(self.text[self.caret_index])[0]

    def caret_home(self, shift_down: bool) -> None:
        if self.focus:
            if (self.select_start != -1 and self.select_end != -1) and (not self.selecting):
                self.select_start = -1
                self.select_end = -1
                self.select_rect = None
            elif self.selecting:
                start_pos = self.calc_text_size(self.text[:self.select_start])[0]
                end_pos = 0
                self.select_rect = pygame.Rect(end_pos, 0, start_pos - end_pos + self.caret_width, self.view_height)
            elif shift_down:  # No text is selected (select_start == -1), but the shift key is down.
                start_pos = self.calc_text_size(self.text[:self.caret_index])[0]
                end_pos = 0
                self.selecting = True
                self.select_start = self.caret_index
                self.select_rect = pygame.Rect(end_pos, 0, start_pos - end_pos + self.caret_width, self.view_height)
            self.caret_index = 0
            self.x = 0
            self.cancel_dnd_event()

    def caret_end(self, shift_down: bool) -> None:
        if self.focus:
            if (self.select_start != -1 and self.select_end != -1) and (not self.selecting):
                self.select_start = -1
                self.select_end = -1
                self.select_rect = None
            elif self.selecting:
                start_pos = self.calc_text_size(self.text[:self.select_start])[0]
                end_pos = self.calc_text_size(self.text)[0]
                self.select_rect = pygame.Rect(start_pos, 0, end_pos - start_pos + self.caret_width, self.view_height)
            elif shift_down:
                start_pos = self.calc_text_size(self.text[:self.caret_index])[0]
                end_pos = self.calc_text_size(self.text)[0]
                self.selecting = True
                self.select_start = self.caret_index
                self.select_rect = pygame.Rect(start_pos, 0, end_pos - start_pos + self.caret_width, self.view_height)
            self.caret_index = len(self.text)
            if self.calc_text_size(self.text)[0] + self.caret_width > self.view_width:
                self.move_view_by_caret("l")
            self.cancel_dnd_event()

    def update(self, underline: bool) -> None:
        self.scroll_time = self.scroll_timer.get_time()
        self.scroll_timer.reset_timer()
        if not self.focus:
            new_size = self.calc_text_size(self.text)
            self.surface = pygame.Surface((new_size[0] + self.caret_width, self.view_height))
            self.surface.fill(WHITE)
            self.surface.blit(self.render_text(), (0, 0))
            return None
        delta_time = self.caret_timer.get_time()
        if delta_time > self.caret_delay:
            compensation = delta_time - self.caret_delay
            self.display_caret = not self.display_caret
            if compensation > self.caret_delay:
                for i in range(math.floor(compensation / self.caret_delay)):
                    self.display_caret = not self.display_caret
                compensation %= self.caret_delay
            self.caret_timer.force_elapsed_time(compensation)
        new_size = self.calc_text_size(self.text)
        self.surface = pygame.Surface((new_size[0] + self.caret_width, self.view_height))
        self.surface.fill(WHITE)
        if self.select_rect is not None:
            pygame.draw.rect(self.surface, (166, 210, 255), self.select_rect, 0)
        self.surface.blit(self.render_text(), (0, 0))
        if underline:
            for x in range(0, self.surface.get_width() - 2, 3):
                pygame.draw.rect(self.surface, BLACK, [x, self.view_height - 1, 2, 1], 0)
        if self.display_caret:
            x = self.calc_text_size(self.text[:self.caret_index])[0]
            self.surface.blit(self.caret_surf, (x, (self.view_height - self.caret_height) / 2))

    def render_text(self) -> pygame.Surface:
        text = self.font.render(self.text, True, self.text_color)
        text = pygame.transform.scale(text, self.calc_text_size(self.text))
        if len(self.text) == 0:
            return pygame.Surface((0, self.view_height))
        else:
            return text

    def calc_text_size(self, text: str) -> Tuple[float, int]:
        text_size = self.font.size(text)
        wh_ratio = text_size[0] / text_size[1]
        new_size = (self.view_height * wh_ratio, self.view_height)
        return new_size

    def focus_get(self) -> None:
        self.focus = True
        self.display_caret = True
        self.caret_timer.reset_timer()

    def focus_lose(self, reset_scroll: bool = True) -> None:
        if not self.focus:
            return None
        if reset_scroll:
            self.x = 0
        self.focus = False
        self.display_caret = False
        if (self.select_start != -1 and self.select_end != -1) or self.selecting:
            self.selecting = False
            self.select_start = -1
            self.select_end = -1
            self.select_rect = None

    def mouse_collision(self, mouse_obj: Mouse.Cursor) -> bool:
        return pygame.Rect(0, 0, self.view_width, self.view_height).collidepoint(*mouse_obj.get_pos())

    def move_view_by_caret(self, direction: Literal["l", "r"]) -> None:
        if direction == "l":
            width = self.calc_text_size(self.text[:self.caret_index])[0] + self.caret_width
            self.x = -(width - self.view_width + self.scroll_padding)
        elif direction == "r":
            width = self.calc_text_size(self.text[:self.caret_index])[0]
            if self.caret_index == 0:
                self.x = 0
            else:
                self.x = -(width - self.caret_width - self.scroll_padding)

    def move_view_by_pos(self, direction: Literal["l", "r"]) -> None:
        if not self.focus:
            return None
        if direction == "l":
            if self.calc_text_size(self.text)[0] + self.caret_width <= self.view_width:
                self.x = 0
                return None
            self.x -= self.scroll_amount * self.scroll_time
            if self.x < -(self.calc_text_size(self.text)[0] + self.caret_width + self.scroll_padding - self.view_width):
                self.x = -(self.calc_text_size(self.text)[0] + self.caret_width + self.scroll_padding - self.view_width)
        elif direction == "r":
            self.x += self.scroll_amount * self.scroll_time
            if self.x > 0:
                self.x = 0

    def get_surface(self) -> pygame.Surface:
        return self.surface

    def get_view_rect(self) -> pygame.Rect:
        return pygame.Rect(abs(self.x), self.y, self.view_width, self.view_height)

    def has_focus(self) -> bool:
        return self.focus

    def get_text(self) -> str:
        return self.text

    def get_x(self) -> int:
        return self.x

    def get_caret_width(self) -> int:
        return self.caret_width

    def set_caret_index(self, index: int) -> None:
        self.caret_index = index

    def get_caret_index(self) -> int:
        return self.caret_index


class Slider(BaseWidget):
    def __init__(self,
                 x: Union[int, float],
                 y: Union[int, float],
                 text_height: int,
                 text_color: Tuple[int, int, int],
                 line_length: int,
                 line_thickness: int,
                 dormant_line_color: Tuple[int, int, int],
                 active_line_color: Tuple[int, int, int],
                 thumb_width: int,
                 thumb_height: int,
                 dormant_color: Tuple[int, int, int],
                 active_color: Tuple[int, int, int],
                 font: pygame.font.Font,
                 min_value: int,
                 max_value: int,
                 text_padding: int = 10,
                 mark_height: int = 0,
                 widget_name: str = "!slider"):
        """A simple slider widget. When the parameter 'mark_height' is greater than 0, lines of that height will be
        drawn at every unit."""
        super().__init__(widget_name)
        self.x = x
        self.y = y
        self.font = font
        self.text_height = text_height
        self.text_color = text_color
        self.line_length = line_length
        self.line_thickness = line_thickness
        self.dormant_line_color = dormant_line_color
        self.active_line_color = active_line_color
        self.thumb_width = thumb_width
        self.text_padding = text_padding  # The padding between the number display and the slider.
        self.gauge_height = mark_height
        self.max_text_width = self.resize_text(str(max_value))[0]
        self.width = self.thumb_width + self.line_length + self.text_padding + self.max_text_width
        self.height = max(text_height, thumb_height)
        self.slider_thumb = SliderButton(self.height / 2 - thumb_height / 2,
                                         self.thumb_width,
                                         thumb_height,
                                         dormant_color,
                                         active_color,
                                         self.line_length,
                                         min_value,
                                         max_value)
        self.image = pygame.Surface((self.width, self.height), flags=pygame.SRCALPHA)
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def render_surface(self) -> None:
        self.image.fill((0, 0, 0, 0))
        # Draw a line from the beginning to the slider thumb's mid-point.
        pygame.draw.line(self.image, self.active_line_color,
                         (self.thumb_width / 2, self.height / 2),
                         (self.thumb_width + self.slider_thumb.get_position()[0], self.height / 2),
                         width=self.line_thickness)
        # Draw a line from the slider thumb's mid-point to the end of the slider.
        pygame.draw.line(self.image, self.dormant_line_color,
                         (self.thumb_width + self.slider_thumb.get_position()[0], self.height / 2),
                         (self.thumb_width / 2 + self.line_length, self.height / 2), width=self.line_thickness)
        if self.gauge_height > 0:
            for x in range(0, self.slider_thumb.value_distance + 1):
                # The lines are slightly inaccurate at large ranges due to float imprecision...
                pygame.draw.line(self.image,
                                 BLACK,
                                 (self.thumb_width / 2 + self.slider_thumb.px_per_value * x, 0),
                                 (self.thumb_width / 2 + self.slider_thumb.px_per_value * x, self.gauge_height - 1),
                                 1)
        self.image.blit(self.slider_thumb.get_surface(),
                        (self.slider_thumb.get_position()[0] + self.thumb_width / 2,
                         self.slider_thumb.get_position()[1]))
        text_surf = self.render_text(str(self.slider_thumb.get_value()))
        self.image.blit(text_surf,
                        (sum((self.thumb_width, self.line_length, self.text_padding))
                         + self.max_text_width / 2 - text_surf.get_width() / 2,
                         self.height / 2 - text_surf.get_height() / 2))

    def update(self, mouse_obj: Mouse.Cursor, keyboard_events: List[pygame.event.Event]) -> None:
        relative_mouse = mouse_obj.copy()
        relative_mouse.set_pos(mouse_obj.get_pos()[0] - self.x - self.thumb_width / 2,
                               mouse_obj.get_pos()[1] - self.y - self.slider_thumb.get_position()[1])
        self.slider_thumb.update(relative_mouse)
        self.render_surface()

    def render_text(self, text: str) -> pygame.Surface:
        return pygame.transform.scale(self.font.render(text, True, self.text_color), self.resize_text(text))

    def resize_text(self, text: str) -> Tuple[float, int]:
        text_size = self.font.size(text)
        wh_ratio = text_size[0] / text_size[1]
        new_size = (self.text_height * wh_ratio, self.text_height)
        return new_size

    def set_slider_value(self, value: int) -> None:
        self.slider_thumb.set_value(value)

    def get_slider_value(self) -> int:
        return self.slider_thumb.get_value()

    @staticmethod
    def calc_size(text_height: int,
                  line_length: int,
                  thumb_width: int,
                  thumb_height: int,
                  font: pygame.font.Font,
                  max_value: int,
                  text_padding: int = 10) -> Tuple[float, int]:
        text_size = font.size(str(max_value))
        max_text_width = text_height * (text_size[0] / text_size[1])
        width = thumb_width + line_length + text_padding + max_text_width
        height = max(text_height, thumb_height)
        return width, height


class SliderButton(pygame.sprite.Sprite):
    def __init__(self,
                 y: Union[int, float],
                 width: int,
                 height: int,
                 dormant_color: Tuple[int, int, int],
                 active_color: Tuple[int, int, int],
                 slider_length: int,
                 min_value: int,
                 max_value: int):
        super().__init__()
        self.x = -width / 2
        self.y = y
        self.width = width
        self.height = height
        self.dormant_color = dormant_color
        self.active_color = active_color
        self.current_color = self.dormant_color
        self.slider_length = slider_length
        self.min_value = min_value
        self.max_value = max_value
        self.value_distance = self.max_value - self.min_value
        self.px_per_value = self.slider_length / self.value_distance
        self.current_value = self.min_value
        self.lock = True
        self.mouse_down = False
        self.mouse_offset = -1
        self.image = pygame.Surface((self.width, self.height))
        self.image.set_colorkey(TRANSPARENT)
        self.render_surface()
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.mask = pygame.mask.from_surface(self.image)

    def render_surface(self) -> None:
        self.image.fill(TRANSPARENT)
        draw_vtp_rounded_rect(self.image, (0, 0), (self.width, self.height), self.current_color)

    def update(self, mouse_obj: Mouse.Cursor) -> None:
        # Handle mouse-drag movement.
        if self.mouse_down and not mouse_obj.has_left():
            self.x = mouse_obj.get_pos()[0] - self.mouse_offset
            if self.x < -self.width / 2:
                self.x = -self.width / 2
            elif self.x > self.slider_length - self.width / 2:
                self.x = self.slider_length - self.width / 2
            mid_x = self.x + self.width / 2
            self.current_value = math.floor(self.min_value + mid_x // self.px_per_value
                                            + (mid_x % self.px_per_value > self.px_per_value / 2))
            self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        # Handle collisions.
        collision = pygame.sprite.collide_mask(self, mouse_obj)
        if collision is None:
            if not mouse_obj.get_button_state(1) and self.mouse_down:
                self.mouse_down = False
                self.stop_drag()
            self.lock = True
            self.current_color = self.dormant_color
        else:
            if mouse_obj.get_button_state(1) and not self.mouse_down and not self.lock:
                self.mouse_down = True
                self.start_drag(mouse_obj)
            elif not mouse_obj.get_button_state(1):
                if self.mouse_down:
                    self.mouse_down = False
                    self.stop_drag()
                self.lock = False
            self.current_color = self.active_color
        self.render_surface()
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def start_drag(self, mouse_obj: Mouse.Cursor) -> None:
        self.mouse_offset = mouse_obj.get_pos()[0] - self.x

    def stop_drag(self) -> None:
        self.mouse_offset = -1
        mid_x = self.x + self.width / 2
        whole, remainder = divmod(mid_x, self.px_per_value)
        if remainder:
            mid_x = whole * self.px_per_value + (self.px_per_value if remainder > self.px_per_value / 2 else 0)
            self.x = mid_x - self.width / 2

    def set_value(self, value: int) -> None:
        mid_x = (value - self.min_value) * self.px_per_value
        self.x = mid_x - self.width / 2
        self.current_value = value

    def get_position(self) -> Tuple[float, float]:
        return self.x, self.y

    def get_surface(self) -> pygame.Surface:
        return self.image

    def get_value(self) -> int:
        return self.current_value


class ScrollBar(BaseWidget):
    def __init__(self, width: int = 20, widget_name: str = "!scrollbar"):
        """A simple, functional scrollbar. It can be interacted with by dragging the thumb, clicking or holding down the
        up and down buttons, or using the scroll-wheel. The width of the scrollbar can be customized by passing a value
        to the 'width' parameter, but 20 pixels (the default) is the recommended width."""
        super().__init__(widget_name)
        # The values of most attributes cannot be calculated until the scrollbar is added to a parent.
        self.x = None
        self.y = 0
        self.width = width
        self.height = None
        self.content_height = 0
        self.scroll_factor = None
        self.button_scroll_amount = 10
        self.thumb = None
        self.up_button = None
        self.down_button = None
        self.image = None
        self.rect = None

    def set_parent(self, parent_widget: "Frame") -> None:
        self.parent = parent_widget
        self.x = self.parent.width - self.width
        self.height = self.parent.height
        self.image = pygame.Surface((self.width, self.height))
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.update_scrollbar_length(first_run=True)
        self.up_button = ScrollButton(0, 0, self.width, "up")
        self.down_button = ScrollButton(0, self.height - self.width, self.width, "down")

    def update_scrollbar_length(self, first_run: bool = False) -> None:
        track_length = self.height - self.width * 2
        content_height = self.parent.get_content_height()
        if not first_run and content_height == self.content_height:
            return None
        self.content_height = content_height
        cs_ratio = content_height / self.height
        thumb_length = track_length / cs_ratio
        if thumb_length > track_length:
            thumb_length = track_length
        elif thumb_length < 30:
            thumb_length = 30
        if first_run:
            self.thumb = ScrollThumb(self.width, self.height, thumb_length)
        else:
            self.thumb.update_thumb_length(thumb_length)
        scrollbar_distance = track_length - thumb_length
        content_distance = content_height - self.height
        if scrollbar_distance:
            self.scroll_factor = content_distance / scrollbar_distance
        else:
            # 'scrollbar_distance' is zero, that means no scrolling is needed.
            self.scroll_factor = None

    def render_surface(self) -> None:
        self.image.fill(GREY1)
        self.image.blit(self.thumb.image, (self.thumb.x, self.thumb.y + self.width))
        self.image.blit(self.up_button.image, self.up_button.rect)
        self.image.blit(self.down_button.image, self.down_button.rect)

    def update(self, mouse_obj: Mouse.Cursor, keyboard_events: List[pygame.event.Event]) -> None:
        relative_mouse = mouse_obj.copy()
        relative_mouse.set_pos(mouse_obj.get_pos()[0] - self.x, mouse_obj.get_pos()[1] - self.y)
        self.update_scrollbar_length()
        up_val = self.up_button.update(relative_mouse)
        down_val = self.down_button.update(relative_mouse)
        relative_mouse.set_pos(mouse_obj.get_pos()[0] - self.x, mouse_obj.get_pos()[1] - self.y - self.width)
        did_scroll = self.thumb.update(relative_mouse)
        if self.scroll_factor is not None:
            if did_scroll:
                # If the scrollbar was dragged, and there is space to scroll...
                self.parent.set_scroll_offset(-(self.scroll_factor * self.thumb.y))
            else:
                if mouse_obj.get_scroll() != 0:
                    self.scroll_by_content(mouse_obj.get_scroll())
                if up_val:
                    self.scroll_by_content(+self.button_scroll_amount)
                if down_val:
                    self.scroll_by_content(-self.button_scroll_amount)
        self.render_surface()

    def scroll_by_content(self, value: int) -> None:
        new_content_y = self.parent.add_scroll_offset(value)
        new_thumb_y = -new_content_y / self.scroll_factor
        self.thumb.force_set_pos(new_thumb_y)


class ScrollThumb(pygame.sprite.Sprite):
    def __init__(self,
                 scrollbar_width: int,
                 scrollbar_height: int,
                 thumb_length: float):
        super().__init__()
        self.x = 0
        self.y = 0
        self.width = scrollbar_width
        self.height = 0
        self.track_length = scrollbar_height - self.width * 2
        self.scroll_distance = 0
        self.dormant_color = GREY4
        self.active_color = GREY5
        self.dragged_color = GREY6
        self.current_color = self.dormant_color
        self.length_updated = False
        self.update_thumb_length(thumb_length)
        self.lock = True
        self.mouse_down = False
        self.mouse_offset = -1
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def update_thumb_length(self, thumb_length: float) -> None:
        self.length_updated = True
        self.height = thumb_length
        self.scroll_distance = self.track_length - self.height
        self.check_bounds()
        self.image = pygame.Surface((self.width, self.height))
        self.render_surface()

    def check_bounds(self) -> None:
        if self.y < 0:
            self.y = 0
        elif self.y > self.scroll_distance:
            self.y = self.scroll_distance

    def render_surface(self) -> None:
        self.image.fill(self.current_color)

    def force_set_pos(self, new_y: float) -> None:
        self.y = new_y
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, mouse_obj: Mouse.Cursor) -> bool:
        did_scroll = False
        if self.mouse_down and not mouse_obj.has_left():
            did_scroll = True
            self.y = mouse_obj.get_pos()[1] - self.mouse_offset
            self.check_bounds()
            self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        collision = pygame.sprite.collide_rect(self, mouse_obj)
        if collision:
            if mouse_obj.get_button_state(1) and not self.mouse_down and not self.lock:
                self.mouse_down = True
                self.start_drag(mouse_obj)
            elif not mouse_obj.get_button_state(1):
                if self.mouse_down:
                    self.mouse_down = False
                    self.stop_drag()
                self.lock = False
            self.current_color = self.active_color
        else:
            if not mouse_obj.get_button_state(1) and self.mouse_down:
                self.mouse_down = False
                self.stop_drag()
            self.lock = True
            self.current_color = self.dormant_color
        if did_scroll:
            self.current_color = self.dragged_color
        if self.length_updated:
            self.length_updated = False
            did_scroll = True
        self.render_surface()
        return did_scroll

    def start_drag(self, mouse_obj: Mouse.Cursor) -> None:
        self.mouse_offset = mouse_obj.get_pos()[1] - self.y

    def stop_drag(self) -> None:
        self.mouse_offset = -1


class ScrollButton(pygame.sprite.Sprite):
    def __init__(self,
                 x: Union[int, float],
                 y: Union[int, float],
                 button_length: int,
                 direction: Literal["up", "down"]):
        super().__init__()
        self.x = x
        self.y = y
        self.length = button_length
        self.direction = direction
        self.arrow_size = (self.length - 11, self.length - 15)
        self.lock = True
        self.mouse_down = False
        self.start_delay = 0.2
        self.repeat_delay = 0.1
        self.button_timer = Time.Time()
        self.repeating = False
        # Color format: (bg, fg)
        self.dormant_color = (GREY1, GREY6)
        self.active_color = (GREY2, BLACK)
        self.dragged_color = (GREY6, WHITE)
        self.current_color = self.dormant_color
        self.image = pygame.Surface((self.length, self.length))
        self.rect = pygame.Rect(self.x, self.y, self.length, self.length)

    def render_surface(self) -> None:
        self.image.fill(self.current_color[0])
        draw_triangle(self.image,
                      (round(self.length / 2 - self.arrow_size[0] / 2) - 1,
                       round(self.length / 2 - self.arrow_size[1] / 2) - 1),
                      self.arrow_size,
                      self.current_color[1],
                      self.direction == "down")

    def update(self, mouse_obj: Mouse.Cursor) -> bool:
        trigger = False
        collision = pygame.sprite.collide_rect(self, mouse_obj)
        if collision:
            if mouse_obj.get_button_state(1) and not self.mouse_down and not self.lock:
                self.mouse_down = True
                trigger = True
                self.button_timer.reset_timer()
            elif not mouse_obj.get_button_state(1):
                if self.mouse_down:
                    self.mouse_down = False
                self.lock = False
            self.current_color = self.active_color
        else:
            if not mouse_obj.get_button_state(1) and self.mouse_down:
                self.mouse_down = False
            self.lock = True
            self.current_color = self.dormant_color
        if self.mouse_down:
            if self.repeating and self.button_timer.get_time() > self.repeat_delay:
                trigger = True
                self.button_timer.reset_timer()
            elif self.button_timer.get_time() > self.start_delay:
                self.repeating = True
                self.button_timer.reset_timer()
            self.current_color = self.dragged_color
        else:
            self.repeating = False
        self.render_surface()
        return trigger


class Spinner(BaseWidget):
    def __init__(self,
                 x: Union[int, float],
                 y: Union[int, float],
                 size: int,
                 thickness: int,
                 lit_length: int,
                 speed: Union[int, float],
                 unlit_color: Tuple[int, int, int],
                 lit_color: Tuple[int, int, int],
                 widget_name: str = "!spinner"):
        """A simple, highly customizable spinner widget. Unfortunately, the arc that makes up the spinner will have
        'holes' in it at higher thicknesses due to limitations in the 'pygame.draw.arc' function."""
        super().__init__(widget_name)
        self.x = x
        self.y = y
        self.length = size
        self.lit_length = lit_length
        self.thickness = thickness
        self.speed = speed
        self.angle = 0
        self.delta_timer = Time.Time()
        self.unlit_color = unlit_color
        self.lit_color = lit_color
        self.image = pygame.Surface((self.length, self.length))
        self.image.set_colorkey(TRANSPARENT)
        self.rect = pygame.Rect(self.x, self.y, self.length, self.length)
        self.delta_timer.reset_timer()

    def render_surface(self) -> None:
        # radians = degrees × (π ÷ 180)
        # Angle system: 0° = EAST, 90° = NORTH, 180° = WEST, 360° = SOUTH
        self.image.fill(TRANSPARENT)
        pygame.draw.arc(self.image,
                        self.unlit_color,
                        (0, 0, self.length, self.length),
                        0,
                        math.radians(360),
                        self.thickness)
        start_angle = 360 - ((self.angle + self.lit_length) % 360)
        end_angle = 360 - self.angle
        pygame.draw.arc(self.image,
                        self.lit_color,
                        (0, 0, self.length, self.length),
                        math.radians(start_angle),
                        math.radians(end_angle),
                        self.thickness)

    def update(self, mouse_obj: Mouse.Cursor, keyboard_events: List[pygame.event.Event]) -> None:
        d_t = self.delta_timer.get_time()
        self.delta_timer.reset_timer()
        self.angle += self.speed * d_t
        self.angle %= 360
        self.render_surface()


class Frame(BaseWidget):
    def __init__(self, x: Union[int, float], y: Union[int, float], width: int, height: int, padding_bottom: int,
                 bg: Union[Tuple[int, int, int], Tuple[int, int, int, int]] = (0, 0, 0, 0), z_index: int = 1,
                 widget_name: str = "!frame"):
        """Container class for all widgets. Every widget should be added to a frame after initialization. User input can
        then be passed to all widgets in the frame by calling the frame's 'update' method and passing a 'Mouse.Cursor'
        object and a list of 'pygame.event.Event' objects as parameters. After updating, the frame can be directly
        rendered to the screen using its 'image' and 'rect' attributes."""
        super().__init__(widget_name)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.window_data: Dict[str, Optional[Union[List[int], Tuple[Union[int, float], Union[int, float]]]]] = {}
        self.padding_bottom = padding_bottom
        self.bg = bg
        self.scroll_constant = 20
        self.z_index = z_index
        self.text_input = False
        self.cursor_display = "arrow"  # Literal["arrow", "i_beam", "text_drag"]
        self.cursor_icons = Mouse.CursorIcons()
        self.cursor_icons.init_cursors()
        self.y_scroll_offset = 0
        # Using per-pixel alpha is necessary because we don't know what colors the surface returned by
        # `pygame.font.Font.render` might contain, and the surfaces of most child widgets will contain text.
        self.image = pygame.Surface((width, height), flags=pygame.SRCALPHA)
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.child_widgets = {}
        # Stores the order with which widgets will be rendered. The last item will be rendered last, and therefore
        # will be on the topmost layer.
        self.render_z_order = []

    def add_widget(self, widget_obj: Union[BaseWidget, RadioGroup]) -> None:
        if isinstance(widget_obj, RadioGroup):
            for w in widget_obj.get_children():
                self.add_widget(w)
        else:
            if widget_obj.get_widget_name() in self.child_widgets:
                raise FrameError(widget_obj, 1)
            elif widget_obj.has_parent():
                raise FrameError(widget_obj, 2)
            else:
                widget_obj.set_parent(self)
                self.child_widgets[widget_obj.get_widget_name()] = widget_obj
                self.render_z_order.append(widget_obj.get_widget_name())
                if isinstance(widget_obj, Entry):
                    widget_obj.update_real_pos((self.x + widget_obj.get_pos()[0],
                                                self.y + widget_obj.get_pos()[1] + self.y_scroll_offset))

    def delete_widget(self, widget_id: str) -> None:
        if widget_id in self.child_widgets:
            self.child_widgets.pop(widget_id)
            self.render_z_order.remove(widget_id)
        else:
            raise WidgetIDError(widget_id)

    def get_content_height(self) -> int:
        return max((widget.y + widget.image.get_height())
                   for widget in self.child_widgets.values()
                   if not isinstance(widget, ScrollBar)) + self.padding_bottom

    def add_scroll_offset(self, amount: int) -> float:
        """Adds a value to the current scroll offset and returns the result."""
        self.y_scroll_offset += amount + math.copysign(self.scroll_constant, amount)
        if self.y_scroll_offset > 0:
            self.y_scroll_offset = 0
        elif self.y_scroll_offset < -(self.get_content_height() - self.height):
            self.y_scroll_offset = -(self.get_content_height() - self.height)
        self.update_ime_rect()
        return self.y_scroll_offset

    def set_scroll_offset(self, offset: int) -> None:
        self.y_scroll_offset = offset
        self.update_ime_rect()

    def calc_resized_ime_rect(self, original_rect: pygame.Rect) -> pygame.Rect:
        if self.window_data:
            return pygame.Rect(*dilate_coordinates(original_rect.topleft, self.window_data["fixed_res"],
                                                   self.window_data["current_res"], self.window_data["resized_res"]),
                               original_rect.width, original_rect.height)
        else:
            return original_rect

    def update_window_data(self, fixed_res: Tuple[int, int], current_res: List[int],
                           resized_res: Tuple[Union[int, float], Union[int, float]]) -> None:
        """Only needed for frames that contain entry widgets. Every time the window is resized, this method should be
        called before the 'update' method. This method can be ignored if the window is not resizable."""
        self.window_data["fixed_res"] = fixed_res
        self.window_data["current_res"] = current_res
        self.window_data["resized_res"] = resized_res

    def update_ime_rect(self) -> None:
        for widget in self.child_widgets.values():
            if isinstance(widget, Entry):
                widget.update_real_pos((self.x + widget.get_pos()[0],
                                        self.y + widget.get_pos()[1] + self.y_scroll_offset))

    def update(self, mouse_obj: Mouse.Cursor, keyboard_events: List[pygame.event.Event]) -> None:
        if self.z_index == mouse_obj.get_z_index() and self.rect.collidepoint(*mouse_obj.get_pos()):
            pointer_events = True
            abs_pos = mouse_obj.get_pos()
            scrolled_rel_mouse = mouse_obj.copy()
            scrolled_rel_mouse.set_pos(abs_pos[0] - self.x, abs_pos[1] - self.y - self.y_scroll_offset)
        else:
            pointer_events = False
            scrolled_rel_mouse = Mouse.Cursor()
            scrolled_rel_mouse.mouse_leave()  # Dummy mouse object to prevent collision.
            if self.z_index != mouse_obj.get_z_index():
                keyboard_events = []
        collide = False
        return_values = []
        for widget in self.child_widgets.values():
            if not collide:
                collide = bool(pygame.sprite.collide_mask(widget, scrolled_rel_mouse)) if hasattr(widget, "mask")\
                          else pygame.sprite.collide_rect(widget, scrolled_rel_mouse)
            if isinstance(widget, Entry):
                value = widget.update(scrolled_rel_mouse, keyboard_events)
                return_values.append(value)
            elif isinstance(widget, ScrollBar):
                if self.z_index == mouse_obj.get_z_index():
                    abs_pos = mouse_obj.get_pos()
                    rel_mouse = mouse_obj.copy()
                    rel_mouse.set_pos(abs_pos[0] - self.x, abs_pos[1] - self.y)
                else:
                    rel_mouse = Mouse.Cursor()
                    rel_mouse.mouse_leave()
                widget.update(rel_mouse, keyboard_events)
            else:
                widget.update(scrolled_rel_mouse, keyboard_events)
        if return_values:
            if any(i[2] for i in return_values):
                if not self.text_input:
                    self.text_input = True
                    pygame.key.start_text_input()
            else:
                if self.text_input:
                    self.text_input = False
                    pygame.key.stop_text_input()
            if any(i[1] for i in return_values):
                if self.cursor_display != "text_drag":
                    self.cursor_display = "text_drag"
                    pygame.mouse.set_cursor(self.cursor_icons.get_cursor(2))
            elif any(i[0] for i in return_values):
                if self.cursor_display != "i_beam":
                    self.cursor_display = "i_beam"
                    pygame.mouse.set_cursor(self.cursor_icons.get_cursor(1))
            else:
                if self.cursor_display != "arrow":
                    self.cursor_display = "arrow"
                    pygame.mouse.set_cursor(self.cursor_icons.get_cursor(0))
        self.render_widgets()
        if pointer_events and (not collide):
            mouse_obj.increment_z_index()

    def render_widgets(self) -> None:
        self.image.fill(self.bg)
        for w_name in self.render_z_order:
            widget_y = (self.child_widgets[w_name].y
                        + (0 if isinstance(self.child_widgets[w_name], ScrollBar) else self.y_scroll_offset))
            if widget_y + self.child_widgets[w_name].image.get_height() >= 0 and widget_y < self.height:
                self.image.blit(self.child_widgets[w_name].image, (self.child_widgets[w_name].rect.x, widget_y))

    def raise_widget_layer(self, widget_name: str) -> None:
        """
        Raises the widget with the given name to the top of the render z-order.
        """
        if widget_name in self.render_z_order:
            # Move the widget name to the end of the list.
            index = self.render_z_order.index(widget_name)
            if index < len(self.render_z_order) - 1:
                self.render_z_order.append(self.render_z_order.pop(index))
        else:
            raise WidgetIDError(widget_name)

    def update_position(self, new_x: int, new_y: int) -> None:
        self.x = new_x
        self.y = new_y
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)


class Window(pygame.sprite.Sprite):
    def __init__(self,
                 x: Union[int, float],
                 start_y: Union[int, float],
                 final_y: Union[int, float],
                 bg: Tuple[int, int, int],
                 overlay_max_alpha: int,
                 active_color: Tuple[int, int, int],
                 dormant_color: Tuple[int, int, int],
                 border_radius: int,
                 button_length: int,
                 button_padding: int,
                 button_thickness: int,
                 speed_factor: float,
                 content_frame: Frame,
                 destination_surf: pygame.Surface,
                 z_index: int):
        """A popup-window widget that takes a frame instance to be used as its content. The window has a nice entry and
        exit animation, and contains a close button in its title bar."""
        super().__init__()
        self.x = x
        self.y = start_y
        self.start_y = start_y
        self.final_y = final_y
        self.content_frame = content_frame
        self.content_pos = (border_radius, border_radius + button_length + button_padding)
        self.width = border_radius * 2 + self.content_frame.width
        self.height = border_radius * 2 + button_length + button_padding + self.content_frame.height
        self.distance = self.start_y - self.final_y
        self.direction: Literal["u", "d", "i", "r"] = "u"
        self.bg = bg
        self.destination_surf = destination_surf
        self.z_index = z_index
        self.close_button = WindowButton(self.width - border_radius - button_length,
                                         border_radius,
                                         button_length,
                                         button_thickness,
                                         active_color,
                                         dormant_color)
        self.overlay = WindowOverlay(self.destination_surf.get_width(),
                                     self.destination_surf.get_height(),
                                     overlay_max_alpha,
                                     self.distance)
        self.border_radius = border_radius
        self.speed_factor = speed_factor
        self.timer = Time.Time()
        self.timer.reset_timer()
        self.image = pygame.Surface((self.width, self.height), flags=pygame.SRCALPHA)
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def render_surface(self) -> None:
        self.image.fill((0, 0, 0, 0))
        draw_rounded_rect(self.image, (0, 0), (self.width, self.height), self.border_radius, self.bg)
        self.image.blit(self.content_frame.image, self.content_pos)
        self.image.blit(self.close_button.image, self.close_button.rect)

    def update(self, mouse_obj: Mouse.Cursor, keyboard_events: list[pygame.event.Event]) -> bool:
        updated_mouse = mouse_obj.copy()
        rel_mouse = mouse_obj.copy()
        rel_mouse.set_pos(mouse_obj.get_pos()[0] - self.x, mouse_obj.get_pos()[1] - self.y)
        if self.z_index != mouse_obj.get_z_index():
            updated_mouse.mouse_leave()
            rel_mouse.mouse_leave()
            keyboard_events = []
        if self.direction in ("u", "d"):
            delta_time = self.timer.get_time()
            self.timer.reset_timer()
            self.distance *= pow(self.speed_factor, delta_time)
            if round(self.distance) > 0:
                self.y = self.final_y + self.distance if self.direction == "u" else self.start_y - self.distance
            else:
                self.y = self.final_y if self.direction == "u" else self.start_y
                self.direction = "i" if self.direction == "u" else "r"
            self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
            self.content_frame.update_position(self.x + self.content_pos[0], self.y + self.content_pos[1])
            dummy_mouse = mouse_obj.copy()
            dummy_mouse.mouse_leave()
            self.close_button.update(dummy_mouse)
            self.overlay.update(self.start_y - self.y)
        elif self.direction == "i":
            if self.close_button.update(rel_mouse):
                self.close_window()
        self.content_frame.update(updated_mouse, keyboard_events)
        self.render_surface()
        return self.direction == "r"

    def draw(self) -> None:
        self.destination_surf.blit(self.overlay.image, self.overlay.rect)
        self.destination_surf.blit(self.image, self.rect)

    def close_window(self, bypass_idle_check: bool = False) -> None:
        if self.direction == "i" or bypass_idle_check:
            self.distance = self.start_y - self.final_y
            self.direction = "d"
            self.timer.reset_timer()


class WindowButton(pygame.sprite.Sprite):
    def __init__(self,
                 x: Union[int, float],
                 y: Union[int, float],
                 length: int,
                 thickness: int,
                 active_color: Tuple[int, int, int],
                 dormant_color: Tuple[int, int, int]):
        super().__init__()
        self.x = x
        self.y = y
        self.width = length
        self.height = length
        self.thickness = thickness
        self.active_color = active_color
        self.dormant_color = dormant_color
        self.current_color = self.dormant_color
        self.lock = True
        self.mouse_down = False
        self.image = pygame.Surface((self.width, self.height))
        self.image.set_colorkey(TRANSPARENT)
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def render_surface(self) -> None:
        self.image.fill(TRANSPARENT)
        draw_cross(self.image, (0, 0), (self.width, self.height), self.thickness, self.current_color)

    def update(self, mouse_obj: Mouse.Cursor) -> bool:
        collision = pygame.sprite.collide_rect(self, mouse_obj)
        clicked = False
        if collision:
            if mouse_obj.get_button_state(1) and not self.mouse_down and not self.lock:
                self.mouse_down = True
            elif not mouse_obj.get_button_state(1):
                if self.mouse_down:
                    self.mouse_down = False
                    clicked = True
                self.lock = False
            self.current_color = self.active_color
        else:
            if not mouse_obj.get_button_state(1) and self.mouse_down:
                self.mouse_down = False
            self.lock = True
            self.current_color = self.dormant_color
        self.render_surface()
        return clicked


class BaseOverlay:
    def __init__(self, width: int, height: int):
        """Base class for all effects that places a partially transparent overlay over the screen."""
        self.x = 0
        self.y = 0
        self.width = width
        self.height = height
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(BLACK)
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)


class SceneTransition(BaseOverlay):
    def __init__(self, width: int, height: int, speed: int):
        """A simple transition effect. The screen will steadily darken until fully black, then the same animation is
        played in reverse until fully transparent. This transition is useful for making scene-changes less abrupt."""
        super().__init__(width, height)
        self.alpha = 0
        self.speed = speed
        self.max_alpha = 255
        self.timer = Time.Time()
        self.timer.reset_timer()

    def update(self) -> int:
        """Returns 1 on the frame the animation enters the second stage, and returns 2 when the animation is done, else
        returns 0."""
        return_code = 0
        delta_time = self.timer.get_time()
        self.timer.reset_timer()
        self.alpha += self.speed * delta_time
        if self.alpha >= self.max_alpha:
            self.speed = -self.speed
            self.alpha = self.max_alpha - self.alpha % self.max_alpha
            return_code = 1
        elif self.alpha < 0:
            self.alpha = 0
            return_code = 2
        self.image.set_alpha(round(self.alpha))
        return return_code


class WindowOverlay(BaseOverlay):
    def __init__(self, width: int, height: int, max_alpha: int, total_distance: Union[int, float]):
        """Darkens the screen by an amount proportionate to the distance the window has moved from the edge of the
        screen as it plays its entry animation. The same animation is played in reverse when the window plays its exit
        animation. This effect is useful for directing the user's attention to the active window."""
        super().__init__(width, height)
        self.alpha = 0
        self.max_alpha = max_alpha
        self.total_distance = total_distance

    def update(self, moved_distance: Union[int, float]) -> None:
        self.alpha = self.max_alpha * (moved_distance / self.total_distance)
        self.image.set_alpha(round(self.alpha))


class WidgetIDError(Exception):
    def __init__(self, widget_id: str):
        """This exception is raised if a non-existent widget identifier is passed to a frame method."""
        super().__init__("A widget with the ID '{}' doesn't exist in this frame".format(widget_id))
        self.widget_id = widget_id

    def get_failed_id(self) -> str:
        return self.widget_id


class FrameError(Exception):
    def __init__(self, widget: BaseWidget, error_type: int):
        """A simple exception class for handling frame-related errors."""
        if error_type == 1:
            message = "The frame already contains a widget with the ID '{}'"\
                .format(widget.get_widget_name())
        elif error_type == 2:
            message = "The widget with the ID '{}' has already been added to a parent frame"\
                .format(widget.get_widget_name())
        else:
            message = "Unknown error"
        super().__init__(message)
        self.failed_widget = widget

    def get_failed_widget(self) -> BaseWidget:
        return self.failed_widget
