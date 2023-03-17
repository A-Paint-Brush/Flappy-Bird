from typing import *
import os.path
import sys
import pygame

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREY = (240, 240, 240)
ORANGE = (255, 160, 20)
BLUE = pygame.Color("lightskyblue1")


def get_root_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(os.path.normpath(__file__)), ".."))


def resolve_path(rel_path: str) -> str:
    return os.path.join(get_root_dir(), os.path.normpath(rel_path))


def center_widget(container_size: Tuple[int, int], content_size: Tuple[int, int]) -> Tuple[float, float]:
    return container_size[0] / 2 - content_size[0] / 2, container_size[1] / 2 - content_size[1] / 2


class Window:
    def __init__(self):
        pygame.init()
        self.resolution = (513, 450)  # Fit content: (513, 640)
        self.fps = 60
        self.game_run = True
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
        pygame.key.stop_text_input()
        self.clock = pygame.time.Clock()
        self.widget_canvas = Widgets.WidgetCanvas(0, 0, self.resolution[0], self.resolution[1], 20, 1, "canvas1")
        self.widgets = Widgets.WidgetGroup()
        self.widgets.add_widget_canvas(self.widget_canvas)
        self.mouse = Mouse.Cursor()
        self.key_events = []
        self.font = pygame.font.Font(resolve_path("./Fonts/Arial/normal.ttf"), 28)
        self.mandarin_font = pygame.font.Font(resolve_path("./Fonts/JhengHei/normal.ttc"), 16)
        self.counter1 = 0
        self.counter2 = 0
        # region Initialize Widgets
        text = self.font.render("Give her up", True, BLACK)
        btn_surf = pygame.Surface((text.get_size()[0] + 30, text.get_size()[1] + 20))
        btn_surf.fill((215, 215, 215))
        btn_surf.blit(text, center_widget(btn_surf.get_size(), text.get_size()))
        self.widget_canvas.add_widget(Widgets.AnimatedSurface(40,
                                                              20,
                                                              btn_surf,
                                                              self.add_counter1,
                                                              "surface1"))
        self.widget_canvas.add_widget(Widgets.Button(270,
                                                     20,
                                                     190,
                                                     55,
                                                     1,
                                                     BLACK,
                                                     ORANGE,
                                                     self.font,
                                                     "Let her down",
                                                     self.add_counter2,
                                                     "button1"))
        self.checkbox1 = Widgets.Checkbox(12,
                                          90,
                                          "Run around and desert her?",
                                          BLACK,
                                          ORANGE,
                                          230,
                                          self.font,
                                          20,
                                          1,
                                          "checkbox1")
        self.widget_canvas.add_widget(self.checkbox1)
        self.checkbox2 = Widgets.Checkbox(252,
                                          90,
                                          "Together forever and never to part?",
                                          BLACK,
                                          ORANGE,
                                          230,
                                          self.font,
                                          20,
                                          1,
                                          "checkbox2")
        self.widget_canvas.add_widget(self.checkbox2)
        self.radio_group = Widgets.RadioGroup()
        self.radio_group.add_radio_button(12,
                                          280,
                                          "Make her cry",
                                          BLACK,
                                          ORANGE,
                                          150,
                                          self.font,
                                          20,
                                          1,
                                          "radio1")
        self.radio_group.add_radio_button(172,
                                          280,
                                          "Say goodbye",
                                          BLACK,
                                          ORANGE,
                                          150,
                                          self.font,
                                          20,
                                          1,
                                          "radio2")
        self.radio_group.add_radio_button(332,
                                          280,
                                          "Tell a lie and hurt her",
                                          BLACK,
                                          ORANGE,
                                          150,
                                          self.font,
                                          20,
                                          1,
                                          "radio3")
        self.widget_canvas.add_widget(self.radio_group)
        self.slider = Widgets.Slider(30,
                                     490,
                                     25,
                                     BLACK,
                                     400,
                                     5,
                                     (250, 50, 50),
                                     (0, 255, 0),
                                     10,
                                     30,
                                     (0, 130, 205),
                                     (155, 205, 0),
                                     self.mandarin_font,
                                     1,
                                     100,
                                     7,
                                     "slider1")
        self.widget_canvas.add_widget(self.slider)
        self.entry1 = Widgets.Entry(10,
                                    530,
                                    150,
                                    30,
                                    4,
                                    self.mandarin_font,
                                    BLACK,
                                    "entry1")
        self.widget_canvas.add_widget(self.entry1)
        self.entry2 = Widgets.Entry(170,
                                    530,
                                    150,
                                    30,
                                    4,
                                    self.mandarin_font,
                                    BLACK,
                                    "entry2")
        self.widget_canvas.add_widget(self.entry2)
        self.entry3 = Widgets.Entry(330,
                                    530,
                                    150,
                                    30,
                                    4,
                                    self.mandarin_font,
                                    BLACK,
                                    "entry3")
        self.widget_canvas.add_widget(self.entry3)
        self.widget_canvas.add_widget(Widgets.Button(180,
                                                     572,
                                                     150,
                                                     55,
                                                     1,
                                                     BLACK,
                                                     ORANGE,
                                                     self.font,
                                                     "Submit",
                                                     self.submit,
                                                     "button2"))
        self.widget_canvas.add_widget(Widgets.Spinner(40,
                                                      580,
                                                      100,
                                                      15,
                                                      90,
                                                      250,
                                                      (205, 205, 205),
                                                      (26, 134, 219),
                                                      "spinner1"))
        self.widget_canvas.add_widget(Widgets.ScrollBar("scrollbar1"))
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
                elif event.type in (pygame.WINDOWFOCUSLOST,
                                    pygame.KEYDOWN,
                                    pygame.KEYUP,
                                    pygame.TEXTINPUT,
                                    pygame.TEXTEDITING):
                    self.key_events.append(event)
            self.mouse.set_pos(*pygame.mouse.get_pos())
            self.mouse.reset_z_index()
            self.widgets.update(self.mouse, self.key_events)
            self.display.fill(BLUE)
            self.widgets.draw(self.display)
            pygame.display.flip()
        pygame.quit()

    def add_counter1(self) -> None:
        self.counter1 += 1

    def add_counter2(self) -> None:
        self.counter2 += 1

    def submit(self) -> None:
        print("{}\n"
              "Love Stats:\n"
              "You gave her up {} times.\n"
              "You let her down {} times.\n"
              "You {} run around and desert her.\n"
              "You {} stay with her forever and not part with her.\n"
              "You chose to {}.\n"
              "The three messages you left her are: '{}', '{}', '{}'.\n"
              "You're {}% in love with Miss Rickietta."
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


if __name__ == "__main__":
    sys.path.extend((get_root_dir(),))
    import Widgets
    import Mouse
    if pygame.version.vernum >= (2, 0, 1):
        Window()
    else:
        print("This game requires Pygame version 2.0.1 or higher to run. Consider updating your version of Pygame "
              "with the command: 'python -m pip install --upgrade pygame'")
