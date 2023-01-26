from typing import *
import pygame


class Cursor(pygame.sprite.Sprite):
    # Cursor class used for Mask collision detection between the mouse cursor and a Sprite group.
    def __init__(self):
        super().__init__()
        # Stores the button state of each mouse button, in the form of [button1, button2, button3]
        # [left mouse button, mouse wheel button, right mouse button, scroll up, scroll down]
        self.buttons = [False] * 5
        # Used to determine if the mouse hover event should continue to pass down to the next lower z-level
        self.z_index = 1
        self.x = 0
        self.y = 0
        self.width = 1
        self.height = 1
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.mask = pygame.mask.Mask(size=(self.width, self.height), fill=True)

    def copy(self):
        new_cur = Cursor()
        for index, button in enumerate(self.buttons, start=1):
            new_cur.set_button_state(index, button)
        new_cur.z_index = self.z_index
        new_cur.set_pos(self.x, self.y)
        return new_cur

    def reset_z_index(self) -> None:
        self.z_index = 1

    def increment_z_index(self) -> None:
        self.z_index += 1

    def get_z_index(self) -> int:
        return self.z_index

    def set_pos(self, new_x: int, new_y: int) -> None:
        self.x = new_x
        self.y = new_y
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def get_pos(self) -> Tuple[int, int]:
        return self.x, self.y

    def set_button_state(self, button_number: int, state: bool) -> None:
        """
        Sets the state of a mouse button.

        e.g. To click mouse button 1: set_button_state(1, True)
        """
        self.buttons[button_number - 1] = state

    def get_button_state(self, button_number: int) -> bool:
        return self.buttons[button_number - 1]
