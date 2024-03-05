
import pygame
pipe_gap = 150
scroll_speed = 4

class Pipe(pygame.sprite.Sprite):
    def __init__(self, x, y, position):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("sprites/pipe-green.png")
        self.rect = self.image.get_rect()
        self.position = position
        self.x = x
        self.y = y
        # position 1 = top, -1 bottom
        if position == 1:
            self.image = pygame.transform.flip(self.image, False, True)
            self.rect.bottomleft = [x, y - pipe_gap/2]
        if position == -1:
            self.rect.topleft = [x,y + pipe_gap/2]
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self.rect.x -= scroll_speed
        if self.rect.right < 0:
            self.kill()