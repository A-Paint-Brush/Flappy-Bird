"""
This file demonstrates usage of the GUI toolkit in the 'Widgets.py' module. You can also have a bit of fun playing with
the UI of this script when run.
"""
from typing import *
from functools import partial
from collections import namedtuple
import os.path
import sys
import pygame
import pygame.colordict
WHITE = (255, 255, 255)
RED = (255, 0, 0)
ORANGE = (255, 160, 20)
GREEN = pygame.colordict.THECOLORS["darkolivegreen1"]
BLUE = pygame.colordict.THECOLORS["lightskyblue1"]
GREY1 = (240, 240, 240)
GREY2 = (96, 96, 96)
BLACK = (0, 0, 0)


def get_root_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(os.path.normpath(__file__)), ".."))


def resolve_path(rel_path: str) -> str:
    return os.path.join(get_root_dir(), os.path.normpath(rel_path))


class MainProc:
    def __init__(self):
        """The mainloop of this program."""
        pygame.init()
        self.resolution = (641, 563)  # Og size: (513, 450)
        self.listen_events = (pygame.QUIT,
                              pygame.WINDOWFOCUSLOST,
                              pygame.WINDOWENTER,
                              pygame.WINDOWLEAVE,
                              pygame.MOUSEBUTTONDOWN,
                              pygame.MOUSEBUTTONUP,
                              pygame.MOUSEWHEEL,
                              pygame.KEYDOWN,
                              pygame.KEYUP,
                              pygame.TEXTINPUT,
                              pygame.TEXTEDITING)
        pygame.display.set_caption("GUI Toolkit")
        self.display = pygame.display.set_mode(self.resolution, pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.event.set_blocked(None)
        pygame.event.set_allowed(self.listen_events)
        pygame.key.stop_text_input()  # Ensure IME input is off when the window first opens.
        self.font = pygame.font.SysFont("arial", 35)
        self.mandarin_font = pygame.font.SysFont(("microsoftjhenghei", "notosanscjktc", "notofontscjk"), 20)
        self.mouse = Mouse.Cursor()
        self.clock = pygame.time.Clock()
        self.special_widgets: Dict[str, Union[tuple, Widgets.SceneTransition, ChildWindow]] = {}
        self.fps = 60
        self.game_run = True
        self.key_events = []
        # region Initialize Frame
        scrollbar_width = 20
        content_width = self.resolution[0] - scrollbar_width
        margin = 10
        accumulated_y = margin
        self.counters = [0, 0]
        self.checkboxes = []
        self.entries = []
        self.content_frame = Widgets.Frame(0, 0, self.resolution[0], self.resolution[1], 20, z_index=2)
        widget_size = [(210, 60), (238, 69)]
        widget_data = [list(Widgets.Button.calc_size(0, *widget_size[0])),
                       list(Widgets.Button.calc_size(0, *widget_size[1]))]
        for w in range(len(widget_data)):
            widget_data[w][0] = abs(widget_data[w][0])
            widget_data[w][1] += widget_data[w][0]
        text = self.font.render("Give her up", True, BLACK)
        text = Global.resize_surf(text, (widget_size[0][0] - 30, widget_size[0][1] - 10))
        btn_surf = pygame.Surface(widget_size[0])
        btn_surf.fill((215, 215, 215))
        btn_surf.blit(text, (btn_surf.get_width() / 2 - text.get_width() / 2,
                             btn_surf.get_height() / 2 - text.get_height() / 2))
        self.content_frame.add_widget(
            Widgets.AnimatedSurface(content_width / 4 - btn_surf.get_width() / 2,
                                    accumulated_y + widget_data[0][0] + (0 if widget_data[0][1] > widget_data[1][1]
                                                                         else (widget_data[1][1] / 2
                                                                               - widget_data[0][1] / 2)),
                                    btn_surf, partial(self.increment_counter, 0)))
        self.content_frame.add_widget(
            Widgets.Button((3 * content_width - 2 * widget_size[1][0]) / 4,
                           accumulated_y + widget_data[1][0] + (0 if widget_data[1][1] > widget_data[0][1]
                                                                else (widget_data[0][1] / 2 - widget_data[1][1] / 2)),
                           widget_size[1][0], widget_size[1][1], 1, BLACK, ORANGE, self.font, "Let her down",
                           partial(self.increment_counter, 1), widget_name="button1"))
        accumulated_y += max(w[1] for w in widget_data) + margin
        widget_size = (content_width - margin) / 2
        for index, text in enumerate(("Run around and desert her?", "Together forever and never to part?")):
            self.checkboxes.append(Widgets.Checkbox(margin + widget_size * index, accumulated_y, text, 44, 13, BLACK,
                                                    ORANGE, round(widget_size - margin), self.font, 20, 1,
                                                    widget_name="checkbox{}".format(index + 1)))
            self.content_frame.add_widget(self.checkboxes[-1])
        accumulated_y += max(w.rect.height for w in self.checkboxes) + margin
        widget_size = (content_width - margin) / 3
        self.radio_group = Widgets.RadioGroup()
        for index, text in enumerate(("Make her cry", "Say goodbye", "Tell a lie and hurt her")):
            self.radio_group.create_radio_button(margin + widget_size * index, accumulated_y, text, 44, 13, 15, BLACK,
                                                 ORANGE, round(widget_size - margin), self.font, 20, 1,
                                                 widget_name="radio{}".format(index + 1))
        self.content_frame.add_widget(self.radio_group)
        accumulated_y += max(w.rect.height for w in self.radio_group.get_children()) + margin
        widget_size = namedtuple("slider_args", ["text_height", "line_length", "thumb_width", "thumb_height", "font",
                                                 "max_value"])(text_height=31, line_length=500, thumb_width=13,
                                                               thumb_height=38, font=self.font, max_value=100)
        widget_data = Widgets.Slider.calc_size(*widget_size)
        self.slider = Widgets.Slider(round(content_width / 2 - widget_data[0] / 2), accumulated_y,
                                     widget_size.text_height, BLACK, widget_size.line_length, 5, (250, 50, 50),
                                     (0, 255, 0), widget_size.thumb_width, widget_size.thumb_height, (0, 130, 205),
                                     (155, 205, 0), widget_size.font, 1, widget_size.max_value, mark_height=7)
        self.content_frame.add_widget(self.slider)
        accumulated_y += widget_data[1] + margin
        widget_size = (189, 38)
        for index, position in enumerate((17.5, 50, 82.5)):
            self.entries.append(Widgets.Entry(content_width * (position / 100) - widget_size[0] / 2, accumulated_y,
                                              widget_size[0], widget_size[1], 4, self.mandarin_font, BLACK,
                                              widget_name="entry{}".format(index + 1)))
            self.content_frame.add_widget(self.entries[-1])
        accumulated_y += widget_size[1] + margin
        widget_size = (188, 69)
        widget_data = list(Widgets.Button.calc_size(0, *widget_size))
        widget_data[1] += abs(widget_data[0])
        self.content_frame.add_widget(Widgets.Button(content_width / 2 - widget_size[0] / 2,
                                                     accumulated_y + abs(widget_data[0]), widget_size[0],
                                                     widget_size[1], 1, BLACK, ORANGE, self.font, "Submit",
                                                     self.submit, widget_name="button2"))
        accumulated_y += widget_data[1] + margin
        widget_size = [(125, 125), (216, 69)]
        widget_data = [list(Widgets.Button.calc_size(0, *widget_size[1]))]
        widget_data[0][0] = abs(widget_data[0][0])
        widget_data[0][1] += widget_data[0][0]
        self.content_frame.add_widget(Widgets.Spinner(
            content_width / 4 - widget_size[0][0] / 2,
            accumulated_y + (0 if widget_size[0][1] > widget_data[0][1]
                             else (widget_data[0][1] / 2 - widget_size[0][1] / 2)),
            widget_size[0][1], 19, 90, 250, (205, 205, 205), (26, 134, 219)))
        self.content_frame.add_widget(
            Widgets.Button((3 * content_width - 2 * widget_size[1][0]) / 4,
                           accumulated_y + widget_data[0][0] + (0 if widget_data[0][1] > widget_size[0][1]
                                                                else (widget_size[0][1] / 2 - widget_data[0][1] / 2)),
                           widget_size[1][0], widget_size[1][1], 1, BLACK, ORANGE, self.font, "Transition",
                           self.start_transition, widget_name="button3"))
        accumulated_y += max((widget_size[0][1], widget_data[0][1])) + margin
        widget_size = (288, 69)
        widget_data = [list(Widgets.Button.calc_size(0, *widget_size))]
        widget_data[0][1] += abs(widget_data[0][0])
        self.content_frame.add_widget(Widgets.Button(content_width / 2 - widget_size[0] / 2,
                                                     accumulated_y + abs(widget_data[0][0]), widget_size[0],
                                                     widget_size[1], 1, BLACK, ORANGE, self.font, "Open Window",
                                                     self.spawn_window, widget_name="button4"))
        self.content_frame.add_widget(Widgets.ScrollBar(width=scrollbar_width))
        # endregion
        while self.game_run:
            self.clock.tick(self.fps)
            self.key_events.clear()
            self.mouse.reset_scroll()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_run = False
                elif event.type == pygame.WINDOWENTER:
                    self.mouse.mouse_enter()
                elif event.type == pygame.WINDOWLEAVE:
                    self.mouse.mouse_leave()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.mouse.set_button_state(event.button, True)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.mouse.set_button_state(event.button, False)
                elif event.type == pygame.MOUSEWHEEL:
                    self.mouse.push_scroll(event.y)
                elif event.type in (pygame.WINDOWFOCUSLOST, pygame.KEYDOWN, pygame.KEYUP, pygame.TEXTINPUT,
                                    pygame.TEXTEDITING):
                    self.key_events.append(event)
            self.mouse.set_pos(*pygame.mouse.get_pos())
            self.mouse.reset_z_index()
            if "transition" in self.special_widgets and isinstance(self.special_widgets["transition"], tuple):
                self.special_widgets["transition"] = Widgets.SceneTransition(*self.special_widgets["transition"])
            elif "window" in self.special_widgets and isinstance(self.special_widgets["window"], tuple):
                self.special_widgets["window"] = ChildWindow(*self.special_widgets["window"])
            if "transition" in self.special_widgets and isinstance(self.special_widgets["transition"],
                                                                   Widgets.SceneTransition):
                return_code = self.special_widgets["transition"].update()
                if return_code == 2:
                    self.special_widgets.pop("transition")
            elif "window" in self.special_widgets and isinstance(self.special_widgets["window"], ChildWindow):
                return_code = self.special_widgets["window"].update(self.mouse, self.key_events)
                if return_code:
                    self.special_widgets.pop("window")
            else:
                # Only allow mouse events to be passed to the widget-group if there aren't any other objects over it.
                self.mouse.increment_z_index()
            self.content_frame.update(self.mouse, self.key_events)
            self.display.fill(BLUE)
            self.display.blit(self.content_frame.image, self.content_frame.rect)
            if "transition" in self.special_widgets and isinstance(self.special_widgets["transition"],
                                                                   Widgets.SceneTransition):
                self.display.blit(self.special_widgets["transition"].image, self.special_widgets["transition"].rect)
            elif "window" in self.special_widgets and isinstance(self.special_widgets["window"], ChildWindow):
                self.special_widgets["window"].draw()
            pygame.display.flip()
        pygame.quit()

    def increment_counter(self, index: int) -> None:
        self.counters[index] += 1

    def start_transition(self) -> None:
        if "transition" not in self.special_widgets:
            self.special_widgets["transition"] = (self.resolution[0], self.resolution[1], 400)

    def spawn_window(self) -> None:
        if "window" not in self.special_widgets:
            widget_size = (375, 250)
            padding = 12
            self.special_widgets["window"] = (self.display, self.resolution, widget_size, 19, 19, 10, 4, 0.05,
                                              widget_size[0] - 2 * padding)

    def submit(self) -> None:
        print("{}\nLove Stats:\nYou gave her up {} time(s).\nYou let her down {} time(s).\n"
              "You {} run around and desert her.\nYou {} stay with her forever and not part with her.\n"
              "You chose to {}.\nThe three messages you left her are: '{}', '{}', '{}'.\n"
              "You're {}% in love with Miss Rick."
              .format("-" * 35, *[i for i in self.counters],
                      *["DID" if checkbox.get_data() else "DIDN'T" for checkbox in self.checkboxes],
                      ("make her cry", "say goodbye", "tell a lie and hurt her")[self.radio_group.get_selected()],
                      *[entry.get_entry_content() for entry in self.entries], self.slider.get_slider_value()))


class ChildWindow:
    def __init__(self,
                 surface: pygame.Surface,
                 resolution: Tuple[int, int],
                 window_size: Tuple[int, int],
                 border_radius: int,
                 button_length: int,
                 button_padding: int,
                 button_thickness: int,
                 animation_speed: Union[int, float],
                 word_wrap_width: int,
                 scrollbar_width: int = 20,
                 z_index: int = 1):
        """A child window that displays lots of text in a scrollable frame. This is an example of how to use the window
        widget."""
        self.frame_size = (window_size[0] - border_radius * 2,
                           window_size[1] - border_radius * 2 - button_length - button_padding)
        self.scrollbar_width = scrollbar_width
        self.content_width = self.frame_size[0] - self.scrollbar_width
        self.window_size = window_size
        self.accumulated_height = 0
        self.w_id_counter = 1
        self.word_wrap_width = word_wrap_width - border_radius * 2 - self.scrollbar_width
        self.vertical_padding = 20
        self.font = pygame.font.SysFont(("microsoftjhenghei", "notosanscjktc", "notofontscjk"), 23)
        # region Initialize Frame
        # Note that the position of the frame isn't important, since it will be handled by the window it's displayed in.
        self.content_frame = Widgets.Frame(0, 0, self.frame_size[0], self.frame_size[1], 20, z_index=z_index)
        for s in ("Hello, world!\n您好，世界！",
                  "The quick brown fox jumps over the lazy dog.\n敏捷地棕色狐狸跳過了懶惰地狗。",
                  "Lorem ipsum dolor sit amet.\n微風迎客，軟語伴茶。"):
            self.create_label(s)
        for i in range(20, -1, -1):
            self.create_label("{} on the wall.\n{}在牆壁上。".format(*self.beer_string(i)))
            self.create_label("{}.\n{}。".format(*self.beer_string(i)))
            if i > 0:
                self.create_label("Take one down, pass it around.\n拿一瓶下來，分給大家喝。")
        self.content_frame.add_widget(Widgets.ScrollBar(width=self.scrollbar_width))
        # endregion
        self.window = Widgets.Window(resolution[0] / 2 - window_size[0] / 2, resolution[1],
                                     resolution[1] / 2 - window_size[1] / 2, GREEN, 100, RED, GREY2, border_radius,
                                     button_length, button_padding, button_thickness, animation_speed,
                                     self.content_frame, surface, z_index)

    @staticmethod
    def beer_string(beer_number: int) -> Tuple[str, ...]:
        if beer_number > 1:
            return tuple("{n} bottles of beer;{n}瓶酒".format(n=beer_number).split(";"))
        elif beer_number == 1:
            return "One bottle of beer", "一瓶酒"
        else:
            return "No more bottles of beer", "已經沒有任何酒"

    def create_label(self, string: str) -> None:
        label = Widgets.Label(self.content_width / 2 - self.word_wrap_width / 2, self.accumulated_height, string, BLACK,
                              self.word_wrap_width, self.font, widget_name="!label{}".format(self.w_id_counter))
        self.accumulated_height += label.rect.height + self.vertical_padding
        self.content_frame.add_widget(label)
        self.w_id_counter += 1

    def update(self, mouse_obj, keyboard_events: list[pygame.event.Event]) -> bool:
        return self.window.update(mouse_obj, keyboard_events)

    def draw(self) -> None:
        self.window.draw()


if __name__ == "__main__":
    sys.path.extend((get_root_dir(),))
    import Widgets
    import Mouse
    import Global
    if pygame.version.vernum >= (2, 0, 1):
        Global.configure_dpi()
        MainProc()
    else:
        print("This game requires Pygame version 2.0.1 or higher to run. Consider updating your version of Pygame "
              "with the command: 'python -m pip install --upgrade pygame'")
