import cv2
import sys
import torch
import random
import numpy as np

import pygame
from pygame.locals import *
from pygame.sprite import Sprite
from pygame.surfarray import array2d

from . sprites import Bird, Pipe, GameText, Base


class Game():

    def __init__(self, frame_size, width=288, height=512):
        """
        Initialize the game. 
        A minimal version for use training deep reinforcement learning methods. 

        Argument:
            frame_size (int): width, height of extracted frame for DRL in pixels
            width (int): width of game screen in pixels
            height (int): height of game screen in pixels
        """
        pygame.init()

        # Frame rate of the game
        self.fps = 30

        # Game clock which ticks according to the game framerate
        self.clock = pygame.time.Clock()

        # Set up display
        self.width, self.height = width, height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Flappy Bird')

        # Set game difficulty as [0,1,2] = [easy, medium, or hard]
        self.level = 2

        # Set up game objects
        self.bg = pygame.image.load('game/assets/background.png').convert_alpha()
        self.game_text = GameText()
        self.player = Bird(0.2*width, 0.45*height)
        self.base = Base()
        self.pipes = [Pipe(self.width*0.5, self.level), Pipe(self.width, self.level)] 

        # List of flags indicating whether or not the pass through of the pipe 
        # pairs has been counted yet
        self.pipe_counted = [False, False]

        # Tell bird sprite the game has started.
        self.player.set_game_play_mode(True)

        # Size of extracted frames for use in DRL training
        self.frame_size = frame_size


    def update_display(self, mode='drl'):
        """
        Update the game display with the game background and sprites. 

        Args:
            mode (str): One of ['drl' or 'game']. If 'dqn', then we would like 
                to render a simplistic version. If 'game', then we would like to 
                render the full version.
        """
        # Draw the background
        if mode == 'game':
            self.screen.blit(self.bg, (0,0))
        if mode == 'drl':
            self.screen.fill(((0,0,0)))

        # Draw the sprites
        for pipe in self.pipes:
            pipe.draw()
        self.player.draw()
        # if mode == 'game':
        self.base.draw()

        # Draw any messages
        if mode == 'game':
            self.game_text.draw('main')

        # Update the entire game display
        pygame.display.flip()


    def process_frame_drl(self):
        """
        Process and clean the frame so we can input into the DRL function.

        Returns:
            (tensor): 1x84x84 tensor 
        """
        # Import game screen array
        state = np.array(array2d(self.screen), dtype='uint8')

        # Crop out where the base would be
        state = state[:,:400]

        # Resize to 84x 84
        state = cv2.resize(state, (self.frame_size, self.frame_size))

        # Convert to black and white
        state[state > 0] = 1

        return torch.tensor([state]).float()


    def step(self, action):
        """
        Advances the game by one frame. 

        The bird tries to accrue as many points as possible by passing through the pipe pairs. The agent can either flap its wings or do nothing. The game ends when the bird hits an obstacle (a pipe pair or 
        the ground).

        Arguments:
            action (bool): If True, the bird flaps its wings once. If False, the bird does nothing.

        Returns:
            tensor, float, bool: 84x84 processed frame, reward, done status
        """
        reward = 0.1 
        done = False

        # Check to see if the player bird has collided with any of the pipe
        # pairs or the base. If so, exit the game loop.
        obstacles = self.pipes + [self.base]
        if self.player.check_collide(obstacles):
            reward = -1
            done = True

        # If the player passes through a pipe, add +1 to score
        for i in range(len(self.pipes)):
            if not self.pipe_counted[i]:
                if self.pipes[i].x < self.player.x:
                    self.game_text.update_score() 
                    self.pipe_counted[i] = True
                    reward = 1

        # Update base sprite
        self.base.update()

        # Update player sprite
        self.player.update(action)

        # Update pipes
        for pipe in self.pipes:
            pipe.update() 

        # Add a new pipe when one of the pipes has shifted off screen
        if self.pipes[0].x < 0 and len(self.pipes) < 3:
            self.pipes.append(Pipe(self.width+50, self.level))
            self.pipe_counted.append(False)

        # Remove pipe that has shifted left off screen
        if self.pipes[0].x < -self.pipes[0].image.get_width():
            self.pipes.pop(0)
            self.pipe_counted.pop(0)

        # Update the game display
        self.update_display(mode='drl')
        frame = self.process_frame_drl()
        # If playing_game, then update display again.

        # Increment
        self.clock.tick(self.fps)

        # If the game ended, restart
        if done:
            self.__init__(self.frame_size)

        return frame, reward, done


def listen():
    """
    Listen and log key presses from user (spacebar, arrow keys). 
    Will automatically exit game if it gets a quit signal.

    Returns:
        list (str): a list of the names of the keys pressed
    """
    keypress = []

    for event in pygame.event.get():

        # If spacebar is pressed
        if event.type == KEYDOWN and event.key == K_SPACE:
            keypress.append('spacebar')

        # If arrows pressed
        if event.type == KEYDOWN and event.key == K_RIGHT:
            keypress.append('right_arrow')

        if event.type == KEYDOWN and event.key == K_LEFT:
            keypress.append('left_arrow')

        # If quit triggered
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

    return keypress