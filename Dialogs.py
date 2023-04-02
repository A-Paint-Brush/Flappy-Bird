from collections import namedtuple
from Global import *
import os
import pygame
import Mouse
import Widgets


class Settings:
    def __init__(self,
                 surface: pygame.Surface,
                 resolution: Tuple[int, int],
                 window_size: Tuple[int, int],
                 border_radius: int,
                 button_length: int,
                 button_padding: int,
                 button_thickness: int,
                 animation_speed: Union[int, float],
                 max_widget_width: int,
                 current_volume: int,
                 z_index: int = 1):
        self.small_font = pygame.font.Font(os.path.normpath("Fonts/Arial/normal.ttf"), 25)
        self.large_font = pygame.font.Font(os.path.normpath("Fonts/Arial/normal.ttf"), 35)
        self.frame_size = (window_size[0] - border_radius * 2,
                           window_size[1] - border_radius * 2 - button_length - button_padding)
        self.window_size = window_size
        self.scrollbar_width = 20
        self.max_widget_width = max_widget_width - border_radius * 2 - self.scrollbar_width
        self.content_width = self.frame_size[0] - self.scrollbar_width
        self.label_id = 1
        self.accumulated_y = 0
        v_pad = 20
        # region Initialize Frame
        self.content_frame = Widgets.Frame(0, 0, self.frame_size[0], self.frame_size[1], 20, z_index)
        self.add_label("Game Settings", 2 * v_pad)
        self.add_label("Volume", v_pad)
        max_value = 100
        thumb_width = 13
        text_size = self.large_font.size(str(max_value))
        text_padding = 10
        max_text_width = 31 * (text_size[0] / text_size[1])
        widget_size = namedtuple("slider_args", ["text_height", "line_length", "thumb_width", "thumb_height", "font",
                                                 "max_value",
                                                 "text_padding"])(text_height=31,
                                                                  line_length=round(self.max_widget_width
                                                                                    - max_text_width - text_padding
                                                                                    - thumb_width),
                                                                  thumb_width=thumb_width,
                                                                  thumb_height=38, font=self.large_font, max_value=100,
                                                                  text_padding=text_padding)
        widget_data = Widgets.Slider.calc_size(*widget_size)
        self.slider = Widgets.Slider(round(self.content_width / 2 - widget_data[0] / 2), self.accumulated_y,
                                     widget_size.text_height, BLACK, widget_size.line_length, 5, (250, 50, 50),
                                     (0, 255, 0), widget_size.thumb_width, widget_size.thumb_height, (0, 130, 205),
                                     (155, 205, 0), widget_size.font, 0, widget_size.max_value)
        self.slider.set_slider_value(current_volume)
        self.content_frame.add_widget(self.slider)
        self.accumulated_y += widget_size[1] + v_pad
        self.content_frame.add_widget(Widgets.ScrollBar(width=self.scrollbar_width))
        # endregion
        self.window = Widgets.Window(resolution[0] / 2 - window_size[0] / 2, resolution[1],
                                     resolution[1] / 2 - window_size[1] / 2, GREEN, 100, RED, GREY6, border_radius,
                                     button_length, button_padding, button_thickness, animation_speed,
                                     self.content_frame, surface, z_index)

    def add_label(self, text: str, padding: int) -> None:
        label = Widgets.Label(self.content_width / 2 - self.max_widget_width / 2, self.accumulated_y, text, BLACK,
                              self.max_widget_width, self.small_font, widget_name="!label{}".format(self.label_id))
        self.content_frame.add_widget(label)
        self.accumulated_y += label.rect.height + padding
        self.label_id += 1

    def update(self,
               mouse_obj: Mouse.Cursor,
               keyboard_events: List[pygame.event.Event]) -> bool:
        return self.window.update(mouse_obj, keyboard_events)

    def draw(self) -> None:
        self.window.draw()

    def get_volume(self) -> int:
        return self.slider.get_slider_value()
