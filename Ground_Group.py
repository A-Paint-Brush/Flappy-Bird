import pygame
import Ground
import Time


class GroundGroup(pygame.sprite.Group):
    def __init__(self, resolution):
        super().__init__()
        self.resolution = resolution
        self.delta_x = -40
        self.temp = Ground.Tile(-1, self.resolution)
        self.ground_tiles = None
        self.generate()
        self.add(self.ground_tiles)
        self.frame_timer = Time.Time()
        self.frame_timer.reset_timer()

    def generate(self):
        self.ground_tiles = [Ground.Tile(x, self.resolution) for x in range(self.resolution[0], -self.temp.get_size()[0], -self.temp.get_size()[0])]
        self.add(self.ground_tiles)

    def get_size(self):
        return self.temp.get_size()

    def get_pos(self):
        return self.temp.get_pos()

    def update_(self):
        movement = self.delta_x * self.frame_timer.get_time()
        super().update(movement)
        self.frame_timer.reset_timer()
        return movement

    def kill_colliding(self, surface):
        self.ground_tiles[:] = [tile for tile in self.ground_tiles if not tile.check_collision()]
        if len(self.ground_tiles) == 0:
            self.generate()
            return None
        while self.ground_tiles[0].get_pos()[0] < self.resolution[0] - self.temp.get_size()[0]:
            self.ground_tiles.insert(0, Ground.Tile(self.resolution[0] - (self.resolution[0] - (self.ground_tiles[0].get_pos()[0] + self.temp.get_size()[0])), self.resolution))
            self.add(self.ground_tiles[0])
            self.ground_tiles[0].draw(surface)
