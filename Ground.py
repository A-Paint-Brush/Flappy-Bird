from os.path import normpath
import pygame
import Time


class Tile(pygame.sprite.Sprite):
    def __init__(self, x_pos, resolution):
        super().__init__()
        self.image = pygame.image.load(normpath("./Images/Ground.png")).convert_alpha()
        self.width, self.height = self.image.get_size()
        self.x = x_pos
        self.y = resolution[1] - self.height
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def get_size(self):
        return self.width, self.height

    def get_pos(self):
        return self.x, self.y

    def get_rect(self):
        return self.rect

    def draw(self, surface):
        surface.blit(self.image, (self.x, self.y))

    def update(self, movement):
        self.x += movement
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def check_collision(self):
        if self.x < -self.width:
            self.kill()
            return True
        else:
            return False


class GroundGroup(pygame.sprite.Group):
    def __init__(self, resolution):
        super().__init__()
        self.resolution = resolution
        self.__delta_x = -100  # Production movement: -100, Debug movement: -40
        self.temp = Tile(-1, self.resolution)
        self.sprite_objects = []
        self.__frame_timer = Time.Time()
        self.__frame_timer.reset_timer()

    def generate(self):
        self.sprite_objects = [Tile(x, self.resolution) for x in range(self.resolution[0], -self.temp.get_size()[0], -self.temp.get_size()[0])]
        self.add(self.sprite_objects)

    def get_size(self):
        return self.temp.get_size()

    def get_pos(self):
        return self.temp.get_pos()

    def move(self):
        movement = (self.__delta_x * self.__frame_timer.get_time())
        self.update(movement)
        self.__frame_timer.reset_timer()
        return movement

    def kill_colliding(self):
        self.sprite_objects[:] = [tile for tile in self.sprite_objects if not tile.check_collision()]
        if len(self.sprite_objects) == 0:
            self.generate()
            return None
        while self.sprite_objects[0].get_pos()[0] < self.resolution[0] - self.temp.get_size()[0]:
            self.sprite_objects.insert(0, Tile(self.sprite_objects[0].get_pos()[0] + self.temp.get_size()[0], self.resolution))
            self.add(self.sprite_objects[0])
