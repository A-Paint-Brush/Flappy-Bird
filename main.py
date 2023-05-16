from functools import partial
from os.path import normpath
from Global import *
import Mouse
import Widgets
import Dialogs
import Ground
import Bird
import Pipe
import Rainbow
import Keyboard
import Notifier
import Storage
import Counters
import pygame


class MainThread:
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
        self.game_state: Literal["menu", "waiting", "started", "dying", "help", "achievements", "results"] = "menu"
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
        self.font = pygame.font.Font(normpath("./Fonts/Arial/normal.ttf"), 35)
        self.special_widgets: Dict[Literal["transition", "settings", "pause", "send_score"], List[Any]] = {}
        self.busy_frame = Dialogs.BusyFrame(self.fixed_resolution, self.font, 100, 125, 19, 90, 250, (205, 205, 205),
                                            (26, 134, 219))
        self.ui_mgr: Optional[Union[Dialogs.HelpManager, Dialogs.LoseScreen, Dialogs.AchievementManager]] = None
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
        self.listen_events = (pygame.QUIT, pygame.WINDOWFOCUSLOST, pygame.WINDOWENTER, pygame.WINDOWLEAVE,
                              pygame.VIDEORESIZE, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEWHEEL,
                              pygame.KEYDOWN, pygame.KEYUP, pygame.TEXTINPUT, pygame.TEXTEDITING)
        pygame.event.set_blocked(None)
        pygame.event.set_allowed(self.listen_events)
        pygame.key.stop_text_input()
        # endregion
        # region Game Objects
        self.background = pygame.image.load(normpath("./Images/Sprites/background.png")).convert_alpha()
        self.mouse_obj = Mouse.Cursor()
        # Object z-orders = 1: toast-group, 2: transition, 3: top-level windows, 4: widget-frame, 5: bird (final)
        self.bird = Bird.BirdManager(self.fixed_resolution, z_index=5)
        self.tiles_group = Ground.GroundGroup(self.fixed_resolution)
        self.font_height = 50
        self.kerning = 5
        self.pipe_group = Pipe.PipeGroup(self.fixed_resolution, self.tiles_group.get_size(), self.font_height,
                                         self.kerning)
        self.notifiers = Notifier.ToastGroup(self.fixed_resolution, z_index=1)
        self.achievement_list = Storage.AchievementData()
        self.achievement_db = Storage.AchievementDB(self.achievement_list.get_achievement_len())
        data = self.achievement_db.read_data()
        if data is None:
            self.achievement_db.set_achievement(-1)
            error_message = "An OS error occurred while attempting to read user achievement data. Please ensure that "\
                            "this application has both read and write permission to the directory '{}'."\
                            .format(self.achievement_db.parent_dir)
            raise RuntimeError(error_message)
        self.achievement_list.load_achievements(data, self.achievement_db.set_achievement)
        self.rainbow = Rainbow.Rainbow()
        self.fps_counter = Counters.FPS(self.fixed_resolution)
        # endregion
        # region Timing Control
        self.fps = 90
        self.clock = pygame.time.Clock()
        # endregion
        while self.game_run:
            self.clock.tick(self.fps)
            self.key_events.clear()
            self.mouse_obj.reset_scroll()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.achievement_db.set_achievement(-1)
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
                        if event.key == pygame.K_ESCAPE and self.full_screen:
                            self.toggle_full_screen()
                        if self.game_state in ("waiting", "started") and \
                                "transition" not in self.special_widgets and \
                                "pause" not in self.special_widgets:
                            if event.key == pygame.K_SPACE:
                                self.bird.process_user_events(self.access_game_state, self.pipe_group, self.mouse_obj,
                                                              False)
                            elif event.key == pygame.K_p:
                                self.schedule_pause_game()
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
            elif "pause" in self.special_widgets and isinstance(self.special_widgets["pause"][0], tuple):
                self.special_widgets["pause"][0] = Dialogs.Pause(*self.special_widgets["pause"][0])
            elif "send_score" in self.special_widgets and isinstance(self.special_widgets["send_score"][0], tuple):
                self.special_widgets["send_score"][0] = Dialogs.SubmitScore(*self.special_widgets["send_score"][0])
                if tuple(self.current_resolution) != self.fixed_resolution:
                    self.update_window_ime_size()
            # The z-index will not be increased if the mouse touches any toasts.
            self.notifiers.send_mouse_pos(self.mouse_obj)
            if "transition" in self.special_widgets:
                return_code = self.special_widgets["transition"][0].update()
                if return_code == 1:
                    self.special_widgets["transition"][1]()
                elif return_code == 2:
                    self.special_widgets.pop("transition")
            else:
                self.mouse_obj.increment_z_index()
            show_load = False
            if self.game_state == "help":
                self.ui_mgr.update()
                if self.ui_mgr.is_loading():
                    show_load = True
                    self.mouse_obj.reset_z_index()
            elif self.game_state == "results":
                status = self.ui_mgr.update()
                if status != "done":
                    show_load = True
                    self.mouse_obj.reset_z_index()
                    if status == "fetch_done" and self.ui_mgr.check_record_score():
                        self.schedule_submit_score()
            key: Optional[Literal["settings", "pause", "send_score"]] = None
            if "settings" in self.special_widgets:
                key = "settings"
            elif "pause" in self.special_widgets:
                key = "pause"
            elif "send_score" in self.special_widgets and isinstance(self.special_widgets["send_score"][0],
                                                                     Dialogs.SubmitScore):
                key = "send_score"
            else:
                self.mouse_obj.increment_z_index()
            if key is not None:
                return_code = self.special_widgets[key][0].update(self.mouse_obj, self.key_events)
                if key in ("settings", "pause"):
                    new_volume = self.special_widgets[key][0].get_volume()
                    if new_volume != self.volume:
                        self.volume = new_volume
                        volume_float = self.volume / 100
                        for sound in self.audio_objects.values():
                            sound.set_volume(volume_float)
                if return_code:
                    self.special_widgets.pop(key)
                    if key == "pause":
                        self.unpause_game()
            if self.display_frame is None:
                self.mouse_obj.increment_z_index()
            else:
                # The mouse will only be able to interact with the widgets if it did not touch any toasts.
                self.display_frame.update(self.mouse_obj, self.key_events)
            if "pause" not in self.special_widgets:
                if self.game_state in ("menu", "help", "achievements", "results"):
                    self.tiles_group.move()
                    self.tiles_group.reset_pos()
                elif self.game_state in ("waiting", "started", "dying"):
                    self.bird.process_user_events(self.access_game_state, self.pipe_group, self.mouse_obj, True)
                    self.bird.update(self.tiles_group, self.pipe_group, self.access_game_state, self.init_dying_frame,
                                     self.schedule_game_over)
            if self.rainbow_mode:
                self.rainbow.tick()
            self.fps_counter.tick()
            self.notifiers.update()  # Does nothing if there are no toast notifications.
            # endregion
            # region Screen Rendering
            self.display_surface.fill(BLACK)
            self.display_surface.blit(self.background, (0, 0))
            self.tiles_group.draw(self.display_surface)
            if self.game_state in ("started", "dying"):
                self.pipe_group.draw(self.display_surface)
                if self.debug:
                    self.pipe_group.draw_hit_box(self.display_surface)
            if self.game_state in ("waiting", "started", "dying"):
                self.bird.advanced_draw(self.display_surface, self.debug)  # For debug mode support.
                score_obj = self.pipe_group.get_score_obj()
                size = score_obj.calc_size()
                score_obj.draw(self.display_surface, (self.fixed_resolution[0] / 2 - size[0] / 2, 20))
            if self.game_state == "results":
                # Render score on results screen.
                self.pipe_group.get_score_obj().draw(self.display_surface, self.ui_mgr.get_score_position())
            if self.debug:
                self.fps_counter.draw(self.display_surface)
            if self.display_frame is not None:
                self.display_surface.blit(self.display_frame.image, self.display_frame.rect)
            if "settings" in self.special_widgets and isinstance(self.special_widgets["settings"][0],
                                                                 Dialogs.Settings):
                self.special_widgets["settings"][0].draw()
            elif "pause" in self.special_widgets and isinstance(self.special_widgets["pause"][0], Dialogs.Pause):
                self.special_widgets["pause"][0].draw()
            elif "send_score" in self.special_widgets and isinstance(self.special_widgets["send_score"][0],
                                                                     Dialogs.SubmitScore):
                self.special_widgets["send_score"][0].draw()
            if show_load:
                self.busy_frame.update(self.mouse_obj, self.key_events)
                self.busy_frame.draw(self.display_surface)
            if "transition" in self.special_widgets and isinstance(self.special_widgets["transition"][0],
                                                                   Widgets.SceneTransition):
                self.display_surface.blit(self.special_widgets["transition"][0].image,
                                          self.special_widgets["transition"][0].rect)
            self.notifiers.draw(self.display_surface)  # Draws nothing if empty.
            # endregion
            # region Display Resizing
            self.resized_surface = resize_surf(self.display_surface, self.current_resolution)
            self.display.fill(self.rainbow.get_color() if self.rainbow_mode else BLACK)
            self.blit_resized_surface(self.display, self.resized_surface)
            # endregion
            pygame.display.update()
        pygame.quit()

    def access_game_state(self, new_state: Optional[str] = None) -> Optional[str]:
        if new_state is None:
            return self.game_state
        else:
            self.game_state = new_state

    def init_menu_frame(self) -> None:
        if self.game_state in ("help", "achievements", "results"):
            self.ui_mgr = None
            if self.game_state == "results":
                self.reset_unusable_objects()
        if "pause" in self.special_widgets:
            self.unpause_game()
            self.special_widgets.pop("pause")
            self.reset_unusable_objects()
        self.game_state = "menu"
        self.display_frame = Widgets.Frame(0, 0, self.fixed_resolution[0], self.fixed_resolution[1], 20, z_index=4)
        # region Vertical Buttons
        widget_labels = ["Start Game", "How to Play", "Achievements"]
        widget_sizes = [(260, 69), (280, 69), (300, 69)]
        widget_callbacks = [partial(self.schedule_toggle_round, "game"), self.schedule_show_help,
                            self.schedule_show_achievements]
        padding = 10
        Dialogs.v_pack_buttons(self.fixed_resolution, self.display_frame, widget_labels, widget_sizes,
                               widget_callbacks, self.font, padding)
        # endregion
        # region Horizontal Buttons
        widen_amount = 20
        widget_surfaces = [pygame.Surface((65, 65)), pygame.Surface((65, 65))]
        widget_callbacks = [self.schedule_launch_settings, self.toggle_full_screen]
        Dialogs.h_pack_buttons_se(self.fixed_resolution, self.display_frame, widget_surfaces, widget_callbacks,
                                  padding, widen_amount)
        # endregion

    def init_game_frame(self) -> None:
        if self.game_state == "results":
            self.game_state = "menu"
            self.ui_mgr = None
            self.reset_unusable_objects()
        if self.game_state == "menu":
            self.display_frame = Widgets.Frame(0, 0, self.fixed_resolution[0], self.fixed_resolution[1], 20, z_index=4)
            padding = 10
            widen_amount = 20
            widget_surfaces = [pygame.Surface((65, 65))]
            widget_callbacks = [self.schedule_pause_game]
            Dialogs.h_pack_buttons_se(self.fixed_resolution, self.display_frame, widget_surfaces, widget_callbacks,
                                      padding, widen_amount)
            self.bird.spawn_bird(self.access_game_state, self.tiles_group)

    def init_dying_frame(self) -> None:
        if self.game_state == "dying":
            self.display_frame = None

    def init_help_frame(self) -> None:
        self.display_frame = Widgets.Frame(0, 0, self.fixed_resolution[0], self.fixed_resolution[1], 20, z_index=4)
        self.busy_frame.reset_animation()
        self.ui_mgr = Dialogs.HelpManager(self.display_frame, self.fixed_resolution, self.font, self.schedule_exit_help)
        self.game_state = "help"

    def init_achievements_frame(self) -> None:
        self.display_frame = Widgets.Frame(0, 0, self.fixed_resolution[0], self.fixed_resolution[1], 20, z_index=4)
        heading_font = pygame.font.Font(normpath("./Fonts/Arial/bold.ttf"), 25)
        body_font = pygame.font.Font(normpath("./Fonts/Arial/normal.ttf"), 23)
        self.ui_mgr = Dialogs.AchievementManager(self.display_frame, self.fixed_resolution, self.font, heading_font,
                                                 body_font, self.achievement_list.get_achievement_string,
                                                 partial(self.schedule_toggle_round, "menu"))
        self.ui_mgr.update_data(self.achievement_list.get_state_data())
        self.game_state = "achievements"

    def init_results_screen(self) -> None:
        self.display_frame = Widgets.Frame(0, 0, self.fixed_resolution[0], self.fixed_resolution[1], 20, z_index=4)
        self.busy_frame.reset_animation()
        self.ui_mgr = Dialogs.LoseScreen(self.display_frame, self.fixed_resolution, self.pipe_group.get_score_obj(),
                                         [partial(self.schedule_toggle_round, "game"),
                                          partial(self.schedule_toggle_round, "menu")],
                                         partial(self.achievement_db.set_achievement, -1))
        self.ui_mgr.start_fetch_data()
        self.game_state = "results"

    def schedule_toggle_round(self, target: Literal["menu", "game"]) -> None:
        if "transition" not in self.special_widgets:
            self.special_widgets["transition"] = [(self.fixed_resolution[0], self.fixed_resolution[1], 400),
                                                  self.init_game_frame if target == "game"
                                                  else self.init_menu_frame]

    def schedule_show_help(self) -> None:
        if "transition" not in self.special_widgets:
            self.special_widgets["transition"] = [(self.fixed_resolution[0], self.fixed_resolution[1], 400),
                                                  self.init_help_frame]

    def schedule_show_achievements(self):
        if "transition" not in self.special_widgets:
            self.special_widgets["transition"] = [(self.fixed_resolution[0], self.fixed_resolution[1], 400),
                                                  self.init_achievements_frame]

    def schedule_exit_help(self) -> None:
        if "transition" not in self.special_widgets:
            self.special_widgets["transition"] = [(self.fixed_resolution[0], self.fixed_resolution[1], 400),
                                                  self.init_menu_frame]

    def schedule_launch_settings(self) -> None:
        if "settings" not in self.special_widgets:
            widget_size = (375, 250)
            padding = 20
            self.special_widgets["settings"] = [(self.display_surface, self.fixed_resolution, widget_size, 19, 19, 10,
                                                 4, 0.05, widget_size[0] - 2 * padding, self.volume, 3)]

    def schedule_pause_game(self) -> None:
        if "pause" not in self.special_widgets and self.game_state in ("waiting", "started"):
            widget_size = (375, 250)
            padding = 20
            self.special_widgets["pause"] = [(self.display_surface, self.fixed_resolution, widget_size, 19, 19, 10, 4,
                                              0.05, widget_size[0] - 2 * padding, self.volume,
                                              [partial(self.schedule_toggle_round, "menu"),
                                               self.toggle_full_screen], 3)]
            self.pause_game()

    def schedule_submit_score(self) -> None:
        if "send_score" not in self.special_widgets and self.game_state == "results":
            widget_size = (460, 360)
            padding = 20
            self.special_widgets["send_score"] = [(self.display_surface, self.fixed_resolution, widget_size, 19, 19, 10,
                                                   4, 0.05, widget_size[0] - 2 * padding, self.submit_score, 3)]

    def submit_score(self, player_name: str) -> None:
        if self.game_state == "results":
            self.ui_mgr.start_write_data(player_name)

    def schedule_game_over(self) -> None:
        if self.game_state == "dying":
            self.special_widgets["transition"] = [(self.fixed_resolution[0], self.fixed_resolution[1], 400),
                                                  self.init_results_screen]

    def reset_unusable_objects(self) -> None:
        self.bird = Bird.BirdManager(self.fixed_resolution, z_index=5)
        self.pipe_group = Pipe.PipeGroup(self.fixed_resolution, self.tiles_group.get_size(), self.font_height,
                                         self.kerning)

    def pause_game(self) -> None:
        self.bird.pause()
        self.tiles_group.pause()
        self.pipe_group.pause_flash()

    def unpause_game(self) -> None:
        self.bird.unpause()
        self.tiles_group.unpause()
        self.pipe_group.unpause_flash()

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
        self.update_window_ime_size()

    def update_window_ime_size(self) -> None:
        if self.game_state == "results" and "send_score" in self.special_widgets and \
                isinstance(self.special_widgets["send_score"][0], Dialogs.SubmitScore):
            self.special_widgets["send_score"][0].window_resize_event(self.current_resolution,
                                                                      resize_surf(self.display_surface,
                                                                                  self.current_resolution,
                                                                                  size_only=True))

    def check_key_sequence(self, sequence_obj: Keyboard.KeySequence, key_code: int,
                           callback: Callable[[], None]) -> None:
        result = sequence_obj.push_key(key_code)
        if result:
            callback()
            if self.game_state == "achievements":
                self.ui_mgr.update_data(self.achievement_list.get_state_data())

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


if __name__ == "__main__":
    if pygame.version.vernum >= (2, 0, 1):
        configure_dpi()
        MainThread()
    else:
        print("This game requires Pygame version 2.0.1 or higher to run. Consider updating your version of Pygame "
              "with the command: 'python -m pip install --upgrade pygame'")
