import Time


class PreciseAcceleration:
    def __init__(self, acceleration):
        self.time = Time.Time()
        self.time.reset_timer()
        self.time.get_time()
        self.acceleration = acceleration

    def calc(self):
        s0 = self.time.get_prev_time()
        s1 = self.time.get_time()
        return (self.acceleration * s1 + self.acceleration * s0) * (s1 - s0) * 0.5, self.acceleration * s1, s1 - s0

    def reset_calculation(self):
        self.time.reset_timer()


class PreciseDeceleration(PreciseAcceleration):
    def __init__(self, deceleration, starting_velocity):
        super().__init__(deceleration)
        self.starting_velocity = starting_velocity

    def calc(self):
        s0 = self.time.get_prev_time()
        s1 = self.time.get_time()
        return ((-self.acceleration * s1 + self.starting_velocity) + (-self.acceleration * s0 + self.starting_velocity)) * (s1 - s0) * 0.5, self.starting_velocity - self.acceleration * s1
