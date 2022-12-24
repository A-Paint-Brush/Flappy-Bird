import pygame.time


class Time:
    def __init__(self):
        self.timer = 0
        self.previous_result = 0

    def reset_timer(self) -> None:
        self.timer = pygame.time.get_ticks() / 1000
        self.previous_result = 0

    def get_time(self) -> float:
        self.previous_result = pygame.time.get_ticks() / 1000 - self.timer
        return self.previous_result

    def force_elapsed_time(self, value: float) -> None:
        self.timer = pygame.time.get_ticks() / 1000 - value

    def get_prev_time(self) -> float:
        return self.previous_result
