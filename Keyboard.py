import Time


class KeySequence:
    def __init__(self, sequence: tuple[int, ...]):
        self.correct_keys = sequence
        self.received_keys = []
        self.maximum_delay = 0.5
        self.delay_timer = Time.Time()
        self.delay_timer.reset_timer()

    def push_key(self, key_code: int):
        time = self.delay_timer.get_time()
        if time > self.maximum_delay:
            self.received_keys.clear()
        self.received_keys.append(key_code)
        if self.received_keys[-1] == self.correct_keys[len(self.received_keys) - 1]:
            self.delay_timer.reset_timer()
            if tuple(self.received_keys) == self.correct_keys:
                self.received_keys.clear()
                return True
            else:
                return False
        else:
            self.received_keys.clear()
            return False
