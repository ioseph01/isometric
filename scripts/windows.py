from pygame.locals import *
from scripts.game import Game
import random
import pygame
import sys
from scripts.utils import load_image, load_images
        
class MainMenu:
    def __init__(self, controller):
        self.controller = controller
        self.options = ["Start Game", "Controls", "Quit"]
        self.selected = 0 
        self.logo = load_image("logo.png")

    def update(self, events, screen):
        self.draw(screen)
        for event in events:
            if event.type == KEYDOWN:
                if event.key == K_DOWN:
                    self.selected = (self.selected + 1) % len(self.options)
                elif event.key == K_UP:
                    self.selected = (self.selected - 1) % len(self.options)
                elif event.key in (K_RETURN, K_SPACE):
                    self.activate_option(self.selected)

    def activate_option(self, index):
        option = self.options[index]
        if option == "Start Game":
            self.controller.windows['Game'] = Game(self.controller)
            self.controller.mode = 'Game'
        if option == "Controls":
            self.controller.mode = 'Options'
        elif option == "Quit":
            pygame.quit()
            sys.exit()

    def draw(self, surface):
        surface.fill((30, 30, 60))
        x = (720 - self.logo.get_width()) // 2
        surface.blit(self.logo, (x,40))
        padding, spacing = 200, 80
        for i, option in enumerate(self.options):
            y = padding + i * spacing
            text_width = self.controller.font.get_width(option)
            x = (720 - text_width) // 2
            self.controller.font.render(surface, option, (x, y))  # Aligned text

            if i == self.selected:
                self.controller.font.render(surface, ">", (x - 20, y))  # Draw selector at fixed position


class Options:
    def __init__(self, controller):
        self.controller = controller
        self.lines = [
            "HOW TO PLAY",
            "",
            "Collect all gems to clear a stage",
            "",
            "CONTROLS:",
            "WASD or Arrow Keys - Move",
            "I/C - Lay an egg (Needs 10 or more gems)",
            "O/V - Teleport to egg",
            "",
            "Press P to pause",
            "Press ESC/Q to return to Main Menu"
        ]

    def update(self, events, screen):
        for event in events:
            if event.type == KEYDOWN and event.key in [K_ESCAPE, K_q]:
                self.controller.mode = 'Main_Menu'
        self.draw(screen)

    def draw(self, surface):
        surface.fill((30, 30, 60))

        total_height = len(self.lines) * 32
        start_y = (480 - total_height) // 2

        for i, line in enumerate(self.lines):
            if i < 4:
                text_width = self.controller.font.get_width(line)
                x = (720 - text_width) // 2
            else:
                x = 60
            y = start_y + i * 32
            self.controller.font.render(surface, line, (x, y))

class Stats:
    def __init__(self, controller):
        self.controller = controller
        self.level = 0
        self.score = 0
        self.message = "Game Over"
        self.lines = 0

    def load_from_game(self, game):
        self.level = str(game.level)
        self.score = str(game.score)
        self.message = random.choice(('Game Over', 'RIP', 'Unlucky', 'End of Run'))
        self.lines = 0
        self.tick = [0,20]

    def update(self, events, screen):
        self.tick[0] = (self.tick[0] + 1) % self.tick[1]
        if self.tick[0] == 0:
            self.lines += 1
        for event in events:
            if event.type == KEYDOWN:
                if self.lines >= 6:
                    self.controller.mode = 'Main_Menu'
                else:
                    self.lines = max(5, self.lines + 1)
                
        self.draw(screen)

    def draw(self, surface):
        surface.fill((20, 60, 20))
        surface.fill((30, 30, 60))
        padding, spacing = 100, 60
        for i,text in enumerate([self.message, "FINAL LEVEL", self.level, "FINAL SCORE", self.score, 'Press any key to continue']):
            if i >= self.lines:
                break
            y = padding + i * spacing
            text_width = self.controller.font.get_width(text)
            x = (720 - text_width) // 2
            self.controller.font.render(surface, text, (x, y))  # Aligned text
