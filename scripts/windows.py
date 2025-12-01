from pygame.locals import *
from scripts.game import Game
from scripts.text import Font
import random
import pygame
import sys
from scripts.utils import load_image, load_images


class Controller:
    def __init__(self):
        self.mode = 'Main_Menu'
        self.windows = {
            # 'Game': Game(self),
            'Main_Menu': MainMenu(self),
            'Options': Options(self),
            'Stats': Stats(self),
            'Pause': Pause(self),
        }
        self.sfx = True
        self.font = Font("small_font.png")
        self.screen_rect = pygame.Rect(0,0,720,540)

    @property
    def current(self):
        return self.windows[self.mode]
    
        
class MainMenu:
    def __init__(self, controller):
        self.controller = controller
        self.options = ["Start Game", "Controls"]
        self.selected = 0 
        self.logo = load_image("logo (2).png")

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
            # self.controller.windows['Game'] = Game(self.controller)
            self.controller.mode = 'Game'
        if option == "Controls":
            self.controller.mode = 'Options'
        # elif option == "Quit":
        #     pygame.quit()
        #     sys.exit()

    def draw(self, surface):
        surface.fill((30, 30, 60))
        x = (720 - self.logo.get_width()) // 2
        surface.blit(self.logo, (x,120))
        padding, spacing = 240, 80
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


class Pause:
    def __init__(self, controller):
        self.controller = controller
        self.options = ["Resume", "SFX: ON", "MUSIC: ON", "Quit"]
        self.selected = 0 
        self.base = pygame.Surface((270, 200), pygame.SRCALPHA)
        self.base.fill((0, 0, 0, 200))  # semi-transparent fill
        self.rect = pygame.Rect(10,10,250,180)
        pygame.draw.rect(self.base, (255, 255, 255), self.rect, width=5)  # white 2px border



    def activate_option(self, selected):
        if selected == 'Quit':
            self.controller.windows['Game'].quit()
        elif selected == 'Resume':
            self.controller.mode = 'Game'
        elif selected == 'SFX: ON':
            self.controller.sfx = not self.controller.sfx
            self.options[1] = 'SFX: OFF'
        elif selected == 'SFX: OFF':
            self.controller.sfx = not self.controller.sfx
            self.options[1] = 'SFX: ON'
        elif selected == 'MUSIC: ON':
            pygame.mixer.music.stop()
            self.options[2] = 'MUSIC: OFF'
        elif selected == 'MUSIC: OFF':
            pygame.mixer.music.load('data/music.mp3')
            pygame.mixer.music.play(-1)
            self.options[2] = 'MUSIC: ON'

            

    def update(self, events, screen):

        for event in events:
            if event.type == KEYDOWN:
                if event.key == K_DOWN:
                    self.selected = (self.selected + 1) % len(self.options)
                elif event.key == K_UP:
                    self.selected = (self.selected - 1) % len(self.options)
                elif event.key in (K_RETURN, K_SPACE):
                    self.activate_option(self.options[self.selected])
                elif event.key == K_p:
                    self.controller.mode = 'Game'

        self.draw(screen)

    def draw(self,surface):
        surface.blit(self.controller.windows['Game'].paused_surface, (0,0))
        surface.blit(self.base, ((720 - 270) // 2,150))
        padding, spacing = 180, 40
        for i, option in enumerate(self.options):
            y = padding + i * spacing
            text_width = self.controller.font.get_width(option)
            x = (720 - text_width) // 2
            self.controller.font.render(surface, option, (x, y))  # Aligned text

            if i == self.selected:
                self.controller.font.render(surface, ">", (x - 20, y))  # Draw selector at fixed position
