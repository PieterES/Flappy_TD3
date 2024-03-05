import pygame
import random
import os
import time
import numpy as np
from Flappy import Flappy
from Pipe import Pipe
from utils import ReplayBuffer
import TD3
import argparse
import math

WIDTH = 288
HEIGHT = 512
pygame.init()
font = pygame.font.SysFont(None, 32)
fps = 600
pipe_gap = 150
pipe_frequency = 650  # ms
flap_frequency = 20
ground_scroll = 0
scroll_speed = 4
pip_gap = 20
flying = False
game_over = False
last_flap = pygame.time.get_ticks() - flap_frequency
last_pipe = pygame.time.get_ticks() - pipe_frequency

button_img = pygame.image.load("sprites/gameover.png")
screen = pygame.display.set_mode((WIDTH*3, HEIGHT))
pygame.display.set_caption("Flappy AI")


# Load the background image
background_image = pygame.image.load("sprites/background-day.png")
ground = pygame.image.load("sprites/base.png")

# Concatenate multiple copies of the background image horizontally
long_background = pygame.Surface((WIDTH * 3, HEIGHT))
long_base = pygame.Surface((WIDTH * 4, HEIGHT))
for i in range(3):
    long_background.blit(background_image, (i * WIDTH, 0))
    long_base.blit(ground, (i * WIDTH, 0))


class Button():
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
    def draw(self):
        screen.blit(self.image, (self.rect.x, self.rect.y))



class FlappyGame:
    def __init__(self):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.flappy_group = pygame.sprite.Group()
        self.pipe_group = pygame.sprite.Group()
        self.last_pipe = last_pipe
        self.last_flap = last_flap
        self.flappy = Flappy(100, int(HEIGHT / 2))
        self.flappy_group.add(self.flappy)
        self.game_over = False
        self.score = 0

    def reset(self):
        self.score = 0
        self.frame_iteration = 0

        self.pipe_group.empty()
        flappy = Flappy(100, int(HEIGHT / 2))
        self.flappy_group.empty()
        self.flappy_group.add(flappy)
        y = HEIGHT/2
        velocity = 0
        top_pipe_y = 50/HEIGHT
        bottom_pipe_x = 800/(WIDTH*3)
        bottom_pipe_y = 350/HEIGHT
        closest_pipe = 800/HEIGHT

        return [float(y), float(0), float(top_pipe_y), float(bottom_pipe_x), float(bottom_pipe_y), float(0)]


    def detect_collision(self):
        for bird in self.flappy_group:
            if pygame.sprite.groupcollide(self.flappy_group, self.pipe_group, False,
                                          False) or bird.rect.top < 0 or bird.rect.bottom > 400:
                return True

        return False


    def step(self, state, prev_action, time_passes):

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

        if prev_action >= 0:
            for bird in self.flappy_group:
                bird.flap()
        self.update(time_passes, ground_scroll, last_pipe)

        next_state = self.get_observations(prev_action)
        dist_top = 800
        dist_bottom = 800
        top_pipe_x = 800
        bottom_pipe_x = 700
        top_pipe_y = 50
        bottom_pipe_y = 350
        score = 0
        done = False
        for bird in self.flappy_group:
            if bird.rect.top < 15 or bird.rect.bottom > 375:
                score = -1
            else:
                score = 1
            closest_pipe_x = np.inf
            for pipe in self.pipe_group:
                if pipe.rect.bottomright[0] >= bird.rect.bottomleft[0]:
                    if pipe.rect.bottomleft[0] <= closest_pipe_x:
                        closest_pipe_x = pipe.rect.bottomleft[0]
                        if pipe.position == 1:
                            top_pipe_y = pipe.rect.bottomleft[1]
                            top_pipe_x = pipe.rect.bottomleft[0]
                        else:
                            bottom_pipe_x = pipe.rect.topleft[0]
                            bottom_pipe_y = pipe.rect.topleft[1]
            if bottom_pipe_y - 5 > bird.rect.bottomright[1] and bird.rect.topright[1] > top_pipe_y+5:
                score += 2
        if self.detect_collision():
            score -= 20
            self.game_over = True
            done = True
        info = None
        return state, next_state, score, self.game_over

    def update(self, score, ground_scroll, last_pipe):
        counting_text = font.render(str(int(score // 100)), 1, (255, 255, 255))
        counting_rect = counting_text.get_rect(center=(WIDTH * 1.5, 100))
        self.screen.blit(long_background, (0, 0))

        self.pipe_group.draw(self.screen)
        self.pipe_group.update()

        self.screen.blit(long_base, (ground_scroll, HEIGHT - 112))

        self.flappy_group.draw(self.screen)
        self.flappy_group.update()

        if self.game_over == False:

            time_now = pygame.time.get_ticks()
            if time_now - self.last_pipe > pipe_frequency:
                pipe_height = random.randint(-150, 50)
                bottom_pipe = Pipe(WIDTH * 3, int(HEIGHT / 2) + pipe_height, -1)
                top_pipe = Pipe(WIDTH * 3, int(HEIGHT / 2) + pipe_height, 1)
                self.pipe_group.add(bottom_pipe)
                self.pipe_group.add(top_pipe)
                self.last_pipe = time_now

            ground_scroll -= scroll_speed
            if abs(ground_scroll) > 25:
                ground_scroll = 0
        self.screen.blit(counting_text, counting_rect)

        pygame.display.flip()
    def sample_action(self):
        sample_action = random.uniform(-1,1)
        return sample_action
    def get_observations(self, prev_action):
        y = 0
        x = 0
        velocity = 0
        top_pipe_y = 50
        bottom_pipe_x = WIDTH*3
        bottom_pipe_y = 350
        for bird in self.flappy_group:
            y = bird.rect.center[1]
            x = bird.rect.bottomleft[0]
            velocity = bird.velocity
            closest_pipe_x = WIDTH * 3
            for pipe in self.pipe_group:
                if pipe.rect.bottomright[0] >= bird.rect.bottomleft[0] and pipe.rect.bottomleft[0] <= closest_pipe_x:
                    closest_pipe_x = pipe.rect.bottomleft[0]
                    # print('cloststs')
                    if pipe.position == 1:
                        top_pipe_y = pipe.rect.bottomleft[1]
                        top_pipe_x = pipe.rect.bottomleft[0]
                    else:
                        bottom_pipe_x = pipe.rect.topleft[0]
                        bottom_pipe_y = pipe.rect.topleft[1]
        observations = [float(y)/HEIGHT,
                        float(velocity)/8,
                        float(top_pipe_y)/HEIGHT,
                        float(bottom_pipe_x)/(WIDTH*3),
                        float(bottom_pipe_y)/HEIGHT,
                        float(prev_action)]
        # print(observations)
        return observations

restart_button = Button((WIDTH * 3) // 2 - 75, HEIGHT // 2 - 100, button_img)

game = FlappyGame()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", default="TD3")  # Policy name (TD3, DDPG or OurDDPG)
    parser.add_argument("--start_timesteps", default=25e3, type=int)  # Time steps initial random policy is used
    parser.add_argument("--eval_freq", default=5e3, type=int)  # How often (time steps) we evaluate
    parser.add_argument("--max_timesteps", default=1e6, type=int)  # Max time steps to run environment
    parser.add_argument("--expl_noise", default=0.1, type=float)  # Std of Gaussian exploration noise
    parser.add_argument("--batch_size", default=16, type=int)  # Batch size for both actor and critic
    parser.add_argument("--discount", default=0.99, type=float)  # Discount factor
    parser.add_argument("--tau", default=0.005, type=float)  # Target network update rate
    parser.add_argument("--policy_noise", default=0.2)  # Noise added to target policy during critic update
    parser.add_argument("--noise_clip", default=0.5)  # Range to clip target policy noise
    parser.add_argument("--policy_freq", default=2, type=int)  # Frequency of delayed policy updates
    parser.add_argument("--save_model", action="store_true")  # Save model and optimizer parameters
    parser.add_argument("--load_model", default="")  # Model load file name, "" doesn't load, "default" uses file_name
    args = parser.parse_args()
    state_dim = 6
    action_dim = 1
    max_action = 1
    kwargs = {
        "state_dim": state_dim,
        "action_dim": action_dim,
        "max_action": max_action,
        "discount": args.discount,
        "tau": args.tau,
    }

    # Initialize policy
    if args.policy == "TD3":
        # Target policy smoothing is scaled wrt the action scale
        kwargs["policy_noise"] = args.policy_noise * max_action
        kwargs["noise_clip"] = args.noise_clip * max_action
        kwargs["policy_freq"] = args.policy_freq
        policy = TD3.TD3(**kwargs)

    flappy_group = pygame.sprite.Group()
    pipe_group = pygame.sprite.Group()

    flappy = Flappy(100, int(HEIGHT / 2))
    flappy_group.add(flappy)

    restart_button = Button((WIDTH * 3) // 2 - 75, HEIGHT // 2 - 100, button_img)

    replay_buffer = ReplayBuffer(state_dim, action_dim)
    game = FlappyGame()
    state, done = game.reset(), False
    total_timesteps = 0
    start_step = 2000
    clock = pygame.time.Clock()
    time_passes = 0
    score = 0
    while int(score // 100) < 100:
        clock.tick(fps)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
        time_passes += 1
        if total_timesteps > start_step:
            policy.train(replay_buffer, args.batch_size)
            action = policy.select_action(np.array(state))

        else:
            action = game.sample_action()

        total_timesteps += 1

        state, next_state, score, game.game_over = game.step(state, action, time_passes)

        replay_buffer.add(state, action, next_state, score, game.game_over)
        state = next_state
        if total_timesteps == start_step:
            print("start_training")
        if game.game_over == True:
            state, game.game_over = game.reset(), False
            time_passes = 0
            done = False
            score = 0
    print('Final Score', score)
    pygame.quit()


