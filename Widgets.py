from os.path import normpath
from Global import *
import pygame
import Time


class Button(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, font, text, identifier):
        super().__init__()
        self.id = identifier  # Stores the index of the current class instance in the button list
        self.font = font
        self.label_text = text
        # The x and y position without resize offset.
        self.real_x = x
        self.real_y = y
        self.x = self.real_x
        self.y = self.real_y
        # region Setup
        self.original_width = width
        self.original_height = height
        self.original_surface = pygame.Surface(self.original_width, self.original_height)
        self.original_surface.fill(WHITE)
        self.original_surface.set_colorkey(WHITE)
        draw_button(self.original_surface,
                    self.x,
                    self.y,
                    self.original_width,
                    self.original_height,
                    self.font,
                    self.label_text,
                    ORANGE)
        self.image = self.original_surface.copy()
        # endregion
        self.new_width = self.original_width
        self.new_height = self.original_height
        self.max_width = self.original_width + 30
        self.min_width = self.original_width
        self.reducing_fraction = 0.92
        self.aspect_ratio = self.original_height / self.original_width
        self.rect = pygame.Rect(self.x, self.y, self.original_width, self.original_height)
        self.mask = pygame.mask.from_surface(self.image)
        self.mode = "idle"  # Literal["small", "large", "dilating", "shrinking"]
        self.delta_timer = Time.Time()

    def set_size(self, new_size):
        self.new_width = new_size
        self.new_height = self.new_width * self.aspect_ratio
        offset_x = round((self.original_width - self.new_width) / 2)
        offset_y = round((self.original_height - self.new_height) / 2)
        self.x = self.real_x + offset_x
        self.y = self.real_y + offset_y
        self.image = pygame.Surface(self.new_width, self.new_height)
        pygame.transform.scale(self.original_surface, (self.new_width, self.new_height), dest_surface=self.image)
        self.rect = pygame.Rect(self.x, self.y, self.new_width, self.new_height)
        self.mask = pygame.mask.from_surface(self.image)

    def calc_physics(self, delta_time, mode):
        return (self.max_width - self.new_width if mode == "dilating" else self.new_width - self.min_width) * (self.reducing_fraction / (delta_time if delta_time > 1 else 1))

    def change_size(self, direction):
        """
        Updates button size and returns True if minimum size has been reached.
        """
        if self.mode == "small" and direction == "decrease":
            return False
        if self.mode == "large" and direction == "increase":
            return False
        skip_delta_time = False
        if self.mode == "small" and direction == "increase":
            skip_delta_time = True
            self.mode = "dilating"
        elif self.mode == "large" and direction == "decrease":
            skip_delta_time = True
            self.mode = "shrinking"
        temp_width = self.calc_physics(1 if skip_delta_time else self.delta_timer.get_time(), self.mode)
        self.delta_timer.reset_timer()
        self.set_size(temp_width)
        if direction == "increase" and temp_width == self.max_width:
            self.mode = "large"
            return False
        elif direction == "decrease" and temp_width == self.min_width:
            self.mode = "small"
            return True

    def get_id(self):
        return self.id


class ButtonList(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.font = pygame.font.Font(normpath("./Fonts/Arial.ttf"), 13)
        self.max_button_size = [0, 0]  # Format: [max_width, max_height]
        self.padding = 20  # Without any padding, the button will be only large enough to fit its text
        self.unmapped_buttons = []  # Holds the data that hasn't been passed to a class initializer yet
        self.button_list = []  # Holds the object instances of all buttons
        self.callback_funcs = []  # Holds the references to the functions that each button has to call when clicked
        self.pending_shrink = []  # Holds button object instances that has been dilated

    def create_button(self, position, text, callback):
        self.unmapped_buttons.append((position, text, callback))
        est_size = estimate_button_size(self.font, self.padding, text)
        for index in range(2):
            # If the current button is larger than the max button size stored so far, update max button size.
            if est_size[index] > self.max_button_size[index]:
                self.max_button_size[index] = est_size[index]

    def pack_buttons(self):
        for index, data in enumerate(self.unmapped_buttons):
            temp_object = Button(*data[0], *self.max_button_size, self.font, data[1], index)
            self.button_list.append(temp_object)
            self.callback_funcs.append(data[2])
        self.unmapped_buttons.clear()
        self.add(self.button_list)

    def update(self, mouse_object, mouse_down):  # This method should be called every frame
        """
        Returns the ID of the button that the mouse cursor is hovering over of
        """
        # 'hovered_button' returns the class object representing the button that the mouse is hovering over of.
        hovered_button = pygame.sprite.spritecollideany(mouse_object, self, collided=collide_function)
        excepted_button = None
        if hovered_button is not None:
            hovered_button.change_size("increase")
            excepted_button = hovered_button.get_id()
            if not hovered_button.get_id() in self.pending_shrink:
                self.pending_shrink.append(hovered_button.get_id())
        for index, button in enumerate(self.pending_shrink):
            if button.get_id() == excepted_button:
                continue
            else:
                shrunk = button.change_size("decrease")
                if shrunk:
                    self.pending_shrink[index] = None
        self.pending_shrink[:] = [button for button in self.pending_shrink if button is not None]
        if mouse_down and (hovered_button is not None):
            self.callback_funcs[hovered_button.get_id()]()
