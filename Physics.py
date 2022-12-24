from typing import *
import Time


class PreciseAcceleration:
    def __init__(self, acceleration: Union[int, float]):
        self.time = Time.Time()
        self.time.reset_timer()
        self.time.get_time()
        self.acceleration = acceleration

    def calc(self) -> Tuple[float, float, float]:
        s0 = self.time.get_prev_time()
        s1 = self.time.get_time()
        return (self.acceleration * s1 + self.acceleration * s0) * (s1 - s0) * 0.5, self.acceleration * s1, s1 - s0

    def reset_calculation(self) -> None:
        self.time.reset_timer()


class PreciseDeceleration(PreciseAcceleration):
    def __init__(self, deceleration: Union[int, float], starting_velocity: Union[int, float]):
        super().__init__(deceleration)
        self.starting_velocity = starting_velocity

    def calc(self) -> Tuple[float, float]:
        s0 = self.time.get_prev_time()
        s1 = self.time.get_time()
        return ((-self.acceleration * s1 + self.starting_velocity) + (-self.acceleration * s0 + self.starting_velocity)) * (s1 - s0) * 0.5, self.starting_velocity - self.acceleration * s1


class EulerAcceleration:
    def __init__(self, acceleration: Union[int, float]):
        self.speed = 0
        self.acceleration = acceleration
        self.time = Time.Time()
        self.time.reset_timer()

    def calc(self) -> float:
        delta_time = self.time.get_time()
        self.time.reset_timer()
        self.speed += self.acceleration * delta_time
        return self.speed * delta_time


class EulerDeceleration(EulerAcceleration):
    def __init__(self, deceleration: Union[int, float], starting_velocity: Union[int, float]):
        super().__init__(deceleration)
        self.speed = starting_velocity
