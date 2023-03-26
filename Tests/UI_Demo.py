"""
This file demonstrates usage of the GUI toolkit in the 'Widgets.py' module. You can also have a bit of fun playing with
the UI of this script when run.
"""
from typing import *
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
        self.resolution = (513, 450)
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
        self.font = pygame.font.Font(resolve_path("./Fonts/Arial/normal.ttf"), 28)
        self.mandarin_font = pygame.font.Font(resolve_path("./Fonts/JhengHei/normal.ttc"), 16)
        self.mouse = Mouse.Cursor()
        self.clock = pygame.time.Clock()
        self.transition = None
        self.transition_ready = False
        self.popup_window: Optional[ChildWindow] = None
        self.counter1 = 0
        self.counter2 = 0
        self.fps = 60
        self.game_run = True
        self.key_events = []
        # region Initialize Frame
        self.content_frame = Widgets.Frame(0, 0, self.resolution[0], self.resolution[1], 20, 2, "canvas1")
        text = self.font.render("Give her up", True, BLACK)
        btn_surf = pygame.Surface((text.get_size()[0] + 30, text.get_size()[1] + 20))
        btn_surf.fill((215, 215, 215))
        btn_surf.blit(text, self.center_widget(btn_surf.get_size(), text.get_size()))
        self.content_frame.add_widget(Widgets.AnimatedSurface(40, 20, btn_surf, self.add_counter1))
        self.content_frame.add_widget(Widgets.Button(270, 20, 190, 55, 1, BLACK, ORANGE, self.font, "Let her down",
                                                     self.add_counter2, "button1"))
        self.checkbox1 = Widgets.Checkbox(12, 90, "Run around and desert her?", BLACK, ORANGE, 230, self.font, 20, 1,
                                          "checkbox1")
        self.content_frame.add_widget(self.checkbox1)
        self.checkbox2 = Widgets.Checkbox(252, 90, "Together forever and never to part?", BLACK, ORANGE, 230, self.font,
                                          20, 1, "checkbox2")
        self.content_frame.add_widget(self.checkbox2)
        self.radio_group = Widgets.RadioGroup()
        self.radio_group.create_radio_button(12, 300, "Make her cry", BLACK, ORANGE, 150, self.font, 20, 1, "radio1")
        self.radio_group.create_radio_button(172, 300, "Say goodbye", BLACK, ORANGE, 150, self.font, 20, 1, "radio2")
        self.radio_group.create_radio_button(332, 300, "Tell a lie and hurt her", BLACK, ORANGE, 150, self.font, 20, 1,
                                             "radio3")
        self.content_frame.add_widget(self.radio_group)
        self.slider = Widgets.Slider(30, 620, 25, BLACK, 400, 5, (250, 50, 50), (0, 255, 0), 10, 30, (0, 130, 205),
                                     (155, 205, 0), self.mandarin_font, 1, 100, 7)
        self.content_frame.add_widget(self.slider)
        self.entry1 = Widgets.Entry(10, 670, 150, 30, 4, self.mandarin_font, BLACK, "entry1")
        self.content_frame.add_widget(self.entry1)
        self.entry2 = Widgets.Entry(170, 670, 150, 30, 4, self.mandarin_font, BLACK, "entry2")
        self.content_frame.add_widget(self.entry2)
        self.entry3 = Widgets.Entry(330, 670, 150, 30, 4, self.mandarin_font, BLACK, "entry3")
        self.content_frame.add_widget(self.entry3)
        self.content_frame.add_widget(Widgets.Button(180, 712, 150, 55, 1, BLACK, ORANGE, self.font, "Submit",
                                                     self.submit, "button2"))
        self.content_frame.add_widget(Widgets.Spinner(50, 790, 100, 15, 90, 250, (205, 205, 205), (26, 134, 219)))
        self.content_frame.add_widget(Widgets.Button(193, 815, 260, 55, 1, BLACK, ORANGE, self.font, "Test Transition",
                                                     self.init_transition, "button3"))
        self.content_frame.add_widget(Widgets.Button(140, 940, 230, 55, 1, BLACK, ORANGE, self.font, "Open Window",
                                                     self.spawn_window, "button4"))
        self.content_frame.add_widget(Widgets.ScrollBar())
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
            if self.transition is None and self.popup_window is None:
                # Only allow mouse events to be passed to the widget-group if there aren't any other objects over it.
                self.mouse.increment_z_index()
            elif self.transition is not None:
                return_code = self.transition.update()
                if return_code == 2:
                    self.transition = None
            elif self.popup_window is not None:
                return_code = self.popup_window.update(self.mouse, self.key_events)
                if return_code:
                    self.popup_window = None
            self.content_frame.update(self.mouse, self.key_events)
            self.display.fill(BLUE)
            self.display.blit(self.content_frame.image, self.content_frame.rect)
            if self.transition is not None:
                if self.transition_ready:
                    self.display.blit(self.transition.image, self.transition.rect)
                else:
                    self.transition_ready = True
            elif self.popup_window is not None:
                self.popup_window.draw()
            pygame.display.flip()
        pygame.quit()

    @staticmethod
    def center_widget(container_size: Tuple[int, int], content_size: Tuple[int, int]) -> Tuple[float, float]:
        return container_size[0] / 2 - content_size[0] / 2, container_size[1] / 2 - content_size[1] / 2

    def add_counter1(self) -> None:
        self.counter1 += 1

    def add_counter2(self) -> None:
        self.counter2 += 1

    def init_transition(self) -> None:
        if self.transition is None:
            self.transition = Widgets.SceneTransition(self.resolution[0], self.resolution[1], 400)
            self.transition_ready = False

    def spawn_window(self) -> None:
        self.popup_window = ChildWindow(self.display, self.resolution, (300, 200), 15, 15, 10, 4, 0.05, 200, 1)

    def submit(self) -> None:
        print("{}\nLove Stats:\nYou gave her up {} times.\nYou let her down {} times.\n"
              "You {} run around and desert her.\nYou {} stay with her forever and not part with her.\n"
              "You chose to {}.\nThe three messages you left her are: '{}', '{}', '{}'.\n"
              "You're {}% in love with Miss Rick."
              .format("-" * 35,
                      self.counter1,
                      self.counter2,
                      "DID" if self.checkbox1.get_data() else "DIDN'T",
                      "DID" if self.checkbox2.get_data() else "DIDN'T",
                      ("make her cry", "say goodbye", "tell a lie and hurt her")[self.radio_group.get_selected()],
                      self.entry1.get_entry_content(),
                      self.entry2.get_entry_content(),
                      self.entry3.get_entry_content(),
                      self.slider.get_slider_value()))
        self.counter1 = 0
        self.counter2 = 0


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
                 z_index: int):
        """A child window that displays several hundred lines of placeholder text in a scrollable frame. This is an
        example of how to use the window widget."""
        self.frame_size = (window_size[0] - border_radius * 2,
                           window_size[1] - border_radius * 2 - button_length - button_padding)
        self.window_size = window_size
        self.accumulated_height = 0
        self.w_id_counter = 1
        self.word_wrap_width = word_wrap_width
        self.vertical_padding = 20
        self.font = pygame.font.Font(resolve_path("./Fonts/JhengHei/normal.ttc"), 18)
        # region Initialize Frame
        # Note that the position of the frame isn't important, since it will be handled by the window it's displayed in.
        self.content_frame = Widgets.Frame(-1, -1, self.frame_size[0], self.frame_size[1], 20, z_index)
        for s in ("Hello, world!\n您好，世界！",
                  "The quick brown fox jumps over the lazy dog.\n敏捷地棕色狐狸跳過了懶惰地狗。",
                  "Lorem ipsum dolor sit amet.\n微風迎客，軟語伴茶。"):
            self.create_label(s)
        for i in range(20, -1, -1):
            self.create_label("{} on the wall.\n{}在牆壁上。".format(*self.beer_string(i)))
            self.create_label("{}.\n{}。".format(*self.beer_string(i)))
            if i > 0:
                self.create_label("Take one down, pass it around.\n拿一瓶下來，分給大家喝。")
        self.content_frame.add_widget(Widgets.ScrollBar())
        # endregion
        self.window = Widgets.Window(resolution[0] / 2 - window_size[0] / 2, resolution[1],
                                     resolution[1] / 2 - window_size[1] / 2, GREEN, 100, RED, GREY2, border_radius,
                                     button_length, button_padding, button_thickness, animation_speed,
                                     self.content_frame, surface, z_index)

    @staticmethod
    def beer_string(beer_number: int) -> Tuple[str, str]:
        if beer_number > 1:
            return f"{beer_number} bottles of beer", f"{beer_number}瓶酒"
        elif beer_number == 1:
            return "One bottle of beer", "一瓶酒"
        else:
            return "No more bottles of beer", "已經沒有任何酒"

    def create_label(self, string: str) -> None:
        label = Widgets.Label(self.frame_size[0] / 2 - self.word_wrap_width / 2, self.accumulated_height, string, BLACK,
                              self.word_wrap_width, self.font, f"!label{self.w_id_counter}")
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
    if pygame.version.vernum >= (2, 0, 1):
        MainProc()
    else:
        print("This game requires Pygame version 2.0.1 or higher to run. Consider updating your version of Pygame "
              "with the command: 'python -m pip install --upgrade pygame'")
