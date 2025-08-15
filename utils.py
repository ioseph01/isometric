import os
import pygame
from hashlib import md5


def sign(x):
    if x > 0:
        return 1
    elif x < 0:
        return -1
    else:
        return 0


def coord_add(a, b):
    return (a[0] + b[0], a[1] + b[1])


BASE_IMG_PATH = 'img/'

def load_image(path):
    img = pygame.image.load(BASE_IMG_PATH + path).convert()
    img.set_colorkey((0,0,0))
    return img


def load_images(path):
    images = []
    for img_name in sorted(os.listdir(BASE_IMG_PATH + path)):
        images.append(load_image(path + '/' + img_name))
        
    return images


def replace_colors(surface, color_map):
    """Replaces all pixels matching old_color with new_color given color map; preserves alpha."""
    
    if color_map is None:
        return surface
    new_surface = surface.copy()
    width, height = new_surface.get_size()

    for x in range(width):
        for y in range(height):
            current_color = new_surface.get_at((x, y))
            new_rgb = color_map.get(current_color[:3])
            if new_rgb:
                new_surface.set_at((x, y), new_rgb + (current_color[3],))  

    return new_surface


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


def stable_randint(x, y, z, level, min_val=0, max_val=3):

    s = f"{x},{y},{z},{level}"
    h = md5(s.encode()).digest()
    val = int.from_bytes(h[:4], 'little')
    return val % (max_val - min_val + 1) + min_val
