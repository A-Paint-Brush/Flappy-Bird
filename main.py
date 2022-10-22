from os.path import normpath
from Global import *
from Resize import *
import Ground
import Bird
import Pipe
import pygame
# TODO: Hidden FPS counter.
# TODO: Show hit-boxes and FPS counter when the Konami code is entered.
# TODO: Toast notifier (in game) when low frame-rate is detected.
# TODO: Title screen (?) and game over screen.
# TODO: Make buttons on title screen dilate on hover, and flash white on click.
# TODO: Fading effect as the game transitions from the title screen to the game.
# FIXME: Mask collision detection is inaccurate.


class MainProc:
    def __init__(self):
        pygame.init()
        self.fixed_resolution = (513, 686)
        self.current_resolution = list(self.fixed_resolution)
        self.screen = "game"
        self.game_run = True
        self.game_state = "waiting"
        self.debug = False
        collide_result = None
        pipe_death = False
        pygame.display.set_caption("Flappy Bird")
        self.display = pygame.display.set_mode(self.fixed_resolution, pygame.RESIZABLE)
        self.background = pygame.image.load(normpath("./Images/background.png")).convert_alpha()
        self.tiles_group = Ground.GroundGroup(self.fixed_resolution)
        self.tiles_group.generate()
        self.bird = Bird.Bird(self.fixed_resolution, self.tiles_group.get_size())
        self.pipe_group = Pipe.PipeGroup(self.fixed_resolution, self.tiles_group.get_size())
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
                elif (event.type == pygame.MOUSEBUTTONDOWN) or (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE):
                    self.interact()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_u:  # FIXME: Make sure to remove this
                    self.debug = not self.debug
            self.display_surface.fill(BLACK)
            self.display_surface.blit(self.background, (0, 0))
            # region Screen Rendering
            if self.game_state == "waiting":
                self.move_ground_tiles()
                self.tiles_group.draw(self.display_surface)
                self.bird.wiggle_tick()
                self.bird.tick_costume(force_update=True)
            elif self.game_state == "started" or self.game_state == "dying":
                speed = self.bird.tick()
                self.bird.tick_costume()
                self.bird.calc_angle(speed)
                if self.game_state == "dying" and pipe_death:
                    if collided_pipe.flash_tick():
                        pipe_death = False
                if self.game_state == "started":
                    collide_result = self.bird.collision_detection(self.tiles_group.get_pos(), self.pipe_group, True)
                    if collide_result[0] == 3:
                        collided_pipe = collide_result[1]
                        collided_pipe.init_flash()
                        pipe_death = True
                        print("Rotation collision")
                        self.die()
                    else:
                        amount = self.move_ground_tiles()
                        collide_result = self.pipe_group.move(amount, self.bird)
                        self.pipe_group.kill_colliding()
                        if collide_result[0]:
                            collided_pipe = collide_result[1]
                            collided_pipe.init_flash()
                            pipe_death = True
                            print("Pipe movement collision")
                            self.die()
                self.tiles_group.draw(self.display_surface)
                self.pipe_group.draw(self.display_surface)
                if self.debug:
                    self.pipe_group.draw_hit_box(self.display_surface)
                collide_result = 0
                if self.game_state == "started":
                    collide_result = self.bird.collision_detection(self.tiles_group.get_pos(), self.pipe_group)
            self.bird.draw(self.display_surface, self.debug)
            if self.game_state == "started" and collide_result == 1:
                self.die()
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

    def interact(self):
        if self.game_state == "waiting":
            self.game_state = "started"
            self.pipe_group.generate()
            self.bird.init_gravity_physics()
            self.bird.jump()
        elif self.game_state == "started":
            self.bird.jump()

    def move_ground_tiles(self):
        amount = self.tiles_group.move()
        self.tiles_group.kill_colliding()
        return amount

    def die(self):
        self.game_state = "dying"
        self.bird.jump()


if __name__ == "__main__":
    MainProc()
