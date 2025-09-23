import os
import pygame

def sign(x):
    if x > 0:
        return 1
    elif x < 0:
        return -1
    else:
        return 0


def coord_add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def load_image(path):
    img = pygame.image.load('img/' + path).convert()
    img.set_colorkey((0,0,0))
    return img

def coord_add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def to_iso(x, y, tile_w, tile_h):
    iso_x = (y - x) * tile_w // 2
    iso_y = (x + y) * tile_h // 2
    
    return iso_x + 200, iso_y + 50

    
def in_range(pos, maze):
    return 0 <= pos[0] < maze.w and 0 <= pos[1] < maze.h
    

def cell_valid(pos, maze):
    '''Checks if in range and if so, if NOT None'''
    if in_range(pos, maze):
        return maze.maze[pos[1]][pos[0]] is not None
    return False

def cell_type(pos, maze, cell_type='Tile'):
    ''' Checks if in range, NOT None, and if given type matches '''
    if cell_valid(pos, maze):
        return cell_type == maze.maze[pos[1]][pos[0]].type
    return False    
