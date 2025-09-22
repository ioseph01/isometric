#!/usr/bin/python3.4
# Setup Python ----------------------------------------------- #
import pygame, sys

from game import Game
from scripts.text import Font

# Setup pygame/window ---------------------------------------- #
mainClock = pygame.time.Clock()
from pygame.locals import *
pygame.init()
pygame.display.set_caption('game base')
screen = pygame.display.set_mode((640,480))

font = Font('small_font.png')

# def draw_text(text, font, color, surface, x, y):
#     textobj = font.render(text, 1, color)
#     textrect = textobj.get_rect()
#     textrect.topleft = (x, y)
#     surface.blit(textobj, textrect)

click = False

button_1 = pygame.Surface((80, 12))
button_2 = pygame.Surface((100, 12))

def main_menu():
    while True:

        screen.fill((0,0,0))

        mx, my = pygame.mouse.get_pos()

        font.render(button_1, "Start", (0,0))
        font.render(button_2, "Tutorial", (0,0))
        screen.blit(button_1, (50,100))
        screen.blit(button_2, (50,200))
        
        if button_1.get_rect(topleft=(50,100)).collidepoint((mx, my)):
            if click:
                game()
        if button_2.get_rect(topleft=(50,200)).collidepoint((mx, my)):
            if click:
                options()
        

        click = False
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    click = True

        pygame.display.update()
        mainClock.tick(60)

def game():
    game = Game()
    game.reset()
    results(game.run())

def results(stats):
    running = True
    click = False
    
    to_blit = [stats['title'], "Final Score", stats['score'], "Final Level", stats['level'], "Press any key to continue"]
    count = 0

    while running:
        
        screen.fill((0,0,0))
        w = 640
        y = 120
        for i in range(count // 20):
            surface = pygame.Surface((600,15))
            x = (640 - len(to_blit[i])*10) // 2
            font.render(surface, to_blit[i], (0,0))
            screen.blit(surface,(x,y))
            y += 50
            
        count = min(count + 1, len(to_blit) * 20)

            
        
        
        click = False
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and count >= len(to_blit) * 20:
                    running = False
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    click = True
        
        pygame.display.update()
        mainClock.tick(60)

def options():
    running = True
    click = False
    button = pygame.Surface((80, 12))

    while running:
        screen.fill((0,0,0))
        font.render(screen, 'Options', (20,20))
        font.render(button, "Back", (0,0))
        screen.blit(button, (50,100))
        mx, my = pygame.mouse.get_pos()
        if button.get_rect(topleft=(50,100)).collidepoint((mx,my)):
            if click:
                running = False
        
        click = False
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    click = True
        
        pygame.display.update()
        mainClock.tick(60)

main_menu()
