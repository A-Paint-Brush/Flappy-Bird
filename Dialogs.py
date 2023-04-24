from collections import namedtuple
from os.path import normpath
from Global import *
import Storage
import Widgets
import pygame
if TYPE_CHECKING:
    import Mouse


def v_pack_buttons(container_size: Tuple[int, int], widget_frame: Widgets.Frame, widget_labels: List[str],
                   widget_sizes: List[Tuple[int, int]], widget_callbacks: List[Callable[[], None]],
                   font: pygame.font.Font, padding: int, start_y: Optional[int] = None,
                   start_id: int = 1) -> Tuple[int, int]:
    """Vertically stack a group of buttons on the same column. Each button will be horizontally centered, and the
    amount of vertical padding between each button will be uniform. The column of buttons will also be vertically
    centered within the height of the container area, unless a value is passed to the 'start_y' parameter, in which case
    the top of the column will be positioned at the y value given. Returns a two-item tuple with the first item being
    the value the widget-ID counter should be updated to, and the second being the total height of the buttons."""
    widget_data = []
    for s in widget_sizes:
        size = list(Widgets.Button.calc_size(0, s[0], s[1]))
        size[0] = abs(size[0])
        size[1] += size[0]
        widget_data.append(size)
    total_height = sum(size[1] for size in widget_data) + (len(widget_data) - 1) * padding
    start_y = container_size[1] / 2 - total_height / 2 if start_y is None else start_y
    offset_y = 0
    button_id = start_id
    for index in range(len(widget_labels)):
        widget_frame.add_widget(
            Widgets.Button(container_size[0] / 2 - widget_sizes[index][0] / 2,
                           start_y + offset_y + widget_data[index][0], widget_sizes[index][0],
                           widget_sizes[index][1], 1, BLACK, ORANGE, font, widget_labels[index],
                           widget_callbacks[index], widget_name="!button{}".format(button_id))
        )
        offset_y += widget_data[index][1] + padding
        button_id += 1
    return button_id, offset_y


def h_pack_buttons_se(container_size: Tuple[int, int], widget_frame: Widgets.Frame,
                      widget_surfaces: List[pygame.Surface], widget_callbacks: List[Callable[[], None]],
                      padding: int, widen_amount: int, start_y: Optional[int] = None,
                      start_id: int = 1) -> Tuple[int, int]:
    """Create a row of buttons that is positioned in the bottom-right corner of the container. The bottom side of the
    row of buttons will be one padding away from the bottom border of the container, unless a y position is given by the
    caller. The amount of horizontal padding between each button will be uniform. Each button will be vertically
    centered within the height of the tallest button in the row. Returns a two-item tuple with the first item being
    the value the widget-ID counter should be updated to, and the second being the height of the tallest button."""
    widget_data = []
    for surf in widget_surfaces:
        size = list(Widgets.Button.calc_size(0, *surf.get_size(), widen_amount=widen_amount))
        size[0] = abs(size[0])
        size[1] += size[0]
        widget_data.append(size)
    total_width = (sum(surface.get_width() + widen_amount for surface in widget_surfaces)
                   + (len(widget_surfaces) - 1) * padding)
    max_height = max(size[1] for size in widget_data)
    start_x = container_size[0] - padding - total_width
    offset_x = 0
    button_id = start_id
    for index in range(len(widget_surfaces)):
        widget_frame.add_widget(
            Widgets.AnimatedSurface(start_x + offset_x + widen_amount / 2,
                                    ((container_size[1] - padding - max_height if start_y is None else start_y)
                                     + (max_height / 2 - widget_data[index][1] / 2) + widget_data[index][0]),
                                    widget_surfaces[index], widget_callbacks[index], widen_amount=widen_amount,
                                    widget_name="!animated_surf{}".format(button_id))
        )
        offset_x += widget_surfaces[index].get_width() + widen_amount + padding
        button_id += 1
    return button_id, max_height + padding


class BaseDialog:
    def __init__(self, surface: pygame.Surface, resolution: Tuple[int, int], max_window_size: Tuple[int, int],
                 border_radius: int, button_length: int, button_padding: int, button_thickness: int,
                 animation_speed: Union[int, float], max_widget_width: int, z_index: int = 1):
        """Base class for all dialogs. If the height that the content of the dialog occupies is less than the value
        given in the 'max_window_size' parameter, the dialog's height will be shortened to fit the contents, or else a
        scrollbar is added to the content area."""
        self.surface = surface
        self.resolution = resolution
        self.border_radius = border_radius
        self.button_length = button_length
        self.button_padding = button_padding
        self.button_thickness = button_thickness
        self.animation_speed = animation_speed
        self.z_index = z_index
        self.small_font = pygame.font.Font(normpath("Fonts/Arial/normal.ttf"), 25)
        self.large_font = pygame.font.Font(normpath("Fonts/Arial/normal.ttf"), 35)
        self.height_difference = self.border_radius * 2 + button_length + button_padding
        self.frame_size = [max_window_size[0] - self.border_radius * 2,
                           max_window_size[1] - self.height_difference]
        self.max_window_size = max_window_size
        self.scrollbar_width = 20
        self.max_widget_width = max_widget_width - self.border_radius * 2
        self.content_width = self.frame_size[0]
        self.widget_id = 1
        self.accumulated_y = 0
        self.content_frame = Widgets.Frame(0, 0, self.frame_size[0], self.frame_size[1], 20, z_index)
        self.window = None  # The size of the window cannot be determined until all widgets are added.

    def h_shift_widgets(self, amount: Union[int, float]) -> None:
        for widget in self.content_frame.child_widgets.values():
            if isinstance(widget, Widgets.ScrollBar):  # The scrollbar should not be moved.
                continue
            if isinstance(widget, Widgets.AnimatedSurface):
                # Children of 'AnimatedSurface' use 'real_x' instead of 'x' to store the x pos given on initialization.
                widget.real_x += amount
            else:
                widget.x += amount
                # Widgets that don't subclass 'AnimatedSurface' only update the rect on initialization. Therefore, it is
                # necessary to manually update the rect.
            widget.rect.move_ip(amount, 0)

    def create_label(self, text: str, padding: int, font: pygame.font.Font) -> None:
        label = Widgets.Label(self.content_width / 2 - self.max_widget_width / 2, self.accumulated_y, text, BLACK,
                              self.max_widget_width, font, widget_name="!label{}".format(self.widget_id))
        self.content_frame.add_widget(label)
        self.accumulated_y += label.rect.height + padding
        self.widget_id += 1

    def create_slider(self, text_height: int, max_value: int, thumb_width: int, text_padding: int,
                      widget_padding: int) -> Widgets.Slider:
        text_size = self.large_font.size(str(max_value))
        max_text_width = text_height * (text_size[0] / text_size[1])
        widget_size = namedtuple("slider_args", ["text_height", "line_length", "thumb_width", "thumb_height", "font",
                                                 "max_value",
                                                 "text_padding"])(text_height=text_height,
                                                                  line_length=round(self.max_widget_width
                                                                                    - max_text_width - text_padding
                                                                                    - thumb_width),
                                                                  thumb_width=thumb_width, thumb_height=38,
                                                                  font=self.large_font, max_value=max_value,
                                                                  text_padding=text_padding)
        widget_data = Widgets.Slider.calc_size(*widget_size)
        slider = Widgets.Slider(round(self.content_width / 2 - widget_data[0] / 2), self.accumulated_y,
                                widget_size.text_height, BLACK, widget_size.line_length, 5, (250, 50, 50),
                                (0, 255, 0), widget_size.thumb_width, widget_size.thumb_height, (0, 130, 205),
                                (155, 205, 0), widget_size.font, 0, widget_size.max_value,
                                widget_name="!slider{}".format(self.widget_id))
        self.content_frame.add_widget(slider)
        self.accumulated_y += widget_data[1] + widget_padding
        self.widget_id += 1
        return slider

    def fit_to_content(self) -> None:
        if self.content_frame.get_content_height() > self.frame_size[1]:
            self.max_widget_width -= self.scrollbar_width
            self.content_width -= self.scrollbar_width
            self.h_shift_widgets(self.scrollbar_width / -2)
            self.content_frame.add_widget(Widgets.ScrollBar(width=self.scrollbar_width))
        else:
            self.frame_size[1] = self.content_frame.get_content_height()
            # The frame's size now has to be forcibly updated.
            self.content_frame.height = self.frame_size[1]
            # Updating the rect is not necessary as it'll be updated by the parent window.
        self.window = Widgets.Window(self.resolution[0] / 2 - self.max_window_size[0] / 2, self.resolution[1],
                                     self.resolution[1] / 2 - (self.frame_size[1] + self.height_difference) / 2, GREEN,
                                     100, RED, GREY6, self.border_radius, self.button_length, self.button_padding,
                                     self.button_thickness, self.animation_speed, self.content_frame, self.surface,
                                     self.z_index)

    def update(self, mouse_obj: "Mouse.Cursor", keyboard_events: List[pygame.event.Event]) -> bool:
        return self.window.update(mouse_obj, keyboard_events)

    def draw(self) -> None:
        self.window.draw()


class Settings(BaseDialog):
    def __init__(self, surface: pygame.Surface, resolution: Tuple[int, int], max_window_size: Tuple[int, int],
                 border_radius: int, button_length: int, button_padding: int, button_thickness: int,
                 animation_speed: Union[int, float], max_widget_width: int, current_volume: int, z_index: int = 1):
        super().__init__(surface, resolution, max_window_size, border_radius, button_length, button_padding,
                         button_thickness, animation_speed, max_widget_width, z_index)
        vertical_padding = 20
        self.create_label("Settings", vertical_padding, self.large_font)
        self.create_label("Volume", vertical_padding, self.small_font)
        self.slider = self.create_slider(31, 100, 13, 10, vertical_padding)
        self.slider.set_slider_value(current_volume)
        self.fit_to_content()  # Adds a scrollbar if the content height exceeds the frame height.

    def get_volume(self) -> int:
        return self.slider.get_slider_value()


class Pause(BaseDialog):
    def __init__(self, surface: pygame.Surface, resolution: Tuple[int, int], max_window_size: Tuple[int, int],
                 border_radius: int, button_length: int, button_padding: int, button_thickness: int,
                 animation_speed: Union[int, float], max_widget_width: int, current_volume: int,
                 callbacks: List[Callable[[], None]], z_index: int = 1):
        super().__init__(surface, resolution, max_window_size, border_radius, button_length, button_padding,
                         button_thickness, animation_speed, max_widget_width, z_index)
        vertical_padding = 20
        self.create_label("Paused", vertical_padding // 3, self.large_font)
        data = v_pack_buttons((max_widget_width, 0), self.content_frame,
                              ["Main Menu"],
                              [(178, 51)],
                              [callbacks[0]],
                              self.large_font, vertical_padding // 3, self.accumulated_y, self.widget_id)
        self.widget_id = data[0]
        self.accumulated_y += data[1] + vertical_padding
        self.create_label("Volume", vertical_padding, self.small_font)
        self.slider = self.create_slider(31, 100, 13, 10, vertical_padding // 2)
        self.slider.set_slider_value(current_volume)
        data = h_pack_buttons_se((max_widget_width, 0), self.content_frame,
                                 [pygame.Surface((65, 65))],
                                 [callbacks[1]],
                                 vertical_padding, 20, self.accumulated_y, self.widget_id)
        self.widget_id = data[0]
        self.accumulated_y += data[1]
        self.fit_to_content()

    def get_volume(self) -> int:
        return self.slider.get_slider_value()


class HelpManager:
    def __init__(self, parent_frame: Widgets.Frame, resolution: Tuple[int, int], font: pygame.font.Font,
                 callback: Callable[[], None]):
        # This class should handle all UI events. Should contain a method that returns a boolean indicating whether the
        # loading animation should continue to be shown.
        self.parent_frame = parent_frame
        self.resolution = resolution
        self.loading = True
        self.font = font
        self.line_height = font.size("█")[1]
        self.padding = 15
        # region Page Controls
        widen_amount = 60
        original_size = (260, 69)
        offset_data, true_size = self.calc_button_data(widen_amount, original_size)
        self.footer_height = true_size[1]
        prev_btn = Widgets.Button(self.padding + widen_amount / 2,
                                  self.resolution[1] - self.padding - true_size[1] + abs(offset_data[0]),
                                  original_size[0], original_size[1], 1, BLACK, ORANGE, self.font, "Prev Page",
                                  self.prev_page, widen_amount=widen_amount, widget_name="!prev_btn")
        self.parent_frame.add_widget(prev_btn)
        next_btn = Widgets.Button(self.resolution[0] - self.padding - true_size[0] + widen_amount / 2,
                                  self.resolution[1] - self.padding - true_size[1] + abs(offset_data[0]),
                                  original_size[0], original_size[1], 1, BLACK, ORANGE, self.font, "Next Page",
                                  self.next_page, widen_amount=widen_amount, widget_name="!next_btn")
        self.parent_frame.add_widget(next_btn)
        # endregion
        # region Header Frame
        widen_amount = 45
        original_size = (173, 69)
        offset_data, true_size = self.calc_button_data(widen_amount, original_size)
        self.header_height = max(true_size[1], self.line_height)
        back_btn = Widgets.Button(self.padding + widen_amount / 2,
                                  self.padding + (self.header_height / 2 - true_size[1] / 2) + abs(offset_data[0]),
                                  original_size[0], original_size[1], 1, BLACK, ORANGE, self.font, "◄ Back",
                                  callback, widen_amount=widen_amount, widget_name="!back_btn")
        self.parent_frame.add_widget(back_btn)
        # endregion
        # region Page System
        self.text_rect = pygame.Rect(self.padding, 2 * self.padding + self.header_height,
                                     self.resolution[0] - 2 * self.padding,
                                     self.resolution[1] - 4 * self.padding - self.footer_height - self.header_height)
        self.lines_per_page = self.text_rect.height // self.line_height
        self.wrapped_lines = []
        self.page = 0
        self.max_page = -1
        self.page_string = "Page {} of {}"
        self.help_data = Storage.HelpFile()
        # endregion

    @staticmethod
    def calc_button_data(widen_amount: int, original_size: Tuple[int, int]) -> Tuple[Tuple[float, float],
                                                                                     Tuple[int, float]]:
        offset_data = Widgets.Button.calc_size(0, original_size[0], original_size[1], widen_amount=widen_amount)
        true_size = (original_size[0] + widen_amount, abs(offset_data[0]) + offset_data[1])
        return offset_data, true_size

    def update(self) -> None:
        if self.loading:
            if not self.help_data.is_running():
                self.loading = False
                self.init_page_sys()

    def init_page_sys(self) -> None:
        self.wrapped_lines = word_wrap_text(self.help_data.get_data().strip("\n"), self.text_rect.width, self.font)
        filled_pages, extra_lines = divmod(len(self.wrapped_lines), self.lines_per_page)
        self.max_page = filled_pages - (not extra_lines)  # filled_pages - 1 if extra_lines is non-zero.
        self.update_text_widget(True)

    def update_text_widget(self, first_update: bool = False) -> None:
        if not first_update:
            self.parent_frame.delete_widget("!page_num")
            self.parent_frame.delete_widget("!help_text")
        page_num_display = Widgets.Label(self.resolution[0] / 2,
                                         self.padding + (self.header_height / 2 - self.line_height / 2),
                                         self.page_string.format(self.page + 1, self.max_page + 1), BLACK,
                                         round(self.resolution[0] / 2), self.font, widget_name="!page_num")
        self.parent_frame.add_widget(page_num_display)
        text_widget = Widgets.Label(self.text_rect.x, self.text_rect.y,
                                    self.wrapped_lines[self.page * self.lines_per_page:
                                                       (self.page + 1) * self.lines_per_page],
                                    BLACK, self.text_rect.width, self.font, align="left", no_wrap=True,
                                    widget_name="!help_text")
        self.parent_frame.add_widget(text_widget)

    def next_page(self) -> None:
        if self.page < self.max_page:
            self.page += 1
            self.update_text_widget()

    def prev_page(self) -> None:
        if self.page > 0:
            self.page -= 1
            self.update_text_widget()

    def is_loading(self) -> bool:
        return self.loading


class BusyFrame:
    def __init__(self, resolution: Tuple[int, int], font: pygame.font.Font, alpha: int, size: int, thickness: int,
                 lit_length: int, speed: Union[int, float], unlit_color: Tuple[int, int, int],
                 lit_color: Tuple[int, int, int]):
        padding = 20
        self.widgets: Dict[str, Optional[Union[Widgets.BaseWidget,
                                               Widgets.BaseOverlay]]] = {}
        self.z_order: List[str] = []
        label = Widgets.Label(0, 0, "Loading...", WHITE, resolution[0] - 2 * padding, font)
        frame_height = size + padding + label.get_size()[1]
        frame_y = resolution[1] / 2 - frame_height / 2
        label.update_position(resolution[0] / 2 - label.get_size()[0] / 2, frame_y + size + padding)
        self.spinner_args = (resolution[0] / 2 - size / 2, frame_y, size, thickness, lit_length, speed, unlit_color,
                             lit_color)
        overlay = Widgets.BaseOverlay(*resolution)
        overlay.image.set_alpha(alpha)
        self.add_widget("overlay", overlay)
        self.add_widget("spinner", None)
        self.add_widget("label", label)
        self.reset_animation()

    def add_widget(self, widget_id: str, widget_obj: Optional[Union[Widgets.BaseWidget, Widgets.BaseOverlay]]) -> None:
        self.widgets[widget_id] = widget_obj
        self.z_order.append(widget_id)

    def reset_animation(self) -> None:
        """Resets the loading animation."""
        self.widgets["spinner"] = Widgets.Spinner(*self.spinner_args)

    def update(self, mouse_obj: "Mouse.Cursor", keyboard_events: List[pygame.event.Event]) -> None:
        # 'Spinner' is the only widget in this class that needs to be updated.
        # 'BaseOverlay' does not have an update method, and the update method of 'Label' only runs 'pass'.
        self.widgets["spinner"].update(mouse_obj, keyboard_events)

    def draw(self, surface: pygame.Surface) -> None:
        for w in self.z_order:
            surface.blit(self.widgets[w].image, self.widgets[w].rect)
