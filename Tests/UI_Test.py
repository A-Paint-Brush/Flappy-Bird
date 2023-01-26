from typing import *
import os.path as path
import Widgets
import Mouse
import pygame
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREY = (240, 240, 240)


class Window:
    def __init__(self):
        pygame.init()
        self.resolution = (513, 350)
        self.fps = 60
        self.game_run = True
        self.clock = pygame.time.Clock()
        self.widget_canvas = Widgets.WidgetCanvas(0, 0, *self.resolution, "canvas1")
        self.widgets = Widgets.WidgetGroup()
        self.widgets.add_widget_canvas(self.widget_canvas)
        self.mouse = Mouse.Cursor()
        self.key_event = None
        self.font = pygame.font.Font(path.normpath("../Fonts/Arial.ttf"), 28)
        btn_surf = pygame.Surface((90, 40))
        btn_surf.fill((215, 215, 215))
        text = self.font.render("Test", True, BLACK)
        btn_surf.blit(text, self.center_widget(btn_surf.get_size(), text.get_size()))
        anim_surf = Widgets.AnimatedSurface(*self.center_widget(self.resolution, btn_surf.get_size()),
                                            btn_surf,
                                            lambda: print("foo"),
                                            "surface1")
        self.widget_canvas.add_widget(anim_surf)
        pygame.display.set_caption("MainProc")
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
            pygame.display.update()
        pygame.quit()

    def center_widget(self, container_size: Tuple[int, int], content_size: Tuple[int, int]) -> Tuple[float, float]:
        return container_size[0] / 2 - content_size[0] / 2, container_size[1] / 2 - content_size[1] / 2


if __name__ == "__main__":
    Window()
