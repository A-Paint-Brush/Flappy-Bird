from os.path import normpath
from Global import *
from dataclasses import *
import Mouse
import Widgets
import Ground
import Bird
import Pipe
import Rainbow
import Keyboard
import Notifier
import Achievements
import FPS
import pygame


class MainProc:
    def __init__(self):
        pygame.init()
        # region Display Data
        self.fixed_resolution = (513, 686)
        self.current_resolution = list(self.fixed_resolution)
        self.restore_resolution = None
        self.monitor_info = pygame.display.Info()
        self.monitor_resolution = (self.monitor_info.current_w, self.monitor_info.current_h)
        # endregion
        # region State Variables
        self.state_data = StateManager("game", "menu")
        self.game_run = True
        self.debug = False
        self.rainbow_mode = False
        self.full_screen = False
        # endregion
        # region Graphic Storage
        self.rickroll_audio = pygame.mixer.Sound(normpath("./Sounds/Rickroll.wav"))
        self.resized_surface = pygame.Surface(self.fixed_resolution)
        self.display_surface = pygame.Surface(self.fixed_resolution)
        # endregion
        # region Widget Setup
        self.ui_widgets = Widgets.WidgetGroup()
        # endregion
        # region Key Sequences
        self.key_table: Dict[str, int] = {"↑": pygame.K_UP, "↓": pygame.K_DOWN, "←": pygame.K_LEFT, "→": pygame.K_RIGHT}
        for char in "abciklorxyz":
            # Generate all needed key codes.
            exec(f"self.key_table['{char}'] = pygame.K_{char}")
        konami_string = "↑↑↓↓←→←→ba"
        magic_string = "xyzzy"
        rickroll_string = "rickroll"
        self.konami = Keyboard.KeySequence(self.key_generator(konami_string))
        self.magic_word = Keyboard.KeySequence(self.key_generator(magic_string))
        self.rickroll = Keyboard.KeySequence(self.key_generator(rickroll_string))
        # endregion
        # region Window Creation
        pygame.display.set_caption("Flappy Bird")
        self.display = pygame.display.set_mode(self.fixed_resolution, pygame.RESIZABLE)
        self.listen_events = (pygame.QUIT,
                              pygame.WINDOWFOCUSLOST,
                              pygame.WINDOWENTER,
                              pygame.WINDOWLEAVE,
                              pygame.VIDEORESIZE,
                              pygame.MOUSEBUTTONDOWN,
                              pygame.MOUSEBUTTONUP,
                              pygame.MOUSEWHEEL,
                              pygame.KEYDOWN,
                              pygame.KEYUP,
                              pygame.TEXTINPUT,
                              pygame.TEXTEDITING)
        pygame.event.set_blocked(None)
        pygame.event.set_allowed(self.listen_events)
        pygame.key.stop_text_input()
        # endregion
        # region Game Objects
        self.background = pygame.image.load(normpath("Images/Sprites/background.png")).convert_alpha()
        self.mouse_obj = Mouse.Cursor()
        self.bird = Bird.BirdManager(self.fixed_resolution)
        self.tiles_group = Ground.GroundGroup(self.fixed_resolution)
        self.pipe_group = Pipe.PipeGroup(self.fixed_resolution, self.tiles_group.get_size())
        self.notifiers = Notifier.ToastGroup(self.fixed_resolution)
        self.achievement_list = Achievements.Storage()
        self.rainbow = Rainbow.Rainbow()
        self.fps_counter = FPS.Counter(self.fixed_resolution)
        # endregion
        # region Timing Control
        self.fps = 60
        self.clock = pygame.time.Clock()
        # endregion
        while self.game_run:
            self.clock.tick(self.fps)
            self.mouse_obj.reset_scroll()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_run = False
                elif event.type == pygame.WINDOWENTER:
                    self.mouse_obj.mouse_enter()
                elif event.type == pygame.WINDOWLEAVE:
                    self.mouse_obj.mouse_leave()
                elif event.type == pygame.VIDEORESIZE:
                    if not self.full_screen:
                        self.resize_window(event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.mouse_obj.set_button_state(event.button, True)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.mouse_obj.set_button_state(event.button, False)
                elif event.type == pygame.MOUSEWHEEL:
                    self.mouse_obj.push_scroll(event.y)
                elif event.type == pygame.KEYDOWN:
                    # region Key Sequence Detection
                    self.check_key_sequence(self.konami, event.key, self.toggle_rainbow)
                    self.check_key_sequence(self.magic_word, event.key, self.toggle_debug)
                    self.check_key_sequence(self.rickroll, event.key, self.toggle_rickroll)
                    # endregion
                    if event.key == pygame.K_F11:
                        self.toggle_full_screen()
                    elif event.key == pygame.K_SPACE:
                        if self.state_data.game_state in ("waiting", "started"):
                            # Jumping the bird is only allowed during "waiting" or "started", not after death.
                            self.bird.click(self.state_data, self.tiles_group, self.pipe_group, self.mouse_obj, False)
            self.mouse_obj.set_pos(*resize_mouse_pos(pygame.mouse.get_pos(),
                                                     self.fixed_resolution,
                                                     self.current_resolution,
                                                     self.resized_surface.get_size()))
            # region User Events and Updating Game Objects
            self.mouse_obj.reset_z_index()  # Set mouse event processing z-order back to top.
            self.notifiers.send_mouse_pos(self.mouse_obj)
            if self.state_data.game_state == "menu":
                self.ui_widgets.update(self.mouse_obj, [])
                self.tiles_group.move()
                self.tiles_group.reset_pos()
            elif self.state_data.game_state in ("waiting", "started", "dying"):
                self.bird.click(self.state_data, self.tiles_group, self.pipe_group, self.mouse_obj, True)
                self.bird.update(self.tiles_group, self.pipe_group, self.state_data)
            if self.rainbow_mode:
                self.rainbow.tick()
            self.fps_counter.tick()
            self.notifiers.update()  # Does nothing if there are no toast notifications.
            # endregion
            # region Screen Rendering
            self.display_surface.fill(BLACK)
            self.display_surface.blit(self.background, (0, 0))
            self.tiles_group.draw(self.display_surface)
            if self.state_data.game_state == "menu":
                self.ui_widgets.draw(self.display_surface)
            elif self.state_data.game_state in ("started", "dying"):
                self.pipe_group.draw(self.display_surface)
                if self.debug:
                    self.pipe_group.draw_hit_box(self.display_surface)
            if self.state_data.game_state in ("waiting", "started", "dying"):
                self.bird.draw_(self.display_surface, self.debug)  # Debug mode support!
            if self.debug:
                self.fps_counter.draw(self.display_surface)
            self.notifiers.draw(self.display_surface)  # Draws nothing if empty.
            # endregion
            # region Display Resizing
            self.resized_surface = resize_surf(self.display_surface, self.current_resolution)
            self.display.fill(self.rainbow.get_color() if self.rainbow_mode else BLACK)
            self.blit_resized_surface(self.display, self.resized_surface)
            # endregion
            pygame.display.update()
        pygame.quit()

    def key_generator(self, string: str) -> Tuple[int]:
        return tuple(self.key_table[char] for char in string)

    def blit_resized_surface(self, display: pygame.Surface, resized_surface: pygame.Surface) -> None:
        display.blit(resized_surface, (round(self.current_resolution[0] / 2 - resized_surface.get_width() / 2),
                                       round(self.current_resolution[1] / 2 - resized_surface.get_height() / 2)))

    def resize_window(self, event: pygame.event.Event) -> None:
        self.current_resolution[0] = event.w
        self.current_resolution[1] = event.h
        if self.current_resolution[0] < self.fixed_resolution[0]:
            self.current_resolution[0] = self.fixed_resolution[0]
        if self.current_resolution[1] < self.fixed_resolution[1]:
            self.current_resolution[1] = self.fixed_resolution[1]
        self.display = pygame.display.set_mode(self.current_resolution, pygame.RESIZABLE)

    def check_key_sequence(self,
                           sequence_obj: Keyboard.KeySequence,
                           key_code: int, callback: Callable[[], None]) -> None:
        result = sequence_obj.push_key(key_code)
        if result:
            callback()

    def toggle_rainbow(self) -> None:
        self.rainbow_mode = not self.rainbow_mode
        if self.rainbow_mode:
            self.rainbow.init_rainbow()
            if not self.achievement_list.has_achievement(0):
                achievement_text = self.achievement_list.get_new_achievement(0)
                self.notifiers.create_toast(*achievement_text)

    def toggle_debug(self) -> None:
        self.debug = not self.debug
        if self.debug:
            if not self.achievement_list.has_achievement(1):
                achievement_text = self.achievement_list.get_new_achievement(1)
                self.notifiers.create_toast(*achievement_text)

    def toggle_rickroll(self) -> None:
        if pygame.mixer.get_busy():
            self.rickroll_audio.stop()
        else:
            self.rickroll_audio.play()
            if not self.achievement_list.has_achievement(2):
                achievement_text = self.achievement_list.get_new_achievement(2)
                self.notifiers.create_toast(*achievement_text)

    def toggle_full_screen(self) -> None:
        if self.full_screen:
            self.full_screen = False
            self.current_resolution = list(self.restore_resolution)
            self.display = pygame.display.set_mode(self.current_resolution, pygame.RESIZABLE)
        else:
            self.full_screen = True
            self.restore_resolution = tuple(self.current_resolution)
            self.current_resolution = list(self.monitor_resolution)
            self.display = pygame.display.set_mode(self.current_resolution, pygame.FULLSCREEN)


@dataclass
class StateManager:
    screen: str
    game_state: str


if __name__ == "__main__":
    if pygame.version.vernum >= (2, 0, 1):
        MainProc()
    else:
        print("This game requires Pygame version 2.0.1 or higher to run. Consider updating your version of Pygame "
              "with the command: 'python -m pip install --upgrade pygame'")
