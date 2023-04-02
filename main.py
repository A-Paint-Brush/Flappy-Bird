from os.path import normpath
from Global import *
from dataclasses import *
import Mouse
import Widgets
import Dialogs
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
        self.fixed_resolution = (641, 858)
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
        # region Assets Storage
        self.audio_objects: Dict[str, pygame.mixer.Sound] = {
            "rickroll": pygame.mixer.Sound(normpath("./Sounds/Rickroll.wav"))
        }
        self.volume = 100
        self.resized_surface = pygame.Surface(self.fixed_resolution)
        self.display_surface = pygame.Surface(self.fixed_resolution)
        # endregion
        # region Widget Setup
        self.special_widgets: Dict[Literal["transition", "settings"],
                                   List[Union[tuple, Widgets.SceneTransition, Dialogs.Settings],
                                        Optional[Callable[[], None]]]] = {}
        self.key_events = []
        self.display_frame: Optional[Widgets.Frame] = None  # The widget-frame is rendered below the notifiers.
        self.init_menu_frame()
        # endregion
        # region Key Sequences
        self.key_table: Dict[str, int] = {"↑": pygame.K_UP, "↓": pygame.K_DOWN, "←": pygame.K_LEFT, "→": pygame.K_RIGHT}
        for char in "abciklorxyz":
            # Generate all needed key codes.
            exec("self.key_table['{c}'] = pygame.K_{c}".format(c=char))
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
        self.bird = Bird.BirdManager(self.fixed_resolution, 5)
        self.tiles_group = Ground.GroundGroup(self.fixed_resolution)
        self.pipe_group = Pipe.PipeGroup(self.fixed_resolution, self.tiles_group.get_size())
        self.notifiers = Notifier.ToastGroup(self.fixed_resolution, 2)
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
            self.key_events.clear()
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
                elif event.type in (pygame.WINDOWFOCUSLOST, pygame.KEYDOWN, pygame.KEYUP, pygame.TEXTINPUT,
                                    pygame.TEXTEDITING):
                    self.key_events.append(event)
                    if event.type == pygame.KEYDOWN:
                        # region Key Sequence Detection
                        self.check_key_sequence(self.konami, event.key, self.toggle_rainbow)
                        self.check_key_sequence(self.magic_word, event.key, self.toggle_debug)
                        self.check_key_sequence(self.rickroll, event.key, self.toggle_rickroll)
                        # endregion
                        if event.key == pygame.K_SPACE:
                            if self.state_data.game_state in ("waiting", "started") and \
                                    "transition" not in self.special_widgets:
                                # Jumping the bird is only allowed during "waiting" or "started", not after death.
                                self.bird.click(self.state_data, self.pipe_group, self.mouse_obj, False)
            self.mouse_obj.set_pos(*resize_mouse_pos(pygame.mouse.get_pos(),
                                                     self.fixed_resolution,
                                                     self.current_resolution,
                                                     self.resized_surface.get_size()))
            # region User Events and Updating Game Objects
            self.mouse_obj.reset_z_index()  # Set mouse event processing z-order back to top.
            if "transition" in self.special_widgets and isinstance(self.special_widgets["transition"][0], tuple):
                self.special_widgets["transition"][0] = Widgets.SceneTransition(*self.special_widgets["transition"][0])
            elif "settings" in self.special_widgets and isinstance(self.special_widgets["settings"][0], tuple):
                self.special_widgets["settings"][0] = Dialogs.Settings(*self.special_widgets["settings"][0])
            if "transition" in self.special_widgets and isinstance(self.special_widgets["transition"][0],
                                                                   Widgets.SceneTransition):
                return_code = self.special_widgets["transition"][0].update()
                if return_code == 1:
                    self.special_widgets["transition"][1]()
                elif return_code == 2:
                    self.special_widgets.pop("transition")
            else:
                self.mouse_obj.increment_z_index()
            # The z-index will not be increased if the mouse touches any toasts.
            self.notifiers.send_mouse_pos(self.mouse_obj)
            if "settings" in self.special_widgets and isinstance(self.special_widgets["settings"][0],
                                                                 Dialogs.Settings):
                return_code = self.special_widgets["settings"][0].update(self.mouse_obj, self.key_events)
                new_volume = self.special_widgets["settings"][0].get_volume()
                if new_volume != self.volume:
                    self.volume = new_volume
                    volume_float = self.volume / 100
                    for sound in self.audio_objects.values():
                        sound.set_volume(volume_float)
                if return_code:
                    self.special_widgets.pop("settings")
            else:
                self.mouse_obj.increment_z_index()
            # The mouse will only be able to interact with the widgets if it did not touch any toasts.
            self.display_frame.update(self.mouse_obj, self.key_events)
            if self.state_data.game_state == "menu":
                self.tiles_group.move()
                self.tiles_group.reset_pos()
            elif self.state_data.game_state in ("waiting", "started", "dying"):
                self.bird.click(self.state_data, self.pipe_group, self.mouse_obj, True)
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
            if self.state_data.game_state in ("started", "dying"):
                self.pipe_group.draw(self.display_surface)
                if self.debug:
                    self.pipe_group.draw_hit_box(self.display_surface)
            if self.state_data.game_state in ("waiting", "started", "dying"):
                self.bird.draw_(self.display_surface, self.debug)  # For debug mode support.
            if self.debug:
                self.fps_counter.draw(self.display_surface)
            self.display_surface.blit(self.display_frame.image, self.display_frame.rect)
            if "settings" in self.special_widgets and isinstance(self.special_widgets["settings"][0],
                                                                 Dialogs.Settings):
                self.special_widgets["settings"][0].draw()
            self.notifiers.draw(self.display_surface)  # Draws nothing if empty.
            if "transition" in self.special_widgets and isinstance(self.special_widgets["transition"][0],
                                                                   Widgets.SceneTransition):
                self.display_surface.blit(self.special_widgets["transition"][0].image,
                                          self.special_widgets["transition"][0].rect)
            # endregion
            # region Display Resizing
            self.resized_surface = resize_surf(self.display_surface, self.current_resolution)
            self.display.fill(self.rainbow.get_color() if self.rainbow_mode else BLACK)
            self.blit_resized_surface(self.display, self.resized_surface)
            # endregion
            pygame.display.update()
        pygame.quit()

    def init_menu_frame(self) -> None:
        font = pygame.font.Font(normpath("Fonts/Arial/normal.ttf"), 35)
        self.display_frame = Widgets.Frame(0, 0, self.fixed_resolution[0], self.fixed_resolution[1], 20, z_index=4)
        # region Vertical Buttons
        widget_labels = ["Start Game", "How to Play", "Achievements"]
        widget_sizes = [(260, 69), (280, 69), (300, 69)]
        widget_data = []
        widget_callbacks = [self.schedule_start_game, lambda: None, lambda: None]
        for size in widget_sizes:
            size = list(Widgets.Button.calc_size(0, size[0], size[1]))
            size[0] = abs(size[0])
            size[1] += size[0]
            widget_data.append(size)
        padding = 10
        total_height = sum(size[1] for size in widget_data) + (len(widget_data) - 1) * padding
        start_y = self.fixed_resolution[1] / 2 - total_height / 2
        offset_y = 0
        button_id = 1
        for index in range(len(widget_labels)):
            self.display_frame.add_widget(
                Widgets.Button(self.fixed_resolution[0] / 2 - widget_sizes[index][0] / 2,
                               start_y + offset_y + widget_data[index][0], widget_sizes[index][0],
                               widget_sizes[index][1], 1, BLACK, ORANGE, font, widget_labels[index],
                               widget_callbacks[index], widget_name="!button{}".format(button_id))
            )
            offset_y += widget_data[index][1] + padding
            button_id += 1
        # endregion
        # region Horizontal Buttons
        button_id = 1
        widen_amount = 20
        widget_surfaces = [pygame.Surface((65, 65)), pygame.Surface((65, 65))]
        widget_callbacks = [self.schedule_launch_settings, self.toggle_full_screen]
        widget_data = []
        for surf in widget_surfaces:
            size = list(Widgets.Button.calc_size(0, *surf.get_size(), widen_amount=widen_amount))
            size[0] = abs(size[0])
            size[1] += size[0]
            widget_data.append(size)
        total_width = (sum(surface.get_width() + widen_amount for surface in widget_surfaces)
                       + (len(widget_surfaces) - 1) * padding)
        max_height = max(size[1] for size in widget_data)
        start_x = self.fixed_resolution[0] - padding - total_width
        offset_x = 0
        for index in range(len(widget_surfaces)):
            self.display_frame.add_widget(
                Widgets.AnimatedSurface(start_x + offset_x + widen_amount / 2,
                                        (self.fixed_resolution[1] - padding - max_height
                                         + (max_height / 2 - widget_data[index][1] / 2) + widget_data[index][0]),
                                        widget_surfaces[index], widget_callbacks[index], widen_amount=widen_amount,
                                        widget_name="!animated_surf{}".format(button_id))
            )
            offset_x += widget_surfaces[index].get_width() + widen_amount + padding
            button_id += 1
        # endregion

    def schedule_start_game(self) -> None:
        if "transition" not in self.special_widgets:
            self.special_widgets["transition"] = [(self.fixed_resolution[0], self.fixed_resolution[1], 400),
                                                  self.init_game]

    def schedule_launch_settings(self) -> None:
        if "settings" not in self.special_widgets:
            widget_size = (375, 250)
            padding = 20
            self.special_widgets["settings"] = [(self.display_surface, self.fixed_resolution, widget_size, 19, 19, 10,
                                                 4, 0.05, widget_size[0] - 2 * padding, self.volume, 3), None]

    def init_game(self) -> None:
        if self.state_data.game_state == "menu":
            self.display_frame = Widgets.Frame(0, 0, self.fixed_resolution[0], self.fixed_resolution[1], 20, z_index=4)
            self.bird.spawn_bird(self.state_data, self.tiles_group)

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

    @staticmethod
    def check_key_sequence(sequence_obj: Keyboard.KeySequence,
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
            self.audio_objects["rickroll"].stop()
        else:
            self.audio_objects["rickroll"].play()
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
        configure_dpi()
        MainProc()
    else:
        print("This game requires Pygame version 2.0.1 or higher to run. Consider updating your version of Pygame "
              "with the command: 'python -m pip install --upgrade pygame'")
