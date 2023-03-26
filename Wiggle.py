import math
import Time


class Wiggle:
    def __init__(self):
        self.frequency = 3.3
        self.v_shift = 30
        # Note to self: Period of a normal sin graph is '2𝜋', giving a coefficient 'b' to 'x' makes the period '2𝜋 / b'.
        self.period = (2 * math.pi) / self.frequency
        self.elapsed_time = Time.Time()
        self.elapsed_time.reset_timer()

    def get_y_pos(self) -> float:
        x = self.elapsed_time.get_time()
        if x >= self.period:
            x %= self.period
            self.elapsed_time.force_elapsed_time(x)
        y = self.v_shift * math.sin(self.frequency * x) + self.v_shift
        return y

    def max_vertical_movement(self) -> int:
        return self.v_shift * 2
