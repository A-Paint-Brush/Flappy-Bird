import math
import Time


class Wiggle:
    def __init__(self):
        self.frequency = 0.3
        self.vertical_movement = 30
        self.elapsed_time = Time.Time()
        self.elapsed_time.reset_timer()

    def get_y_pos(self) -> float:
        return self.vertical_movement * math.sin(self.elapsed_time.get_time() / self.frequency) + self.vertical_movement

    def max_vertical_movement(self) -> int:
        return self.vertical_movement * 2
