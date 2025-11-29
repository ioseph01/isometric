import pygame
import random
import sys
from pygame.locals import *
import asyncio

from scripts.windows import *
from scripts.text import Font

# -- Controller Class --

import os

class Controller:
    def __init__(self):
        self.mode = 'Main_Menu'
        self.windows = {
            # 'Game': Game(self),
            'Main_Menu': MainMenu(self),
            'Options': Options(self),
            'Stats': Stats(self),
            'TestWindow': TestWindow(self),
        }
        # self.mode = 'TestWindow'
        self.font = Font("small_font.png")

    @property
    def current(self):
        return self.windows[self.mode]
    
class TestWindow:
    def __init__(self, controller):
        self.controller = controller
        
    def update(self, events, screen):
        self.draw(screen)
    def draw(self, screen):
        screen.fill((255, 0, 0))  # Red screen
        self.controller.font.render(screen, "HI!",(20,20))

async def main():
    pygame.init()
    screen = pygame.display.set_mode((720,540))
    pygame.display.set_caption("gameing")
    clock = pygame.time.Clock()
    controller = Controller()
    
    running = True
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
        
        controller.current.update(events, screen)
        pygame.display.flip()
        await asyncio.sleep(0)  
        clock.tick(60)

    if sys.platform != "emscripten":
        pygame.quit()
        sys.exit()

if sys.platform == "emscripten":
    asyncio.ensure_future(main())  
else:
    asyncio.run(main())        
