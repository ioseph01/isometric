import os
import pygame

def sign(x):
    if x > 0:
        return 1
    elif x < 0:
        return -1
    else:
        return 0

def load_image(path):
    img = pygame.image.load('img/' + path).convert()
    img.set_colorkey((0,0,0))
    return img

def coord_add(a, b):
    return (a[0] + b[0], a[1] + b[1])

def cell_check(pos, maze):
    if pos[0] in range(len(maze[0])) and pos[1] in range(len(maze)):
        return maze[pos[1]][pos[0]] is not None
    return False
