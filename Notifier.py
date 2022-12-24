from os.path import normpath
from Global import *
import Physics
import Mouse
import Time
import pygame


class ToastNotifier(pygame.sprite.Sprite):
    def __init__(self, resolution: Tuple[int, int], y_pos: int, message_title: str, message_text: str):
        super().__init__()
        self.title_font = pygame.font.Font(normpath("./Fonts/Arial bold.ttf"), 20)
        self.body_font = pygame.font.Font(normpath("./Fonts/Arial.ttf"), 18)
        self.icon_img = pygame.Surface((50, 50))
        self.icon_img.fill(BLACK)
        self.image_padding = 15
        self.resolution = resolution
        self.x = self.resolution[0]
        self.y = y_pos
        self.width = 320
        self.corner_radius = 15
        self.close_btn_img = pygame.Surface((15, 15))
        self.close_btn_img.fill(BLACK)
        self.close_btn_x = self.width - self.corner_radius - self.close_btn_img.get_size()[0]
        self.close_btn_y = self.corner_radius
        self.close_btn_hovered = pygame.Surface((15, 15))
        self.close_btn_hovered.fill((255, 0, 0))
        self.close_rect = pygame.Rect(self.close_btn_x, self.close_btn_y, *self.close_btn_img.get_size())
        self.title_text = word_wrap_text(message_title,
                                         self.width - self.corner_radius * 2 - self.icon_img.get_size()[0] -
                                         self.image_padding - self.close_btn_img.get_size()[0],
                                         self.title_font)
        self.body_text = word_wrap_text(message_text,
                                        self.width - self.corner_radius * 2 - self.icon_img.get_size()[0] -
                                        self.image_padding - self.close_btn_img.get_size()[0],
                                        self.body_font)
        self.height = self.title_font.size("|")[1] * (len(self.title_text) + 1) + \
                      self.body_font.size("|")[1] * len(self.body_text) + \
                      self.corner_radius * 2
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(TRANSPARENT)
        self.image.set_colorkey(TRANSPARENT, pygame.RLEACCEL)
        draw_rounded_rect(self.image, 0, 0, self.width, self.height, self.corner_radius, GREY)
        self.image.blit(self.icon_img, (self.corner_radius, self.corner_radius))
        self.image.blit(self.close_btn_img, (self.close_btn_x, self.close_btn_y))
        self.render_text(self.title_font, self.title_text, self.title_font.size("|")[1])
        self.render_text(self.body_font, self.body_text, self.body_font.size("|")[1],
                         self.title_font.size("|")[1] * (len(self.title_text) + 1))
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.mask = pygame.mask.from_surface(self.image)
        # region Physics Variables
        self.direction = "left"
        self.slide_padding = 20
        self.dest_x = self.resolution[0] - self.width - self.slide_padding
        self.remaining_distance = self.resolution[0] - self.dest_x
        self.fraction = 0.92
        self.delta_time = Time.Time()
        self.delta_time.reset_timer()
        self.notification_timer = Time.Time()
        self.dismiss_timer = 10
        self.physics = None
        self.acceleration = 550
        # endregion

    def render_text(self, font: pygame.font.Font, text: List[str], line_height: int, calc_y: int = 0) -> None:
        for line_number, line_text in enumerate(text):
            text_surf = font.render(line_text, True, BLACK)
            self.image.blit(text_surf, (self.corner_radius + self.icon_img.get_size()[0] + self.image_padding,
                                        self.corner_radius + calc_y + line_height * line_number))

    def update(self) -> Union[Literal[True], None]:
        if self.direction == "left":
            time = self.delta_time.get_time()
            self.delta_time.reset_timer()
            self.remaining_distance = self.remaining_distance * (self.fraction / (time if time > 1 else 1))
            if round(self.remaining_distance) > 0:
                self.x = self.dest_x + self.remaining_distance
            else:
                self.x = self.dest_x
                self.direction = "idle"
                self.notification_timer.reset_timer()
        elif self.direction == "right":
            movement = self.physics.calc()
            self.x += movement
            if self.x > self.resolution[0]:
                self.kill()
                return True  # Delete this toast notification
        elif self.direction == "idle":
            if self.notification_timer.get_time() > self.dismiss_timer:
                self.notification_timer.reset_timer()
                self.dismiss()
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def change_y(self, y: int) -> None:
        self.y -= y
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def reset_hover_state(self) -> None:
        if self.direction == "idle":
            self.image.blit(self.close_btn_img, (self.close_btn_x, self.close_btn_y))

    def mouse_event(self, mouse_pos: Tuple[int, int], clicked: bool) -> None:
        if self.direction == "idle":
            if self.close_rect.collidepoint((mouse_pos[0] - self.x, mouse_pos[1] - self.y)):
                if clicked:
                    # Blit the image of the darkened close button over the original, un-darkened one.
                    self.dismiss()
                else:
                    self.image.blit(self.close_btn_hovered, (self.close_btn_x, self.close_btn_y))

    def dismiss(self) -> None:
        pygame.draw.rect(self.image, GREY, self.close_rect, 0)  # Paint over the close button.
        self.direction = "right"
        self.physics = Physics.EulerAcceleration(self.acceleration)

    def get_size(self) -> Tuple[int, int]:
        return self.width, self.height


class ToastGroup(pygame.sprite.Group):
    def __init__(self, resolution: Tuple[int, int]):
        super().__init__()
        self.z_index = 1
        self.resolution = resolution
        self.toasts = []
        self.padding = 10

    def create_toast(self, toast_title: str, toast_text: str) -> None:
        new_toast = ToastNotifier(self.resolution,
                                  self.padding * (len(self.toasts) + 1) + sum(toast.get_size()[1] for toast in self.toasts),
                                  toast_title,
                                  toast_text)
        self.toasts.append(new_toast)
        self.add(new_toast)

    def update(self) -> None:
        for index, toast in enumerate(self.toasts):
            value = toast.update()
            if value is not None:
                self.move_up(index)
                self.toasts[index] = None
        self.toasts[:] = [toast for toast in self.toasts if toast is not None]

    def move_up(self, index: int) -> None:
        height = self.toasts[index].get_size()[1] + self.padding
        for i in range(index + 1, len(self.toasts)):
            if self.toasts[i] is not None:
                self.toasts[i].change_y(height)

    def send_mouse_pos(self, mouse_object: Mouse.Cursor) -> None:
        if not self.z_index == mouse_object.get_z_index():
            return None  # Exit if the mouse interaction has already been intercepted by a widget with a higher z-index.
        for toast in self.toasts:
            toast.reset_hover_state()
        colliding_toast = pygame.sprite.spritecollideany(mouse_object, self, collided=collide_function)
        if colliding_toast is None:
            # Only pass mouse event to the widget below if the mouse cursor failed to touch a toast notifier.
            mouse_object.increment_z_index()
        else:
            colliding_toast.mouse_event(mouse_object.get_pos(), mouse_object.get_button_state(1))

    def get_toast_num(self) -> int:
        return len(self.toasts)
