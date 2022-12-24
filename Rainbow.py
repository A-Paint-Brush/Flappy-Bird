from typing import *
import Time
import random


class Rainbow:
    def __init__(self):
        self.destination_rgb = tuple(random.randint(0, 255) for color in range(3))
        self.current_rgb = list(self.destination_rgb)
        self.divider_constant = 1
        self.size_diff = []
        self.steps = None
        self.delay = 0.1
        self.tick_timer = Time.Time()

    def init_rainbow(self) -> None:
        self.tick_timer.reset_timer()
        self.tick_timer.get_time()

    def tick(self) -> None:
        time = self.tick_timer.get_time()
        self.tick_timer.reset_timer()
        if self.current_rgb == list(self.destination_rgb):
            self.destination_rgb = tuple(random.randint(0, 255) for color in range(3))
            self.size_diff = []
            for color in range(3):
                if self.current_rgb[color] < self.destination_rgb[color]:
                    diff = "<"
                elif self.current_rgb[color] > self.destination_rgb[color]:
                    diff = ">"
                else:
                    diff = "="
                self.size_diff.append(diff)
            differences = tuple(self.destination_rgb[color] - self.current_rgb[color] for color in range(3))
            self.steps = tuple(differences[color] / self.divider_constant for color in range(3))
            self.step_color(time)
        else:
            # Do one step towards destination RGB.
            self.step_color(time)

    def step_color(self, delta_time: float) -> None:
        for color in range(3):
            if self.size_diff[color] == "=":
                continue
            self.current_rgb[color] += self.steps[color] * delta_time
            if self.size_diff[color] == "<":
                if self.current_rgb[color] > self.destination_rgb[color]:
                    self.current_rgb[color] = self.destination_rgb[color]
            elif self.size_diff[color] == ">":
                if self.current_rgb[color] < self.destination_rgb[color]:
                    self.current_rgb[color] = self.destination_rgb[color]

    def get_color(self) -> List:
        return self.current_rgb
