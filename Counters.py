from os.path import normpath
from Global import *
import pygame
import Time


class FPS(pygame.sprite.Sprite):
    def __init__(self, resolution: Tuple[int, int]):
        """Simple sprite that displays a fps counter whose value is calculated by the average of the delays between the
        last 10 frames."""
        super().__init__()
        self.resolution = resolution
        self.font = pygame.font.Font(normpath("Fonts/Arial/normal.ttf"), 25)
        self.frame_timer = Time.Time()
        self.frame_timer.reset_timer()
        self.fps_data = []
        self.storage_length = 10  # The number of entries to keep in the list.
        self.x = 0
        self.y = 0
        self.image = None
        self.rect = None
        self.update_text("-- FPS")

    def push_data(self) -> None:
        data = self.frame_timer.get_time()
        self.frame_timer.reset_timer()
        self.fps_data.append(data)

    def calc_data(self) -> int:
        return round(1 / (sum(self.fps_data) / len(self.fps_data)))

    def update_text(self, new_text: str) -> None:
        self.image = self.font.render(new_text, True, BLACK)
        self.x = self.resolution[0] - self.image.get_size()[0]
        self.rect = pygame.Rect(self.x, self.y, *self.image.get_size())

    def tick(self) -> Union[int, None]:
        self.push_data()
        if len(self.fps_data) <= self.storage_length:
            return None
        else:
            self.fps_data.pop(0)
            fps = self.calc_data()
            self.update_text("{} FPS".format(fps))
            return fps

    def stop(self) -> None:
        self.fps_data.clear()
        self.update_text("-- FPS")

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.image, (self.x, self.y))


class Score:
    def __init__(self, font_height: int = 70, kerning: int = 5):
        """Contains functionality for storing the score and rendering it using an image for each numeric character."""
        self.font_height = font_height
        self.kerning = kerning
        self.digit_images = []
        self.score = 0
        for i in range(10):
            image = pygame.image.load(normpath("Images/Digits/{}.png".format(i))).convert_alpha()
            if image.get_height() != self.font_height:
                new_size = (self.font_height * (image.get_width() / image.get_height()), self.font_height)
                image = pygame.transform.scale(image, new_size)
            self.digit_images.append(image)

    def change_score(self, value: int, mode: Literal["set", "change"]) -> None:
        if mode == "set":
            self.score = value
        elif mode == "change":
            self.score += value
        if self.score < 0:
            self.score = 0

    def get_score(self) -> int:
        return self.score

    def calc_size(self) -> Tuple[int, int]:
        s = str(self.score)
        return sum(self.digit_images[int(d)].get_width() for d in s) + self.kerning * (len(s) - 1), self.font_height

    def draw(self, surface: pygame.Surface, position: Tuple[Union[int, float], Union[int, float]]) -> None:
        accumulated_width = 0
        for d in str(self.score):
            digit_surf = self.digit_images[int(d)]
            surface.blit(digit_surf, (position[0] + accumulated_width, position[1]))
            accumulated_width += digit_surf.get_width() + self.kerning
