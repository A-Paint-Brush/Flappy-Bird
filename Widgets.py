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


class WordWrappedText(BaseWidget):
    def __init__(self,
                 x: int,
                 y: int,
                 text: str,
                 fg: Tuple[int, int, int],
                 width: int,
                 font: pygame.font.Font,
                 widget_name: str = "!label"):
        super().__init__(widget_name)
        self.x = x
        self.y = y
        self.text_lines = word_wrap_text(text, width, font)
        self.line_height = font.size("|")[1]
        self.rect = pygame.Rect(self.x, self.y, width, self.line_height * len(self.text_lines))
        self.image = pygame.Surface((self.rect.width, self.rect.height), flags=pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))
        for index, text in enumerate(self.text_lines):
            size = font.size(text)
            surface = font.render(text, True, fg)
            self.image.blit(surface, (width / 2 - size[0] / 2, index * self.line_height))


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
        draw_rounded_rect(self.image, (0, 0), self.image.get_size(), self.button_radius, bg)
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
        self.image = pygame.Surface((length, length))
        self.image.set_colorkey(TRANSPARENT)
        self.image.fill(TRANSPARENT)
        self.normal_color = GREY
        self.active_color = CYAN
        self.current_color = self.normal_color
        draw_rounded_rect(self.image, (0, 0), (length, length), radius, BLACK)
        draw_rounded_rect(self.image,
                          (border, border),
                          (length - border * 2, length - border * 2),
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
                          (self.border, self.border),
                          (self.length - self.border * 2, self.length - self.border * 2),
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
            pygame.draw.circle(self.image, BLACK, (self.radius, self.radius), self.radius - 5, 0)

    def unselect(self) -> None:
        self.selected = False


class Entry(BaseWidget):
    def __init__(self,
                 x: int,
                 y: int,
                 width: int,
                 height: int,
                 padding: int,
                 font: pygame.font.Font,
                 fg: Tuple[int, int, int],
                 widget_name: str = "!entry"):
        super().__init__(widget_name)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.padding = padding
        self.border_thickness = 2
        self.shift = False
        self.selecting = False
        self.start_select = True
        self.normal_border = BLACK
        self.active_border = BLUE
        self.current_border = self.normal_border
        self.cursors = Mouse.CursorIcons()
        self.mouse_icon = "normal"  # Literal["normal", "i_beam", "block_select"]
        self.cursors.init_cursors()
        self.drag_pos = None
        self.drag_pos_recorded = False
        self.dnd_start_x = -1
        self.dnd_distance = 0
        self.dnd_x_recorded = False
        self.lock = True
        self.mouse_down = False
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
                                                 lambda: self.text_canvas.backspace()],
                            pygame.K_DELETE: [False,
                                              Time.Time(),
                                              False,
                                              Time.Time(),
                                              lambda: self.text_canvas.delete()]}
        self.start_delay = 1
        self.repeat_delay = 0.1
        self.scroll_hit_box = 30
        self.text_canvas = EntryText(width - padding * 2, height - padding * 2, font, fg)
        self.image = pygame.Surface((width, height))
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def render_text_canvas(self) -> None:
        self.image.fill(self.current_border)
        pygame.draw.rect(self.image, WHITE, [self.border_thickness,
                                             self.border_thickness,
                                             self.width - self.border_thickness * 2,
                                             self.height - self.border_thickness * 2],
                         0)
        self.image.blit(source=self.text_canvas.get_surface(),
                        dest=(self.padding, self.padding),
                        area=self.text_canvas.get_view_rect())

    def update_real_pos(self, real_pos: Tuple[Union[int, float], Union[int, float]]) -> None:
        self.text_canvas.update_text_rect(real_pos)

    def update(self, mouse_obj: Mouse.Cursor, keyboard_event: pygame.event.Event) -> None:
        collide = pygame.sprite.collide_rect(self, mouse_obj)
        if collide:
            if mouse_obj.get_button_state(1):
                if not self.lock:
                    self.mouse_down = True
                    self.text_canvas.focus_get()
            elif not mouse_obj.get_button_state(1):
                self.mouse_down = False
                self.lock = False
            self.current_border = self.active_border
            if (not self.text_canvas.dnd_event_ongoing()) and self.mouse_icon != "i_beam":
                self.mouse_icon = "i_beam"
                pygame.mouse.set_cursor(self.cursors.get_cursor(1))
        else:
            if mouse_obj.get_button_state(1):
                self.mouse_down = True
                if self.lock:
                    self.text_canvas.focus_lose()
            elif not mouse_obj.get_button_state(1):
                self.mouse_down = False
                self.lock = True
            self.current_border = self.normal_border
            if (not self.text_canvas.dnd_event_ongoing()) and self.mouse_icon != "normal":
                self.mouse_icon = "normal"
                pygame.mouse.set_cursor(self.cursors.get_cursor(0))
        abs_pos = mouse_obj.get_pos()
        rel_mouse = mouse_obj.copy()
        rel_mouse.set_pos(abs_pos[0] - self.x - self.padding, abs_pos[1] - self.y - self.padding)
        if keyboard_event is not None:
            if keyboard_event.type == pygame.KEYDOWN or keyboard_event.type == pygame.KEYUP:
                if keyboard_event.mod & pygame.KMOD_SHIFT:
                    self.shift = True
                else:
                    if self.shift:
                        self.shift = False
                        if not self.start_select:
                            self.text_canvas.end_selection()
                            self.start_select = True
            if keyboard_event.type == pygame.KEYDOWN:
                if keyboard_event.key == pygame.K_TAB:
                    self.text_canvas.add_text("\t".expandtabs(tabsize=4))
                elif keyboard_event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_BACKSPACE, pygame.K_DELETE):
                    if not self.sticky_keys[keyboard_event.key][0]:
                        if keyboard_event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                            if self.shift and self.start_select:
                                self.text_canvas.start_selection()
                                self.start_select = False
                        self.sticky_keys[keyboard_event.key][4]()
                        self.sticky_keys[keyboard_event.key][0] = True
                        self.sticky_keys[keyboard_event.key][1].reset_timer()
                elif keyboard_event.key == pygame.K_HOME:
                    self.text_canvas.caret_home()
                elif keyboard_event.key == pygame.K_END:
                    self.text_canvas.caret_end()
                elif keyboard_event.mod & pygame.KMOD_CTRL:
                    if keyboard_event.key == pygame.K_c:
                        self.text_canvas.copy_text()
                    elif keyboard_event.key == pygame.K_v:
                        self.paste_text()
                    elif keyboard_event.key == pygame.K_a:
                        self.text_canvas.select_all()
                    elif keyboard_event.key == pygame.K_x:
                        self.text_canvas.copy_text()
                        self.text_canvas.backspace()
                    elif keyboard_event.key == pygame.K_z:
                        if self.shift:
                            self.text_canvas.redo()
                        else:
                            self.text_canvas.undo()
                    elif keyboard_event.key == pygame.K_y:
                        self.text_canvas.redo()
            elif keyboard_event.type == pygame.KEYUP:
                if keyboard_event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_BACKSPACE, pygame.K_DELETE):
                    self.sticky_keys[keyboard_event.key][0] = False
                    self.sticky_keys[keyboard_event.key][2] = False
            elif keyboard_event.type == pygame.TEXTINPUT:
                self.text_canvas.add_text(keyboard_event.text)
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
                elif mouse_obj.get_pos()[0] > self.x + (self.width - self.scroll_hit_box):
                    self.text_canvas.move_view_by_pos("l")
            if self.text_canvas.mouse_collision(rel_mouse):
                if not self.drag_pos_recorded:
                    self.drag_pos_recorded = True
                    self.drag_pos = rel_mouse.copy()
                self.text_canvas.update_caret_pos(rel_mouse.get_pos())
                if not self.dnd_x_recorded:
                    self.dnd_x_recorded = True
                    self.dnd_start_x = rel_mouse.get_pos()[0]
                if self.text_canvas.selection_event_ongoing() and (not self.text_canvas.dnd_event_ongoing()):
                    if abs(rel_mouse.get_pos()[0] - self.dnd_start_x) > self.dnd_distance:
                        self.text_canvas.start_dnd_event(rel_mouse)
                        if self.mouse_icon != "block_select":
                            self.mouse_icon = "block_select"
                            pygame.mouse.set_cursor(self.cursors.get_cursor(2))
                if (not self.selecting) and \
                        (not self.text_canvas.dnd_event_ongoing()) and \
                        (not self.text_canvas.selection_rect_collide(rel_mouse.get_pos())):
                    self.text_canvas.start_selection()
                    self.selecting = True
        elif not mouse_obj.get_button_state(1):
            if self.text_canvas.mouse_collision(rel_mouse):
                if self.dnd_start_x != -1 and self.text_canvas.selection_event_ongoing():
                    if self.text_canvas.selection_rect_collide(rel_mouse.get_pos()):
                        if abs(rel_mouse.get_pos()[0] - self.dnd_start_x) == self.dnd_distance:
                            self.text_canvas.cancel_dnd_event()
                            self.text_canvas.start_selection()
                            self.text_canvas.end_selection()
            if self.text_canvas.dnd_event_ongoing():
                self.text_canvas.end_dnd_event()
            if self.selecting:
                self.selecting = False
                self.text_canvas.update_caret_pos(rel_mouse.get_pos())
                self.text_canvas.end_selection()
            self.drag_pos_recorded = False
            self.drag_pos = None
            self.dnd_x_recorded = False
            self.dnd_start_x = -1
        self.text_canvas.update()
        self.render_text_canvas()

    def paste_text(self) -> None:
        text = pygame.scrap.get(pygame.SCRAP_TEXT)
        if text is not None:
            try:
                text = "".join(c for c in text.decode("utf-8", "ignore") if c.isprintable())
            except pygame.error:
                text = None
            if text is not None:
                self.text_canvas.add_text(text)

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
        self.scroll_amount = 40
        self.scroll_time = 0
        self.scroll_timer = Time.Time()
        self.scroll_timer.reset_timer()
        self.display_caret = True
        self.focus = False
        self.surface = pygame.Surface((self.caret_width, self.view_height))
        self.surface.fill(WHITE)
        self.rect = pygame.Rect(self.x, self.y, *self.surface.get_size())
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
            if self.x + current_width < self.scroll_padding:
                self.move_view_by_caret("r")
            elif self.x + current_width >= self.view_width - self.scroll_padding:
                self.move_view_by_caret("l")
            self.rect = pygame.Rect(self.x, self.y, *self.surface.get_size())

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
            if self.x + current_width < self.scroll_padding:
                self.move_view_by_caret("r")
            elif self.x + current_width >= self.view_width - self.scroll_padding:
                self.move_view_by_caret("l")
            self.rect = pygame.Rect(self.x, self.y, *self.surface.get_size())

    def selection_event_ongoing(self) -> bool:
        return self.select_start != -1 and self.select_end != -1 and (not self.selecting)

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
            selection = self.text[self.select_start:self.select_end]
            front = self.text[:self.select_start]
            back = self.text[self.select_end:]
            self.text = front + back
            front = self.text[:self.caret_index]
            back = self.text[self.caret_index:]
            self.text = front + selection + back
            self.select_start = -1
            self.select_end = -1
            self.select_rect = None
            self.record_undo()

    def cancel_dnd_event(self) -> None:
        self.dnd_event = False

    def dnd_event_ongoing(self) -> bool:
        return self.dnd_event

    def add_text(self, text) -> None:
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
        new_size = self.calc_text_size(self.text)
        self.surface = pygame.Surface((new_size[0] + self.caret_width, new_size[1]))
        self.reset_caret()
        if not overwrite:
            self.caret_index += len(text)
        current_width = self.calc_location_width()
        if self.x + current_width < self.scroll_padding:
            self.move_view_by_caret("r")
        elif self.x + current_width >= self.view_width - self.scroll_padding:
            self.move_view_by_caret("l")
        self.rect = pygame.Rect(self.x, self.y, *self.surface.get_size())
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
        current_width = self.calc_location_width()
        if current_width < self.view_width - self.scroll_padding * 2:
            self.x = 0
        elif self.x + current_width < self.scroll_padding:
            self.move_view_by_caret("r")
        elif self.x + current_width < self.view_width - self.scroll_padding:
            self.move_view_by_caret("l")
        self.rect = pygame.Rect(self.x, self.y, *self.surface.get_size())
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
        current_width = self.calc_location_width()
        if current_width < self.view_width - self.scroll_padding * 2:
            self.x = 0
        elif self.x + current_width < self.scroll_padding:
            self.move_view_by_caret("r")
        elif self.x + current_width < self.view_width - self.scroll_padding:
            self.move_view_by_caret("l")
        self.rect = pygame.Rect(self.x, self.y, *self.surface.get_size())
        self.record_undo()
        self.cancel_dnd_event()
        self.reset_caret()

    def copy_text(self) -> None:
        if (self.select_start != -1 or self.selecting) and self.focus:
            if self.selecting:
                if self.caret_index > self.select_start:
                    selection = self.text[self.select_start:self.caret_index]
                else:
                    selection = self.text[self.caret_index:self.select_start]
            else:
                selection = self.text[self.select_start:self.select_end]
            try:
                pygame.scrap.put(pygame.SCRAP_TEXT, selection.encode("utf-8", "ignore"))
            except pygame.error:
                return None

    def calc_location_width(self) -> float:
        return self.calc_text_size(self.text[:self.caret_index])[0]

    def reset_caret(self) -> None:
        self.display_caret = True
        self.caret_timer.reset_timer()

    def update_caret_pos(self, mouse_pos) -> None:
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
                self.select_rect = pygame.Rect(start_pos, 0, abs(end_pos - start_pos), self.view_height)
            else:
                self.select_rect = pygame.Rect(end_pos, 0, abs(end_pos - start_pos), self.view_height)

    def select_all(self) -> None:
        if self.focus:
            self.select_start = 0
            self.select_end = len(self.text)
            start_pos = self.calc_text_size(self.text[:self.select_start])[0]
            end_pos = self.calc_text_size(self.text[:self.select_end])[0]
            self.select_rect = pygame.Rect(start_pos, 0, end_pos - start_pos, self.view_height)
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
            self.select_rect = pygame.Rect(start_pos, 0, end_pos - start_pos, self.view_height)

    def change_caret_pos(self, direction: Literal["l", "r"]) -> None:
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
                self.select_rect = pygame.Rect(start_pos, 0, abs(end_pos - start_pos), self.view_height)
            else:
                self.select_rect = pygame.Rect(end_pos, 0, abs(end_pos - start_pos), self.view_height)
        else:
            self.select_start = -1
            self.select_end = -1
            self.select_rect = None
        self.reset_caret()
        self.cancel_dnd_event()
        current_width = self.calc_location_width()
        if self.x + current_width < self.scroll_padding:
            self.move_view_by_caret("r")
        elif self.x + current_width >= self.view_width - self.scroll_padding:
            self.move_view_by_caret("l")
        self.rect = pygame.Rect(self.x, self.y, *self.surface.get_size())

    def caret_home(self) -> None:
        if self.focus:
            if self.select_start != -1 or self.selecting:
                self.select_start = -1
                self.select_end = -1
                self.select_rect = None
            self.caret_index = 0
            self.x = 0
            self.rect = pygame.Rect(self.x, self.y, *self.surface.get_size())
            self.cancel_dnd_event()

    def caret_end(self) -> None:
        if self.focus:
            if self.select_start != -1 or self.selecting:
                self.select_start = -1
                self.select_end = -1
                self.select_rect = None
            self.caret_index = len(self.text)
            if self.calc_text_size(self.text)[0] >= self.view_width - self.scroll_padding:
                self.move_view_by_caret("l")
            self.cancel_dnd_event()

    def update(self) -> None:
        self.scroll_time = self.scroll_timer.get_time()
        self.scroll_timer.reset_timer()
        if not self.focus:
            self.surface.fill(WHITE)
            if self.select_rect is not None:
                pygame.draw.rect(self.surface, BLUE, self.select_rect, 0)
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
        self.surface.fill(WHITE)
        if self.select_rect is not None:
            pygame.draw.rect(self.surface, BLUE, self.select_rect, 0)
        self.surface.blit(self.render_text(), (0, 0))
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

    def calc_text_size(self, text) -> Tuple[float, int]:
        text_size = self.font.render(text, True, self.text_color, WHITE).get_size()
        wh_ratio = text_size[0] / text_size[1]
        new_size = (self.view_height * wh_ratio, self.view_height)
        return new_size

    def update_text_rect(self, real_pos: Tuple[Union[int, float], Union[int, float]]) -> None:
        pygame.key.set_text_input_rect(pygame.Rect(*real_pos, self.view_width, self.view_height))

    def focus_get(self) -> None:
        self.focus = True
        self.display_caret = True
        self.caret_timer.reset_timer()
        pygame.key.start_text_input()

    def focus_lose(self) -> None:
        self.focus = False
        self.display_caret = False
        pygame.key.stop_text_input()
        if self.select_start != -1 and self.select_end != -1:
            self.select_start = -1
            self.select_end = -1
            self.select_rect = None

    def mouse_collision(self, mouse_obj: Mouse.Cursor) -> bool:
        return pygame.Rect(0, 0, self.view_width, self.view_height).collidepoint(*mouse_obj.get_pos())

    def move_view_by_caret(self, direction: Literal["l", "r"]) -> None:
        if direction == "l":
            width = self.calc_text_size(self.text[:self.caret_index])[0]
            self.x = -(width - self.view_width + self.scroll_padding)
        elif direction == "r":
            width = self.calc_text_size(self.text[:self.caret_index])[0]
            if self.caret_index == 0:
                self.x = 0
            else:
                self.x = -width + self.scroll_padding
        self.rect = pygame.Rect(self.x, self.y, *self.surface.get_size())

    def move_view_by_pos(self, direction: Literal["l", "r"]) -> None:
        if direction == "l":
            if self.calc_text_size(self.text)[0] <= self.view_width - self.scroll_padding:
                self.x = 0
                return None
            self.x -= self.scroll_amount * self.scroll_time
            if self.x < -(self.calc_text_size(self.text)[0] - self.view_width + self.scroll_padding):
                self.x = -(self.calc_text_size(self.text)[0] - self.view_width + self.scroll_padding)
        elif direction == "r":
            self.x += self.scroll_amount * self.scroll_time
            if self.x > 0:
                self.x = 0
        self.rect = pygame.Rect(self.x, self.y, *self.surface.get_size())

    def get_surface(self) -> pygame.Surface:
        return self.surface

    def get_view_rect(self) -> pygame.Rect:
        return pygame.Rect(abs(self.x), self.y, self.view_width, self.view_height)

    def get_text(self) -> str:
        return self.text


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
            if isinstance(widget_obj, Entry):
                self.scroll_event()

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

    def scroll_event(self) -> None:  # Should be called on scroll.
        for widget in self.child_widgets.values():
            if isinstance(widget, Entry):
                widget.update_real_pos((self.x + widget.get_pos()[0], self.y + widget.get_pos()[1]))

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
