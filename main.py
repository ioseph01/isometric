import pygame
import random
from utils import sign, load_image

pygame.init()
WIDTH, HEIGHT = 21, 21
TILE_WIDTH, TILE_HEIGHT = 20, 10
WALL_HEIGHT = 4
WALL_SPACING = 4
sprite = "grass"
SCREEN = pygame.display.set_mode((800, 600))
display = pygame.Surface((200,150), pygame.SRCALPHA)
pygame.display.set_caption("Isometric Maze with Stairs")
mode = True
NEIGHBORS = {(-1,0),(0,-1),(1,0),(0,1)}

assets = {
    'grass': load_image('cube.png'),
    'ramp_right': load_image('ramp.png'),
    'ramp_left': pygame.transform.flip(load_image('ramp.png'), True, False),
    'wall': load_image('wall.png'),
    'tile': load_image('trap.png')
}


import random

NEIGHBORS = [(-1,0), (0,-1), (1,0), (0,1)]

def sign(x):
    if x > 0:
        return 1
    elif x < 0:
        return -1
    else:
        return 0
        
def coord_add(a, b):
    return (a[0] + b[0], a[1] + b[1])

def carve(layout, stair_prob=0):
    visited = set()
    rows, cols = len(layout), len(layout[0])
    toVisit = [(cols - 2, rows - 2)]  # Start with just the starting position
    
    def in_range(coord):
        return 0 <= coord[0] < cols and 0 <= coord[1] < rows
    
    # Mark starting position as visited and carve it
    visited.add(toVisit[-1])
    layout[rows - 2][cols - 2] = 0  # 0 represents open space
    max_z, z = 0,0
    while toVisit:
        x, y = toVisit[-1]
        choices = []
        
        # Look for unvisited cells that are 2 steps away
        for n in NEIGHBORS:
            # The cell 2 steps away in this direction
            next_cell = coord_add((x, y), (n[0] * 2, n[1] * 2))
            
            if in_range(next_cell) and next_cell not in visited:
                # The wall between current cell and next cell
                wall = coord_add((x, y), n)
                choices.append((next_cell, wall))
            elif in_range(next_cell):
                z = layout[y][x]
                
        if choices:
            # Choose a random direction to carve
            next_cell, wall = random.choice(choices)
            
            # Add the new cell to visit stack
            toVisit.append(next_cell)
            
            # Mark both the wall and the new cell as visited
            visited.add(next_cell)
            visited.add(wall)
            
            offset = 1 if next_cell[0] < x or next_cell[1] < y else -1
            z = max(0, z + offset) if random.randint(0,100) < stair_prob else z
            offset = 1 if next_cell[0] < wall[0] or next_cell[1] < wall[1] else -1
            z2 = max(0, z + offset) if random.randint(0,100) < stair_prob else z
            # Carve out the wall and the new cell
            layout[wall[1]][wall[0]] = z
            layout[next_cell[1]][next_cell[0]] = z2
        else:
            # Dead end - backtrack
            toVisit.pop()
    
    return layout

def create_maze(width, height, stair_prob=0):
    # Initialize maze with walls (1) and ensure odd dimensions for proper maze structure
    if width % 2 == 0:
        width += 1
    if height % 2 == 0:
        height += 1
    
    # Create maze filled with walls
    maze = [[None for _ in range(width)] for _ in range(height)]
    
    # Carve the maze
    return carve(maze, stair_prob)

def print_maze(maze):
    for x in range(len(maze[0])):
        col = ""
        for y in range(len(maze)):
            if maze[y][x] is not None:
                col += str(maze[y][x])
            else:
                col += "#"
        print(col)



def to_iso(x, y, tile_w, tile_h):
    # Fix the backwards rendering by swapping the x-y calculation
    iso_x = (y - x) * tile_w // 2
    iso_y = (x + y) * tile_h // 2
    
    # Use the same base position for both flat and tall tiles
    return iso_x + 200, iso_y + 50

def draw_block(screen, x, y, h, z=0, offset=(0,0), sprite=sprite):
    iso_x, iso_y = to_iso(x, y, TILE_WIDTH, TILE_HEIGHT)
    iso_y -= z * (TILE_HEIGHT // 2)  # Add this line!
    for i in reversed(range(h)):
        screen.blit(assets[sprite], (iso_x + offset[0], iso_y + offset[1] + WALL_SPACING * i))

    

def draw_map(screen, layout, offset=(0,0)):
    tiles_to_draw = []
    rows = len(layout)
    cols = len(layout[0])
    
    for y in range(rows):
        for x in range(cols):
            tile = layout[y][x]
            if tile is not None:
                tiles_to_draw.append((x + y, x, y, tile))  # z affects depth

                # tiles_to_draw.append((x, y, tile))
    
    tiles_to_draw.sort()
    
    for _, x, y, z in tiles_to_draw:
        draw_block(screen, x, y, WALL_HEIGHT, z, offset)
        

def in_range(pos, maze):
    return 0 <= pos[0] < len(maze[0]) and 0 <= pos[1] < len(maze)

def render(player=None, offset=(0,0)):
    display.fill((40, 0, 40))
    draw_map(display, maze, offset=offset)
    if player is not None:
        draw_block(display, player[0], player[1], 1, maze[player[1]][player[0]], offset=offset, sprite="tile")
        # pos = to_iso(*player, TILE_WIDTH, TILE_HEIGHT)
        # display.blit(assets['grass'], [pos[0], pos[1] + WALL_HEIGHT * 14])
    pygame.transform.scale(display, SCREEN.get_size(), SCREEN)
    pygame.display.flip()
    

def border_check(maze, player, direction):
    sign_ = sign(direction[0]) if sign(direction[0]) != 0 else sign(direction[1]) 
    pos = [player[0] + direction[0], player[1] + direction[1]]
    locs = [10000,*player]
    for i in range(3):
        if in_range((pos[0], pos[1]), maze):
            if maze[pos[1]][pos[0]] is not None:
                tile = maze[player[1]][player[0]]
                ix, iy = to_iso(player[0], player[1], TILE_WIDTH, TILE_HEIGHT)
                iy -= tile * (TILE_HEIGHT // 2)
                
                new_tile = maze[pos[1]][pos[0]]
                i_x, i_y = to_iso(pos[0], pos[1], TILE_WIDTH, TILE_HEIGHT)
                i_y -= new_tile * (TILE_HEIGHT // 2)
                
                dx, dy = abs(ix - i_x), abs(iy - i_y)
                if dx <= 10 and dy <= 10 and dx + dy < locs[0]:
                    print(*player, ix, iy, "-", *pos)
                    locs = [dx + dy, *pos]
            pos = [pos[0] + sign_, pos[1] + sign_]
            
    return locs[1:]
        


# Create maze with room areas that will be flat
maze = create_maze(21,21, stair_prob=25)
print_maze(maze)
render_scroll = [0,0]
player = [1,1]
Z = maze[player[1]][player[0]]
# ------------- Game Loop -------------
clock = pygame.time.Clock()
running = True

while running:
    movement = [0,0]
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            
            if event.key == pygame.K_UP:
                render_scroll[1] += 10
            elif event.key == pygame.K_DOWN:
                render_scroll[1] -= 10
            elif event.key == pygame.K_RIGHT:
                render_scroll[0] -= 10
            elif event.key == pygame.K_LEFT:
                render_scroll[0] += 10
            elif event.key == pygame.K_SPACE:
                mode = not mode
              
            elif event.key == pygame.K_w:
                player = border_check(maze, player, (0,-1))
                movement = [0,-1]
            elif event.key == pygame.K_d:
                movement = [-1,0]
                player = border_check(maze, player, (-1,0))
            elif event.key == pygame.K_s:
                movement = [0,1]
                player = border_check(maze, player, (0,1))
            elif event.key == pygame.K_a:
                movement = [1,0]
                player = border_check(maze, player, (1,0))
            elif event.key == pygame.K_r:
                WALL_SPACING = (WALL_SPACING + 1) % 15
                print(player)
            tile = maze[player[1]][player[0]]
            ix, iy = to_iso(player[0], player[1], TILE_WIDTH, TILE_HEIGHT)
            iy -= tile * (TILE_HEIGHT // 2)
            # print("->", ix, iy, tile)
            render(offset=render_scroll, player=player)
            if event.key in [pygame.K_q,pygame.K_ESCAPE]:
                running = False

    clock.tick(60)

pygame.quit()
