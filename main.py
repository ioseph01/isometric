import pygame
import random
import sys
from pygame.locals import *

from scripts.game import Game
from scripts.windows import *
from scripts.text import Font

# -- Initialize Pygame --
pygame.init()
screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption("Game Base")
clock = pygame.time.Clock()


# -- Controller Class --
class Controller:
    def __init__(self):
        self.mode = 'Main_Menu'
        self.windows = {
            'Game': Game(self),
            'Main_Menu': MainMenu(self),
            'Options': Options(self),
            'Stats': Stats(self)
        }
        self.font = Font("small_font.png")

    @property
    def current(self):
        return self.windows[self.mode]

# -- Init Controller and Font --
controller = Controller()
font = Font("small_font.png")  # Replace with your bitmap font loader if needed

# -- Main Loop (Works in Pygbag) --
running = True
while running:
    events = pygame.event.get()

    for event in events:
        if event.type == QUIT:
            running = False

    controller.current.update(events, screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
