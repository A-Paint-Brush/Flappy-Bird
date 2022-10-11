from os.path import normpath
from Colors import *
from Resize import *
import Ground
import pygame
# All images have to be reduced by a ratio of 1.493̅, meaning: (image height) / 1.493̅


class MainProc:
    def __init__(self):
        pygame.init()
        self.fixed_resolution = (513, 686)
        self.current_resolution = list(self.fixed_resolution)
        self.screen = "game"
        self.background = pygame.image.load(normpath("./Images/background.png"))
        self.game_run = True
        temp = Ground.Tile(0, self.fixed_resolution)
        self.ground_tiles_obj = [Ground.Tile(x, self.fixed_resolution) for x in range(self.fixed_resolution[0], -temp.get_size()[0], -temp.get_size()[0])]
        self.ground_tiles_group = pygame.sprite.Group(self.ground_tiles_obj)
        pygame.display.set_caption("Flappy Bird")
        self.display = pygame.display.set_mode(self.fixed_resolution, pygame.RESIZABLE)
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
            self.display_surface.blit(self.background, (0, 0))
            # region Draw to screen here
            self.ground_tiles_group.update()
            self.ground_tiles_obj[:] = [tile for tile in self.ground_tiles_obj if not tile.check_collision()]
            if self.ground_tiles_obj[0].get_pos()[0] < self.fixed_resolution[0] - self.ground_tiles_obj[0].get_size()[0] + self.ground_tiles_obj[0].get_speed():
                self.ground_tiles_obj.insert(0, Ground.Tile(self.fixed_resolution[0], self.fixed_resolution))
                self.ground_tiles_group.add(self.ground_tiles_obj[0])
            self.ground_tiles_group.draw(self.display_surface)
            # endregion
            resized_surface = resize_surf(self.display_surface, self.current_resolution)
            self.display.fill(CYAN)
            self.display.blit(resized_surface, (round(self.current_resolution[0] / 2 - resized_surface.get_width() / 2),
                                                round(self.current_resolution[1] / 2 - resized_surface.get_height() / 2)))
            if resized_surface.get_size()[1] < self.current_resolution[1]:
                # For some reason, without the -1 on the y pos and the +1 on height, the yellow rectangle will be one
                # pixel too low, resulting in a 1 pixel line of blue to show through.
                pygame.draw.rect(self.display, YELLOW, pygame.Rect(0, self.current_resolution[1] - round((self.current_resolution[1] - resized_surface.get_size()[1]) / 2) - 1, self.current_resolution[0], round((self.current_resolution[1] - resized_surface.get_size()[1]) / 2) + 1))
            pygame.display.update()
        pygame.quit()


if __name__ == "__main__":
    MainProc()
