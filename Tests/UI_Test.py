from typing import *
import os.path as path
import Widgets
import Mouse
import pygame
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREY = (240, 240, 240)
ORANGE = (255, 160, 20)


class Window:
    def __init__(self):
        pygame.init()
        self.resolution = (513, 500)
        self.fps = 60
        self.game_run = True
        self.clock = pygame.time.Clock()
        self.widget_canvas = Widgets.WidgetCanvas(0, 0, *self.resolution, 1, "canvas1")
        self.widgets = Widgets.WidgetGroup()
        self.widgets.add_widget_canvas(self.widget_canvas)
        self.mouse = Mouse.Cursor()
        self.key_event = None
        self.font = pygame.font.Font(path.normpath("../Fonts/Arial.ttf"), 28)
        text = self.font.render("Give her up", True, BLACK)
        btn_surf = pygame.Surface((text.get_size()[0] + 30, text.get_size()[1] + 20))
        btn_surf.fill((215, 215, 215))
        btn_surf.blit(text, self.center_widget(btn_surf.get_size(), text.get_size()))
        self.widget_canvas.add_widget(Widgets.AnimatedSurface(50, 20, btn_surf, lambda: print("foo"), "surface1"))
        self.widget_canvas.add_widget(Widgets.Button(280,
                                                     20,
                                                     190,
                                                     55,
                                                     1,
                                                     BLACK,
                                                     ORANGE,
                                                     self.font,
                                                     "Let her down",
                                                     lambda: print("bar"),
                                                     "button1"))
        self.widget_canvas.add_widget(Widgets.Checkbox(10,
                                                       90,
                                                       "Run around and desert her?",
                                                       BLACK,
                                                       ORANGE,
                                                       230,
                                                       self.font,
                                                       20,
                                                       1,
                                                       "checkbox1"))
        self.widget_canvas.add_widget(Widgets.Checkbox(270,
                                                       90,
                                                       "Together forever and never to part?",
                                                       BLACK,
                                                       ORANGE,
                                                       230,
                                                       self.font,
                                                       20,
                                                       1,
                                                       "checkbox2"))
        radio_group = Widgets.RadioGroup()
        radio_group.add_radio_button(10, 280, "Make her cry", BLACK, ORANGE, 150, self.font, 20, 1, "radio1")
        radio_group.add_radio_button(180, 280, "Say goodbye", BLACK, ORANGE, 150, self.font, 20, 1, "radio2")
        radio_group.add_radio_button(350, 280, "Tell a lie and hurt her", BLACK, ORANGE, 150, self.font, 20, 1, "radio3")
        for w in radio_group.get_children():
            self.widget_canvas.add_widget(w)
        pygame.display.set_caption("GUI Toolkit")
        self.display = pygame.display.set_mode(self.resolution, pygame.HWSURFACE | pygame.DOUBLEBUF)
        while self.game_run:
            self.clock.tick(self.fps)
            self.key_event = None
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_run = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.mouse.set_button_state(event.button, True)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.mouse.set_button_state(event.button, False)
                elif event.type == pygame.KEYDOWN:
                    self.key_event = event
            self.mouse.set_pos(*pygame.mouse.get_pos())
            self.mouse.reset_z_index()
            self.widgets.update(self.mouse, self.key_event)
            self.display.fill(GREY)
            self.widgets.draw(self.display)
            pygame.display.flip()
        pygame.quit()

    def center_widget(self, container_size: Tuple[int, int], content_size: Tuple[int, int]) -> Tuple[float, float]:
        return container_size[0] / 2 - content_size[0] / 2, container_size[1] / 2 - content_size[1] / 2


if __name__ == "__main__":
    Window()
