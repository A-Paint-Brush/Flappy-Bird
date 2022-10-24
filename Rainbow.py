import Time
import random


class Rainbow:
    def __init__(self):
        self.rgb = tuple(random.randint(0, 255) for i in range(3))
        self.delay = 0.3
        self.tick_timer = Time.Time()

    def init_rainbow(self):
        self.tick_timer.reset_timer()

    def tick(self):
        if self.tick_timer.get_time() > self.delay:
            self.tick_timer.reset_timer()
            self.rgb = tuple(random.randint(0, 255) for i in range(3))

    def get_color(self):
        return self.rgb
