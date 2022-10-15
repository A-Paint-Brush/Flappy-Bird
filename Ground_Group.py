import pygame
import Time


class GroundGroup(pygame.sprite.Group):
    def __init__(self, sprite_list):
        super().__init__(sprite_list)
        self.delta_x = -40
        self.frame_timer = Time.Time()
        self.frame_timer.reset_timer()

    def get_movement(self):
        return self.delta_x

    def update_(self):
        movement = self.delta_x * self.frame_timer.get_time()
        super().update(movement)
        self.frame_timer.reset_timer()
        return movement
