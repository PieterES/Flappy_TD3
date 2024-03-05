import pygame
import numpy as np

class Flappy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        self.index = 0
        self.counter = 0
        for i in range(1, 4):
            img = pygame.image.load(f"sprites/yellowbird_{i}.png")
            self.images.append(img)
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.center = [x, y]
        self.velocity = 0

    def update(self):
        self.counter += 1
        flap_cooldown = 10
        if self.counter > flap_cooldown:
            self.counter = 0
            self.index += 1
            if self.index >= len(self.images):
                self.index = 0
        self.image = self.images[self.index]


        self.velocity += 0.3
        if self.velocity >= 8:
            self.velocity = 8
        if self.velocity <= -8:
            self.velocity = -8
        # self.rect.y += int(self.velocity)
        if self.rect.bottom < 405:
            self.rect.y += int(self.velocity)

        # rotate bird
        self.image = pygame.transform.rotate(self.images[self.index], -self.velocity*2)
    def flap(self):
        self.velocity -= 8

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)
