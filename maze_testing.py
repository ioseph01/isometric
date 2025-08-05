import pygame
import random
from structures import Elevator, Tile
from utils import cell_type, cell_valid, sign, load_image

pygame.init()
WIDTH, HEIGHT = 21, 21
TILE_WIDTH, TILE_HEIGHT = 20, 10
WALL_HEIGHT = 4
WALL_SPACING = 4
sprite = "block"
SCREEN = pygame.display.set_mode((800, 600))
display = pygame.Surface((200,150), pygame.SRCALPHA)
display = pygame.Surface((400,300), pygame.SRCALPHA)
pygame.display.set_caption("Isometric Maze with Stairs")
mode = True
NEIGHBORS = {(-1,0),(0,-1),(1,0),(0,1)}
offset = [0,0]

assets = {
    'elevator': load_image('elevator1.png'),
    'block': load_image('block.png'),
    'block1': load_image('block1.png'),
    'block2': load_image('block2.png'),
    'block3': load_image('block3.png'),
    'block4': load_image('block4.png'),
    'block5': load_image('block5.png'),
    'entity': load_image('ball.png'),
    'ramp_right': load_image('ramp.png'),
    'ramp_left': pygame.transform.flip(load_image('ramp.png'), True, False),
    'wall': load_image('wall.png'),
    'tile': load_image('gem.png')
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
    toVisit = [(1,1), (cols - 2, rows - 2)]  # Init with corners
    
    def connect_to_start():
        visited = set()
        queue = [(1,1)]  
    
        while queue:
            x, y, = queue[-1]
        
            if (x,y) in visited:
                continue
            elif (maze[y][x] != None):
                for i in range(len(queue) - 1):
                    maze[queue[i][0]][queue[i][1]] = Tile(None,maze[y][x].z1,sprite)
                return
            
            visited.add((x, y))
        
            # Add neighbors
            for dx, dy in [(0,1), (1,0)]:
                queue.append((x + dx, y + dy))

    
    def in_range(coord):
        return 0 <= coord[0] < cols and 0 <= coord[1] < rows


    def fill_room(start, z_val):
        stack = [start]
        seen = set()
        while stack:
            cx, cy = stack.pop()
            if (cx, cy) in seen:
                continue
            seen.add((cx, cy))
        
            if in_range((cx, cy)) and layout[cy][cx] == ".":
                layout[cy][cx] = Tile(None, z_val, sprite)
                for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
                    nx, ny = cx + dx, cy + dy
                    if in_range((nx, ny)):
                        stack.append((nx, ny))
                        
        return seen

    
    visited.add(toVisit[-1])
    layout[rows - 2][cols - 2] = Tile(None, 0, sprite)
    z = 0
    while toVisit:
        x, y = toVisit[-1]
        choices = []
        
        # Look for unvisited cells that are 2 steps away
        for n in NEIGHBORS:
            next_cell = coord_add((x, y), (n[0] * 2, n[1] * 2))
            
            if in_range(next_cell) and next_cell not in visited:
                wall = coord_add((x, y), n)
                choices.append((next_cell, wall))
            elif in_range(next_cell):
                z = layout[y][x].z if layout[y][x] is not None else z
                
        if choices:
            # Choose a random direction to carve
            next_cell, wall = random.choice(choices)
            
            # Add the new cell to visit stack
            toVisit.append(next_cell)
            
            # Mark both the wall and the new cell as visited
            visited.add(next_cell)
            visited.add(wall)
            

            offset = 1 if next_cell[0] < x or next_cell[1] < y else -1
            z = max(0, z + offset) if random.randint(0,100) < stair_prob and layout[next_cell[1]][next_cell[0]] != "." else z
            offset = 1 if next_cell[0] < wall[0] or next_cell[1] < wall[1] else -1
            z2 = max(0, z + offset) if random.randint(0,100) < stair_prob and layout[wall[1]][wall[0]] != "." else z
            
            if layout[wall[1]][wall[0]] == ".":
                visited.update(fill_room(wall, z))
            else:
                layout[wall[1]][wall[0]] = Tile(None, z, sprite)

            if layout[next_cell[1]][next_cell[0]] == ".":
                visited.update(fill_room(next_cell, z))
            else:
                layout[next_cell[1]][next_cell[0]] = Tile(None, z2, sprite)

        
        else:
            toVisit.pop()
            

            
    if maze[1][1] is None:
        connect_to_start()
        
    
    return layout


def fix_maze(maze):
    nothing_to_change = True
    for row_i, row in enumerate(maze):
        for cell_i, cell in enumerate(row):
            if cell is not None:
                for dx in range(-1,100):
                    
                    dy = dx + 1 if dx > -1 else 1
                    dz = dx + dy if dx > -1 else 1
                    dx = abs(dx)
                    offset = 0 if dx < 3 else 1
                    if (a:= in_range([cell_i + dx, row_i + dy], maze)):
                        to_check = maze[row_i + dy][cell_i + dx]
                        if to_check is not None:
                            if to_check.z - cell.z > dz - 1:
                                nothing_to_change = False
                                maze[row_i + dy][cell_i + dx] = Tile(None, max(0, cell.z + dz - offset - random.choice([1,2,2,2,2,2])),sprite)
                            
                    if (b:= in_range([cell_i + dy, row_i + dx], maze)):
                        to_check = maze[row_i + dx][cell_i + dy]
                        if to_check is not None:
                            if to_check.z - cell.z > dz - 1:
                                nothing_to_change = False
                                maze[row_i + dx][cell_i + dy] = Tile(None, max(0, cell.z + dz - offset - random.choice([1,2,2,2,2,2])), sprite)
                    if not a and not b:
                        break
                        
                                
    if nothing_to_change:
        print("Nothing changed")
    else:
        print("Maze 'fixed'")
            
    return maze

def add_elevators(maze, probability=80):
    if probability <= 0:
        return
    
    def check(a,b, tile_type, comparator=max):
        coords = []
        if cell_type(a, maze, tile_type):
            coords.append(maze[a[1]][a[0]])
        if cell_type(b, maze, tile_type):
            coords.append(maze[b[1]][b[0]])
        if len(coords) <= 0:
            return None
        return comparator(coords)

    for row_i, row in enumerate(maze):
        for cell_i, cell in enumerate(row):
            
            if cell is not None:
                if cell.type == 'Elevator':
                    continue
                for dx, dy in NEIGHBORS:
                    if in_range([cell_i + dx, row_i + dy], maze):
                        if cell_type((cell_i + dx, row_i + dy), maze, 'Elevator'):
                            break
                else:
                    if (maze[row_i][cell_i - 1] is not None or maze[row_i - 1][cell_i]):
                        other = check([cell_i, row_i + 1], [cell_i + 1, row_i], 'Tile')
                        if other is None:
                            other = check([cell_i + 2, row_i + 1], [cell_i + 1, row_i + 2], 'Tile')
                            if other is not None:
                                diag = maze[row_i + 1][cell_i + 1].z1 if cell_valid([cell_i + 1, row_i + 1], maze) else 0
                                if cell.z - other.z1 >= 2 and probability > random.randint(0,100) and diag + 1 <= other.z1:
                                    maze[row_i][cell_i] =  Elevator(None, cell.z, "A", max(0, other.z - 1))
                                    print(cell_i,row_i, cell.z1)
                        elif cell.z - other.z >= 2 and probability > random.randint(0,100):
                            maze[row_i][cell_i] =  Elevator(None, cell.z, "A", other.z)
                        

def create_maze(width, height, stair_prob=0):
    if width % 2 == 0:
        width += 1
    if height % 2 == 0:
        height += 1
    
    return [[None for _ in range(width)] for _ in range(height)]
    

def print_maze(maze, spacing=""):
    def symbol(i):
        if i >= 10:
            return ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
             'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
             'U', 'V', 'W', 'X', 'Y', 'Z'][int((i - 10) % 26)]
        return str(i)
            
    for x in range(len(maze[0])):
        col = ""
        for y in range(len(maze)):
            if maze[y][x] is not None:
                col += symbol(maze[y][x].z)
            else:
                col += "#"
        print(col)
    print(spacing, end="")


def add_room(x, y, w, h, maze):
    if x % 2 == 1 and y % 2 == 1 and w % 2 == 0 and h % 2 == 0:
        if in_range((x, y), maze) and in_range((x + w, y + h), maze):
            for i in range(h):
                for j in range(w):
                    maze[y + i][x + j] = "."
                    
        return maze


def generate_rooms(maze, attempts=1):
    rooms = []
    for attempt in range(attempts):
        x,y,w,h = random.randint(0,((len(maze[0]) - 3) // 2)) * 2 + 1, random.randint(0,(len(maze) - 3) // 2) * 2 + 1, random.randint(2, 6), random.randint(2,6)
        print(x,y,w,h)
        if x + w < len(maze[0]) - 2 and y + h < len(maze) - 2:
            room = pygame.Rect(x,y,w,h)
            for r in rooms:
                if r.colliderect(room):
                    break
            else:
                rooms.append(room)
                add_room(x,y,w,h, maze)    
               
    return maze
            
            

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

    

def draw_map(screen, layout, offset=(0,0), sprite='block'):
    tiles_to_draw = []
    rows = len(layout)
    cols = len(layout[0])
    
    for y in range(rows):
        for x in range(cols):
            tile = layout[y][x]
            if tile is not None:
                if isinstance(tile, Elevator):
                    tile.update()
                    tile = tile.current_z
                    draw_block(screen, x, y, 1, tile, offset, sprite='elevator')
                    
                else:
                    tile = tile.z
                    draw_block(screen, x, y, WALL_HEIGHT, tile, offset, sprite=sprite)
                
        

def in_range(pos, maze):
    return 0 <= pos[0] < len(maze[0]) and 0 <= pos[1] < len(maze)

def render(maze, player=None, offset=(0,0), entities=[], sprite='block'):
    dz = 0

    display.fill((40, 0, 40))
    draw_map(display, maze, offset=offset, sprite=sprite)
    if player is not None:
        tile = maze[player[1]][player[0]]
        if isinstance(tile, Elevator):
            if tile.time_stopped <= 0:
                dz = .5 * tile.direction
        
        draw_block(display, player[0], player[1], 1, tile.z, offset=[offset[0], offset[1]], sprite="tile")
        # pos = to_iso(*player, TILE_WIDTH, TILE_HEIGHT)
        # display.blit(assets['grass'], [pos[0], pos[1] + WALL_HEIGHT * 14])
    for e in entities:
        print(maze[e[1]][e[0]].z)
        print( [offset[0], offset[1] - 12], "entity")
        draw_block(display, e[0], e[1], 1, maze[e[1]][e[0]].z, offset=[offset[0], offset[1] - 12], sprite="entity")
    pygame.transform.scale(display, SCREEN.get_size(), SCREEN)
    pygame.display.flip()
    
    return dz
    

def border_check(maze, player, direction):
    if direction == [0,0]:
        if maze[player[1]][player[0]].type == 'Tile':
            return player, [0,0]
    elif maze[player[1]][player[0]].type == 'Elevator':
        if maze[player[1]][player[0]].time_stopped >= 50:
            return player,[0,0]
            
    sign_ = sign(direction[0]) if sign(direction[0]) != 0 else sign(direction[1]) 
    if abs(direction[0]) == 2 or abs(direction[1]) == 2:
        direction = [direction[0] - sign_, direction[1] - sign_]
    elif abs(direction[0]) == 1 and abs(direction[1]) == 1:
        direction = random.choice(([direction[0], 0],[0,direction[1]]))
    pos = [player[0] + direction[0], player[1] + direction[1]]
    locs = [10000,*player]
    diff = [0,0]
    for i in range(2):
        if in_range((pos[0], pos[1]), maze):
            if maze[pos[1]][pos[0]] is not None:
                tile = maze[player[1]][player[0]].z
                ix, iy = to_iso(player[0], player[1], TILE_WIDTH, TILE_HEIGHT)
                iy -= tile * (TILE_HEIGHT // 2)
                
                if maze[pos[1]][pos[0]].type == 'Elevator':
                    if maze[pos[1]][pos[0]].time_stopped <= 10:
                        continue
                new_tile = maze[pos[1]][pos[0]].z
                i_x, i_y = to_iso(pos[0], pos[1], TILE_WIDTH, TILE_HEIGHT)
                i_y -= new_tile * (TILE_HEIGHT // 2)
                
                dx, dy = abs(ix - i_x), abs(iy - i_y)
                
                if dx <= 10 and dy <= 10 and dx + dy + abs(new_tile - tile) < locs[0] and i >= abs(new_tile - tile) - 1:
                    locs = [dx + dy + abs(new_tile - tile), *pos]
                    diff = [i_x - ix, i_y - iy]
            pos = [pos[0] + sign_, pos[1] + sign_]
    return locs[1:], diff
        


def trace(player, target, maze):
        
    x,y = player
    target_x, target_y = target
    
    if maze[y][x].type == 'Tile':
        visited = {(x, y, maze[y][x].z)}
        paths = [[(x, y, maze[y][x].z)]]
    else:
        visited = {(x, y, maze[y][x].z1)}
        paths = [[(x, y, maze[y][x].z1)]]
        visited.add((x, y, maze[y][x].z2))
        paths += [[(x, y, maze[y][x].z2)]]
        
    if player == target:
        return [(player)]
        
    while len(paths) > 0 :
            
        current = paths.pop(-1)
        x, y, z = current[-1]
            
        if x == target_x and y == target_y:
            return current
            
        visited.add((x, y, z))
            
        toAdd = {}
            
        dirs = [(-1,0,range(2)),(1,0,range(-1,1)),(0,1,range(-1,1)),(0,-1,range(2)),(2,1,range(1,3)),(1,2,range(1,3)),(-2,-1,range(-2,0)),(-1,-2,range(-2,0))]
        for dx,dy,dz in dirs:
            if in_range((x + dx, y + dy), maze):
                cell = maze[y + dy][x + dx]

                if cell != None:
                    if cell.type == 'Tile' and maze[y][x].type == 'Tile':
                        if cell.z - maze[y][x].z not in dz or (x + dx, y + dy, cell.z) in visited:
                            continue
                    elif cell.type == 'Tile' and maze[y][x].type == 'Elevator':
                        closer_z = maze[y][x].z1 if abs(maze[y][x].z1 - cell.z) < abs(maze[y][x].z2 - cell.z) else maze[y][x].z2
                        if (cell.z - z not in dz) or (x + dx, y + dy, closer_z) in visited:
                            continue
                    elif cell.type == 'Elevator':
                        closer_z = cell.z1 if abs(maze[y][x].z - cell.z1) < abs(maze[y][x].z - cell.z2) else cell.z2
                        if (cell.z2 - maze[y][x].z not in dz and cell.z1 - maze[y][x].z not in dz) or (x + dx, y + dy, closer_z) in visited:
                            continue
                    # k = sign(dx) if dx != 0 else sign(dy)
                    k = abs(target_x - x - dx) + abs(target_y - y - dy)
                    if k not in toAdd:
                        toAdd[k] = []
                    if cell.type == 'Elevator':
                        closer_z = cell.z1 if abs(maze[y][x].z - cell.z1) < abs(maze[y][x].z - cell.z2) else cell.z2
                        toAdd[k].append((x + dx, y + dy, closer_z))
                    elif cell.type == 'Tile':
                        toAdd[k].append((x + dx, y + dy, cell.z))
                        
        if maze[y][x].type == 'Elevator':
            if z == maze[y][x].z1:
                
                k = abs(target_x - x - 1) + abs(target_y - y - 1)
                if k not in toAdd:
                    toAdd[k] = [(x,y,maze[y][x].z2)]
                else:
                    toAdd[k].append((x,y,maze[y][x].z2))
            elif z == maze[y][x].z2:
                k = abs(target_x - x + 1) + abs(target_y - y + 1)
                if k not in toAdd:
                    toAdd[k] = [(x,y,maze[y][x].z1)]
                else:
                    toAdd[k].append((x,y,maze[y][x].z1))
                    
                    
        for key in reversed(dict(sorted(toAdd.items()))):
            for val in random.sample(toAdd[key], len(toAdd[key])):
                if val not in visited:
                    paths.append(current + [val])
     


def combine(layout, other, sparsity):
    for y in range(1, len(other) - 1):
        for x in range(1, len(layout[y]) - 1):
                
            if (layout[y][x] is None or None is other[y][x]) and random.randint(0,100) < sparsity[0]:
                for z in [layout[y][x], layout[y - 1][x], layout[y][x - 1]]:
                    if z is not None:
                        layout[y][x] = Tile(None,z.z,sprite)
                        break

            if  random.randint(0, 100 ) < sparsity[1] and x != 0 and x != len(layout[0]) - 1 and y != 0 and y != len(layout) - 1 and x % 2 != 1 and y % 2 != 1:
                for z in [layout[y][x - 1], layout[y - 1][x]]:
                    if z is not None:
                        layout[y][x] = Tile(None,z.z,sprite)
                        break
    
    return layout


def test(maze, display):
    # Get player's world position
    player_x, player_y = 1, 1
    player_z = maze[1][1].z  # or however you access the z value

    # Calculate where the player would appear on screen without any scrolling
    player_screen_x, player_screen_y = to_iso(player_x, player_y, TILE_WIDTH, TILE_HEIGHT)
    player_screen_y -= player_z * (TILE_HEIGHT // 4)  # Account for height

    # Calculate the center of your display surface
    center_x = display.get_width() // 2   # 100 for your 200px wide surface
    center_y = display.get_height() // 2  # 75 for your 150px tall surface

    # Set render_scroll to move the player to the center
    return [center_x - player_screen_x, center_y - player_screen_y]


def reset():
    w,h = random.randint(3,11) * 2 + 1, random.randint(3,11) * 2 + 1
    maze = create_maze(w,h)
    maze = carve(generate_rooms(maze, random.randint(0,10)), stair_prob=random.randint(-20,100))
    other = carve(create_maze(w,h),0)
    print("RESET", len(maze), len(maze[0]), len(other), len(other[0]))
    maze = combine(maze, other, (random.randint(0,100),random.randint(0,100)))
    fix_maze(maze)
    player = [1,1]
    print_maze(maze)
    render_scroll = test(maze, display)
    path = trace(player, (w - 2, h - 2), maze)
    if path is None or path == []:
        add_elevators(maze, 100)
        path = trace(player, (w - 2, h - 2), maze)

    return {'w': w, 'h': h, 'maze': maze, 'player': player, 'scroll': render_scroll, 'path': path, 'sprite': random.choice(( 'block', 'block1', 'block2', 'block3', 'block4', 'block5',))}
###############################################################################################################################################################
###############################################################################################################################################################
###############################################################################################################################################################

maze = create_maze(21,21)
maze = carve(generate_rooms(maze, 10), stair_prob=25)
# maze = carve(maze, stair_prob=15)
# maze = combine(maze, carve(create_maze(21,21), 0), (10,50))
print_maze(maze, "\n ==================================================== \n")

# maze = fix_maze(maze)
# print_maze(maze, "\n ==================================================== \n")

player = [1,1]
entity = [19,19]
entity_path = []
path = []
# ------------- Game Loop -------------
clock = pygame.time.Clock()
running = True
movement = [False, False, False, False]
tick = [0,60]

render_scroll = to_iso(player[0],player[1], TILE_WIDTH, TILE_HEIGHT)
render_scroll = [-1 * render_scroll[0] // 2, render_scroll[1]]

while running:
    tick[0] = (tick[0] + 1) % tick[1]
    diff = [0,0]
    if tick[0] % 5 == 0:
        
        if path == [] or path is None:
            new_player, diff = border_check(maze, player, [movement[1] - movement[3], movement[0] - movement[2]])

        else:
            next_coord = path[0]
            cell, next_cell = maze[player[1]][player[0]], maze[next_coord[1]][next_coord[0]]
            if next_cell.z == next_coord[2]:
                new_player, diff = border_check(maze, player, [next_coord[0] - player[0], next_coord[1] - player[1]])
                
                # if (cell.type == 'Tile' or next_cell.type == 'Tile' and diff[:2] != [0,0]) or (type(diff[1]) == float):
                if list(next_coord[:2]) == new_player:
                    path.pop(0)
        # print(diff)
        render_scroll[1] -= diff[1]
        render_scroll[0] -= diff[0]
        player = new_player
    
    if player == [WIDTH - 2, HEIGHT - 2] and tick[0] == 0:
        r = reset()
        WIDTH = r['w']
        HEIGHT = r['h']
        maze = r['maze']
        player = r['player']
        render_scroll = r['scroll']
        path = r['path']
        sprite = 'block1'
        print(sprite)
    # print(sprite)
    # if entity_path == [] or entity_path is None:
    #     entity_path = trace(entity, player, maze)
    # elif tick[0] % 5 == 0:
    #     entity = entity_path.pop(0)
    
        
    render_scroll[1] += render(maze, offset=render_scroll, player=player, entities=[], sprite=sprite)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e:
                add_elevators(maze, probability=60)
            if event.key == pygame.K_p:
                print_maze(maze, spacing="\n=============0====================\n")
            if event.key == pygame.K_c:
                    
                    maze = create_maze(WIDTH,HEIGHT)
                    maze = carve(generate_rooms(maze, 100), stair_prob=100)
                    # maze = carve(maze, stair_prob=15)
                    maze = combine(maze, carve(create_maze(WIDTH,HEIGHT), 0), (10,50))
                    print_maze(maze)
                    player = [1,1]
                    render_scroll = test(maze, display)
                    print(render_scroll, "pos player")
                    path = []

            if event.key == pygame.K_b:
                for i in range(100):
                    WIDTH, HEIGHT = random.randint(3,10) * 2 + 1, random.randint(3,10) * 2 + 1
                    print(WIDTH,HEIGHT)
                    maze = create_maze(WIDTH, HEIGHT)
                    maze = carve(generate_rooms(maze, random.randint(0,10)), stair_prob=random.randint(-20,100))
                    maze = combine(maze, carve(create_maze(WIDTH,HEIGHT), 0), (random.randint(0,100),random.randint(0,100)))
                    fix_maze(maze)
                    player = [1,1]
                    print_maze(maze)
                    render_scroll = test(maze, display)
                    print(render_scroll, "pos player")
                    path = trace(player, (WIDTH - 2, HEIGHT - 2), maze)
                    if (path is None):
                        print("ATTEMPT", i + 1, '#')
                        break
                    
                continue

            if event.key == pygame.K_t:
                print(path := trace(player, (WIDTH - 2, HEIGHT - 2), maze))
                
            if event.key == pygame.K_SPACE:
                player = [1,1]
                fix_maze(maze)
                print_maze(maze, "\n=====================================\n")
                render_scroll = test(maze, display)
                print(render_scroll)
                
            if event.key == pygame.K_UP:
                render_scroll[1] += 10
                print(render_scroll)
                
            elif event.key == pygame.K_DOWN:
                render_scroll[1] -= 10
                print(render_scroll)
                
            elif event.key == pygame.K_RIGHT:
                render_scroll[0] -= 10
                print(render_scroll)
                
            elif event.key == pygame.K_LEFT:
                render_scroll[0] += 10
                print(render_scroll)
            elif event.key == pygame.K_SPACE:
                mode = not mode
              
            if event.key == pygame.K_w:
                movement[2] = True
            elif event.key == pygame.K_d:
                movement[3] = True
            elif event.key == pygame.K_s:
                movement[0] = True
            elif event.key == pygame.K_a:
                movement[1] = True
            if event.key == pygame.K_r:
                WALL_SPACING = (WALL_SPACING + 1) % 46
                print(player)
                
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_w:
                movement[2] = False
            if event.key == pygame.K_d:
                movement[3] = False
            if event.key == pygame.K_s:
                movement[0] = False
            if event.key == pygame.K_a:
                movement[1] = False
            
            
            tile = maze[player[1]][player[0]].z
            ix, iy = to_iso(player[0], player[1], TILE_WIDTH, TILE_HEIGHT)
            iy -= tile * (TILE_HEIGHT // 2)
            # print("->", ix, iy, tile)
            if event.key in [pygame.K_q,pygame.K_ESCAPE]:
                running = False
    

    clock.tick(60)

pygame.quit()
