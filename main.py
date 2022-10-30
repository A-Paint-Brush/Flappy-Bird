from os.path import normpath
from Global import *
import Ground
import Bird
import Pipe
import Rainbow
import Keyboard
import Notifier
import Achievements
import FPS
import pygame
# TODO: Toast notifier (in game) when low frame-rate is detected.
# TODO: Make the title screen, game over screen, and pause menu.
# TODO: Screen darkening effect as pause menu slides into view.
# TODO: Option to hide mouse pointer in the pause menu.
# TODO: Make buttons on title screen dilate on hover, and flash white on click.
# TODO: Fading effect as the game transitions from the title screen to the game.
# TODO: Submit score pop-up on results screen.
# TODO: Achievements page and in-game instructions.


class MainProc:
    def __init__(self):
        pygame.init()
        self.fixed_resolution = (513, 686)
        self.current_resolution = list(self.fixed_resolution)
        self.restore_resolution = None
        self.monitor_info = pygame.display.Info()
        self.monitor_resolution = (self.monitor_info.current_w, self.monitor_info.current_h)
        # region State variables
        self.screen = "game"
        self.game_run = True
        self.game_state = "waiting"
        self.debug = False
        self.rainbow_mode = False
        self.full_screen = False
        # endregion
        self.rickroll_audio = pygame.mixer.Sound(normpath("./Sounds/Rickroll.wav"))
        self.pipe_death = False  # Is True if the bird died by hitting a pipe.
        self.flash_pipe = None  # Stores the sprite instance of the pipe that has to be flashed.
        pygame.display.set_caption("Flappy Bird")
        self.display = pygame.display.set_mode(self.fixed_resolution, pygame.RESIZABLE)
        self.resized_surface = None
        self.background = pygame.image.load(normpath("./Images/background.png")).convert_alpha()
        self.tiles_group = Ground.GroundGroup(self.fixed_resolution)
        self.tiles_group.generate()
        self.bird = Bird.Bird(self.fixed_resolution, self.tiles_group.get_size())
        self.pipe_group = Pipe.PipeGroup(self.fixed_resolution, self.tiles_group.get_size())
        self.notifiers = Notifier.ToastGroup(self.fixed_resolution)
        self.achievement_list = Achievements.Storage()
        self.rainbow = Rainbow.Rainbow()
        self.fps_counter = FPS.Counter(self.fixed_resolution)
        key_table = {"↑": pygame.K_UP, "↓": pygame.K_DOWN, "←": pygame.K_LEFT, "→": pygame.K_RIGHT}
        konami_string = "↑↑↓↓←→←→ba"
        magic_string = "xyzzy"
        rickroll_string = "rickroll"
        key_generator = lambda string: tuple(key_table[char] if char in key_table else ord(char) for char in string)
        self.konami = Keyboard.KeySequence(key_generator(konami_string))
        self.magic_word = Keyboard.KeySequence(key_generator(magic_string))
        self.rickroll = Keyboard.KeySequence(key_generator(rickroll_string))
        self.display_surface = pygame.Surface(self.fixed_resolution)
        self.clock = pygame.time.Clock()
        self.fps = 60
        while self.game_run:
            self.clock.tick(self.fps)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_run = False
                elif event.type == pygame.VIDEORESIZE:
                    if not self.full_screen:
                        self.resize_window(event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.interact()
                        if self.notifiers.get_toast_num() > 0 and self.resized_surface is not None:
                            self.notifiers.send_mouse_pos(resize_mouse_pos(event.pos,
                                                                           self.fixed_resolution,
                                                                           self.current_resolution,
                                                                           self.resized_surface.get_size()))
                elif event.type == pygame.KEYDOWN:
                    self.check_key_sequence(self.konami, event.key, self.toggle_rainbow)
                    self.check_key_sequence(self.magic_word, event.key, self.toggle_debug)
                    self.check_key_sequence(self.rickroll, event.key, self.toggle_rickroll)
                    if event.key == pygame.K_F11:
                        self.toggle_full_screen()
                    elif event.key == pygame.K_SPACE:
                        self.interact()
            self.display_surface.fill(BLACK)
            self.display_surface.blit(self.background, (0, 0))
            # region Screen Rendering
            if self.game_state == "waiting":
                self.move_ground_tiles()
                self.tiles_group.draw(self.display_surface)
                self.bird.wiggle_tick()
                self.bird.tick_costume(force_update=True)
            elif self.game_state == "started":
                collision_type, collided_pipe = self.tick_all()
                if collision_type in (1, 2, 3):
                    self.pipe_death = True
                    self.flash_pipe = collided_pipe
                    self.flash_pipe.init_flash()
                    self.die()
                elif collision_type == 4:
                    self.die()
            elif self.game_state == "dying":
                speed, movement = self.bird.tick()
                self.bird.move_collide(movement, None, collide=False)
                self.bird.calc_angle(speed, None, collide=False)  # Collision detection is no longer needed after death.
                if self.pipe_death:
                    self.pipe_death = not self.flash_pipe.flash_tick()
            self.tiles_group.draw(self.display_surface)
            self.pipe_group.draw(self.display_surface)
            fps = self.fps_counter.tick()
            if self.debug:
                self.pipe_group.draw_hit_box(self.display_surface)
                self.fps_counter.draw(self.display_surface)
            if fps is not None and fps < 30:
                if not self.achievement_list.has_achievement(3):
                    achievement_text = self.achievement_list.get_new_achievement(3)
                    self.notifiers.create_toast(*achievement_text)
            self.bird.draw(self.display_surface, self.debug)
            if self.notifiers.get_toast_num() > 0:
                self.notifiers.update()
                self.notifiers.draw(self.display_surface)
            # endregion
            if self.rainbow_mode:
                self.rainbow.tick()
            self.resized_surface = resize_surf(self.display_surface, self.current_resolution)
            self.display.fill(self.rainbow.get_color() if self.rainbow_mode else BLACK)
            self.blit_resized_surface(self.display, self.resized_surface)
            pygame.display.update()
        pygame.quit()

    def blit_resized_surface(self, display, resized_surface):
        display.blit(resized_surface, (round(self.current_resolution[0] / 2 - resized_surface.get_width() / 2),
                                       round(self.current_resolution[1] / 2 - resized_surface.get_height() / 2)))

    def resize_window(self, event):
        self.current_resolution[0] = event.w
        self.current_resolution[1] = event.h
        if self.current_resolution[0] < self.fixed_resolution[0]:
            self.current_resolution[0] = self.fixed_resolution[0]
        if self.current_resolution[1] < self.fixed_resolution[1]:
            self.current_resolution[1] = self.fixed_resolution[1]
        self.display = pygame.display.set_mode(self.current_resolution, pygame.RESIZABLE)

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

    def tick_all(self):
        """
        Update all items on the screen and return the type of collision that is currently happening.

        | 0: No collision
        | 1: Vertical movement collision
        | 2: Rotation collision
        | 3: Pipe movement collision
        | 4: Ground collision
        """
        self.bird.tick_costume(True)
        speed, movement = self.bird.tick()
        vertical_collide = self.bird.move_collide(movement, self.pipe_group)
        if vertical_collide[0]:
            print("Vertical movement collision")
            return 1, vertical_collide[1]
        rotation_collide = self.bird.calc_angle(speed, self.pipe_group)
        if rotation_collide[0]:
            print("Rotation collision")
            return 2, rotation_collide[1]
        amount = self.move_ground_tiles()
        pipe_collide = self.pipe_group.move(amount, self.bird)
        if pipe_collide[0]:
            print("Pipe movement collision")
            return 3, pipe_collide[1]
        self.pipe_group.kill_colliding()
        ground_collide = self.bird.collision_detection(self.tiles_group.get_pos())
        if ground_collide == 1:
            print("Ground collision")
            return 4, None
        return 0, None

    def check_key_sequence(self, sequence_obj, key_code, callback):
        result = sequence_obj.push_key(key_code)
        if result:
            callback()

    def toggle_rainbow(self):
        self.rainbow_mode = not self.rainbow_mode
        if self.rainbow_mode:
            self.rainbow.init_rainbow()
            if not self.achievement_list.has_achievement(0):
                achievement_text = self.achievement_list.get_new_achievement(0)
                self.notifiers.create_toast(*achievement_text)

    def toggle_debug(self):
        self.debug = not self.debug
        if self.debug:
            if not self.achievement_list.has_achievement(1):
                achievement_text = self.achievement_list.get_new_achievement(1)
                self.notifiers.create_toast(*achievement_text)
        else:
            pass
            # self.fps_counter.stop()

    def toggle_rickroll(self):
        if pygame.mixer.get_busy():
            self.rickroll_audio.stop()
        else:
            self.rickroll_audio.play()
            if not self.achievement_list.has_achievement(2):
                achievement_text = self.achievement_list.get_new_achievement(2)
                self.notifiers.create_toast(*achievement_text)

    def toggle_full_screen(self):
        if self.full_screen:
            self.full_screen = False
            self.current_resolution = list(self.restore_resolution)
            self.display = pygame.display.set_mode(self.current_resolution, pygame.RESIZABLE)
        else:
            self.full_screen = True
            self.restore_resolution = tuple(self.current_resolution)
            self.current_resolution = list(self.monitor_resolution)
            self.display = pygame.display.set_mode(self.current_resolution, pygame.FULLSCREEN)

    def die(self):
        self.game_state = "dying"
        self.bird.jump()


if __name__ == "__main__":
    MainProc()
