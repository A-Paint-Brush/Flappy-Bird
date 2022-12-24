import time


class Time:
    def __init__(self):
        self.timer = 0
        self.previous_result = 0

    def reset_timer(self) -> None:
        self.timer = time.time()
        self.previous_result = 0

    def get_time(self) -> float:
        self.previous_result = time.time() - self.timer
        return self.previous_result

    def get_prev_time(self) -> float:
        return self.previous_result
