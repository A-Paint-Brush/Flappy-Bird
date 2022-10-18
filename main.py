from os.path import normpath
from Colors import *
from Resize import *
import Ground_Group
import Bird
import pygame
# TODO: Add pipes.


class MainProc:
    def __init__(self):
        pygame.init()
        self.fixed_resolution = (513, 686)
        self.current_resolution = list(self.fixed_resolution)
        self.screen = "game"
        self.game_run = True
        self.game_state = "waiting"
        collide_result = None
        pygame.display.set_caption("Flappy Bird")
        self.display = pygame.display.set_mode(self.fixed_resolution, pygame.RESIZABLE)
        self.background = pygame.image.load(normpath("./Images/background.png")).convert_alpha()
        self.tiles_group = Ground_Group.GroundGroup(self.fixed_resolution)
        self.bird = Bird.Bird(self.fixed_resolution, self.tiles_group.get_size())
        self.display_surface = pygame.Surface(self.fixed_resolution)
        self.clock = pygame.time.Clock()
        self.fps = 60
        while self.game_run:
            self.clock.tick(self.fps)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_run = False
                elif event.type == pygame.VIDEORESIZE:
                    self.current_resolution[0] = event.w
                    self.current_resolution[1] = event.h
                    if self.current_resolution[0] < self.fixed_resolution[0]:
                        self.current_resolution[0] = self.fixed_resolution[0]
                    if self.current_resolution[1] < self.fixed_resolution[1]:
                        self.current_resolution[1] = self.fixed_resolution[1]
                    self.display = pygame.display.set_mode(self.current_resolution, pygame.RESIZABLE)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.game_state == "waiting":
                        self.game_state = "started"
                        self.bird.init_gravity_physics()
                        self.bird.jump()
                    elif self.game_state == "started":
                        self.bird.jump()
            self.display_surface.fill(BLACK)
            self.display_surface.blit(self.background, (0, 0))
            # region Screen Rendering
            self.tiles_group.update_()
            self.tiles_group.kill_colliding(self.display_surface)
            self.tiles_group.draw(self.display_surface)
            if self.game_state == "waiting":
                self.bird.wiggle_tick()
                self.bird.tick_costume(force_update=True)
            elif self.game_state == "started" or self.game_state == "dying":
                speed = self.bird.tick()
                self.bird.tick_costume()
                rect = self.bird.calc_angle(speed)
                collide_result = 0
                if self.game_state == "started":
                    collide_result = self.bird.collision_detection(self.tiles_group.get_pos())
            self.bird.draw(self.display_surface, False)
            if self.game_state == "started" and collide_result == 1:
                self.game_state = "dying"
                self.bird.jump()
            # endregion
            resized_surface = resize_surf(self.display_surface, self.current_resolution)
            self.display.fill(CYAN)
            self.display.blit(resized_surface, (round(self.current_resolution[0] / 2 - resized_surface.get_width() / 2),
                                                round(self.current_resolution[1] / 2 - resized_surface.get_height() / 2)))
            if resized_surface.get_size()[1] < self.current_resolution[1]:
                # Without the -1 on the y pos and the +1 on height, the yellow rectangle will be one
                # pixel too low, resulting in a 1 pixel line of blue to show through.
                pygame.draw.rect(self.display, YELLOW, pygame.Rect(0, self.current_resolution[1] - round((self.current_resolution[1] - resized_surface.get_size()[1]) / 2) - 1, self.current_resolution[0], round((self.current_resolution[1] - resized_surface.get_size()[1]) / 2) + 1))
            pygame.display.update()
        pygame.quit()


if __name__ == "__main__":
    MainProc()
