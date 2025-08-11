import pygame
import random
from structures import Elevator, Tile
from utils import *

NEIGHBORS = [(-1,0), (0,-1), (1,0), (0,1)]

class Maze:
    def __init__(self, game, width, height, tile_asset, elevator_asset, stair_prob=0, room_attempts=0, sparsity=[0,0], elevator_prob=0):
        self.game = game
        self.maze = self.create_maze(width, height)
        self.width = width
        self.height = height
        self.TILE_WIDTH, self.TILE_HEIGHT = 20, 10
        self.WALL_HEIGHT = 4
        self.WALL_SPACING = 4
        self.assets = {
            'Tile': self.game.assets[tile_asset],
            'Elevator': self.game.assets[elevator_asset],
        }
        print(self.assets['Tile'])
        print(self.assets['Elevator'])
        
        self.maze = self.generate_rooms(room_attempts)
        self.maze = self.combine(self.carve(self.maze, stair_prob=stair_prob), self.carve(self.create_maze(width, height)), sparsity=sparsity)
        self.maze = self.fix_maze(self.maze)
        self.add_elevators(elevator_prob)
        for i in range(10):
            print("Attempt", i)
            if self.trace([1,1], [width - 2, height - 2]) is None:
                self.add_elevators(i * 10 + elevator_prob)
            else:
                break
        else:
            raise RuntimeError

    @property
    def cols(self):
        return self.width

    @property
    def rows(self):
        return self.height
    
    @property
    def w(self):
        return self.width

    @property
    def h(self):
        return self.height


    def in_range(self, coord):
        return 0 <= coord[0] < self.w and 0 <= coord[1] < self.h


    def dim(self):
        return (self.width, self.height)
        
    def create_maze(self, width, height):
        if width % 2 == 0:
            width += 1
        if height % 2 == 0:
            height += 1
    
        return [[None for _ in range(width)] for _ in range(height)]


    
    def print_maze(self, spacing=""):
        def symbol(i):
            if i >= 10:
                return ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
                 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
                 'U', 'V', 'W', 'X', 'Y', 'Z'][int((i - 10) % 26)]
            return str(i)
            
        for x in range(self.cols):
            col = ""
            for y in range(self.rows):
                if self.maze[y][x] is not None:
                    col += symbol(self.maze[y][x].z)
                else:
                    col += "#"
            print(col)
        print(spacing, end="")

        
    def add_room(self, x, y, w, h):
        if x % 2 == 1 and y % 2 == 1 and w % 2 == 0 and h % 2 == 0:
            if in_range((x, y), self) and in_range((x + w, y + h), self):
                for i in range(h):
                    for j in range(w):
                        self.maze[y + i][x + j] = "."
                    
            return self.maze
        
    def generate_rooms(self, attempts=1):
        rooms = []
        if attempts <= 0:
            return self.maze
        for attempt in range(attempts):
            x,y,w,h = random.randint(0,((self.cols - 3) // 2)) * 2 + 1, random.randint(0,(self.rows - 3) // 2) * 2 + 1, random.randint(2, 6), random.randint(2,6)
            print(x,y,w,h)
            if x + w < len(self.maze[0]) - 2 and y + h < len(self.maze) - 2:
                room = pygame.Rect(x,y,w,h)
                for r in rooms:
                    if r.colliderect(room):
                        break
                else:
                    rooms.append(room)
                    self.add_room(x,y,w,h)    
               
        return self.maze



    def carve(self, layout, stair_prob=0):
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
                elif (self.maze[y][x] != None):
                    for i in range(len(queue) - 1):
                        self.maze[queue[i][0]][queue[i][1]] = Tile(self, self.maze[y][x].z1, x, y)
                    return
            
                visited.add((x, y))
        
                # Add neighbors
                for dx, dy in [(0,1), (1,0)]:
                    queue.append((x + dx, y + dy))

    

        def fill_room(start, z_val):
            stack = [start]
            seen = set()
            while stack:
                cx, cy = stack.pop()
                if (cx, cy) in seen:
                    continue
                seen.add((cx, cy))
        
                if self.in_range((cx, cy)) and layout[cy][cx] == ".":
                    layout[cy][cx] = Tile(self, z_val, cx, cy)
                    for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
                        nx, ny = cx + dx, cy + dy
                        if self.in_range((nx, ny)):
                            stack.append((nx, ny))
                        
            return seen

    
        visited.add(toVisit[-1])
        layout[rows - 2][cols - 2] = Tile(self, 0, cols - 2, rows - 2)
        z = 0
        while toVisit:
            x, y = toVisit[-1]
            choices = []
        
            # Look for unvisited cells that are 2 steps away
            for n in NEIGHBORS:
                next_cell = coord_add((x, y), (n[0] * 2, n[1] * 2))
            
                if self.in_range(next_cell) and next_cell not in visited:
                    wall = coord_add((x, y), n)
                    choices.append((next_cell, wall))
                elif self.in_range(next_cell):
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
                    layout[wall[1]][wall[0]] = Tile(self, z, wall[0], wall[1])

                if layout[next_cell[1]][next_cell[0]] == ".":
                    visited.update(fill_room(next_cell, z))
                else:
                    layout[next_cell[1]][next_cell[0]] = Tile(self, z2, next_cell[0], next_cell[1])

        
            else:
                toVisit.pop()
            

            
        if layout[1][1] is None:
            connect_to_start()
        
    
        return layout


    def fix_maze(self, maze):
        for row_i, row in enumerate(maze):
            for cell_i, cell in enumerate(row):
                if cell is not None:
                    for dx in range(-1,100):
                    
                        dy = dx + 1 if dx > -1 else 1
                        dz = dx + dy if dx > -1 else 1
                        dx = abs(dx)
                        offset = 0 if dx < 3 else 1
                        if (a:= in_range([cell_i + dx, row_i + dy], self)):
                            to_check = maze[row_i + dy][cell_i + dx]
                            if to_check is not None:
                                if to_check.z - cell.z > dz - 1:
                                    maze[row_i + dy][cell_i + dx] = Tile(self, max(0, cell.z + dz - offset - random.choice([1,2,2,2,2,2])), cell_i + dx, row_i + dy)
                            
                        if (b:= in_range([cell_i + dy, row_i + dx], self)):
                            to_check = maze[row_i + dx][cell_i + dy]
                            if to_check is not None:
                                if to_check.z - cell.z > dz - 1:
                                    maze[row_i + dx][cell_i + dy] = Tile(self, max(0, cell.z + dz - offset - random.choice([1,2,2,2,2,2])), cell_i + dy, row_i + dx)
                        if not a and not b:
                            break
                        
                                
        return maze

    def add_elevators(self, probability=80):
        if probability <= 0:
            return
        maze = self.maze
        def check(a,b, tile_type, comparator=max):
            coords = []
            if cell_type(a, self, tile_type):
                coords.append(maze[a[1]][a[0]])
            if cell_type(b, self, tile_type):
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
                        if in_range([cell_i + dx, row_i + dy], self):
                            if cell_type((cell_i + dx, row_i + dy), self, 'Elevator'):
                                break
                    else:
                        if (maze[row_i][cell_i - 1] is not None or maze[row_i - 1][cell_i]):
                            other = check([cell_i, row_i + 1], [cell_i + 1, row_i], 'Tile')
                            if other is None:
                                other = check([cell_i + 2, row_i + 1], [cell_i + 1, row_i + 2], 'Tile')
                                if other is not None:
                                    diag = maze[row_i + 1][cell_i + 1].z1 if cell_valid([cell_i + 1, row_i + 1], self) else 0
                                    if cell.z - other.z1 >= 2 and probability > random.randint(0,100) and diag + 1 <= other.z1:
                                        maze[row_i][cell_i] =  Elevator(self, cell.z, max(0, other.z - 1), cell_i, row_i)
                                        print(cell_i,row_i, cell.z1)
                            elif cell.z - other.z >= 2 and probability > random.randint(0,100):
                                maze[row_i][cell_i] =  Elevator(self, cell.z, other.z, cell_i, row_i)

    

    def combine(self, layout, other, sparsity):
        for y in range(1, len(other) - 1):
            for x in range(1, len(layout[y]) - 1):
                
                if (layout[y][x] is None or None is other[y][x]) and random.randint(0,100) < sparsity[0]:
                    for z in [layout[y][x], layout[y - 1][x], layout[y][x - 1]]:
                        if z is not None:
                            layout[y][x] = Tile(self,z.z, x, y)
                            break

                if  random.randint(0, 100 ) < sparsity[1] and x != 0 and x != len(layout[0]) - 1 and y != 0 and y != len(layout) - 1 and x % 2 != 1 and y % 2 != 1:
                    for z in [layout[y][x - 1], layout[y - 1][x]]:
                        if z is not None:
                            layout[y][x] = Tile(self,z.z, x, y)
                            break
    
        return layout

    

    def draw_map(self, screen, offset=(0,0)):
        ''' Maze render function '''
        for y in range(self.h):
            for x in range(self.w):
                tile = self.maze[y][x]
                if tile is not None:
                    tile.update()
                    tile.render(screen, self.WALL_HEIGHT, offset, self.WALL_SPACING)


    def border_check(self, player, direction):
        if direction == [0,0]:
            if self.maze[player[1]][player[0]].type == 'Tile':
                return player, [0,0]
        elif self.maze[player[1]][player[0]].type == 'Elevator':
            if self.maze[player[1]][player[0]].time_stopped >= 50:
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
            if cell_valid(pos, self):
                current = self.maze[player[1]][player[0]]
                tile = current.z
                ix, iy = current.render_pos
                if current.type == 'Elevator':
                    if current.time_stopped <= 10:
                        continue
                    
                other = self.maze[pos[1]][pos[0]]
                new_tile = other.z
                i_x, i_y = other.render_pos
                dx, dy = abs(ix - i_x), abs(iy - i_y)
                
                if dx <= 10 and dy <= 10 and dx + dy + abs(new_tile - tile) < locs[0] and i >= abs(new_tile - tile) - 1:
                    locs = [dx + dy + abs(new_tile - tile), *pos]
                    diff = [i_x - ix, i_y - iy]
            pos = [pos[0] + sign_, pos[1] + sign_]
        return locs[1:], diff
        


    def trace(self, player, target):
        
        x,y = player
        target_x, target_y = target
    
        if self.maze[y][x].type == 'Tile':
            visited = {(x, y, self.maze[y][x].z)}
            paths = [[(x, y, self.maze[y][x].z)]]
        else:
            visited = {(x, y, self.maze[y][x].z1)}
            paths = [[(x, y, self.maze[y][x].z1)]]
            visited.add((x, y, self.maze[y][x].z2))
            paths += [[(x, y, self.maze[y][x].z2)]]
        
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
                if in_range((x + dx, y + dy), self):
                    cell = self.maze[y + dy][x + dx]

                    if cell != None:
                        if cell.type == 'Tile' and self.maze[y][x].type == 'Tile':
                            if cell.z - self.maze[y][x].z not in dz or (x + dx, y + dy, cell.z) in visited:
                                continue
                        elif cell.type == 'Tile' and self.maze[y][x].type == 'Elevator':
                            closer_z = self.maze[y][x].z1 if abs(self.maze[y][x].z1 - cell.z) < abs(self.maze[y][x].z2 - cell.z) else self.maze[y][x].z2
                            if (cell.z - z not in dz) or (x + dx, y + dy, closer_z) in visited:
                                continue
                        elif cell.type == 'Elevator':
                            closer_z = cell.z1 if abs(self.maze[y][x].z - cell.z1) < abs(self.maze[y][x].z - cell.z2) else cell.z2
                            if (cell.z2 - self.maze[y][x].z not in dz and cell.z1 - self.maze[y][x].z not in dz) or (x + dx, y + dy, closer_z) in visited:
                                continue
                        # k = sign(dx) if dx != 0 else sign(dy)
                        k = abs(target_x - x - dx) + abs(target_y - y - dy)
                        if k not in toAdd:
                            toAdd[k] = []
                        if cell.type == 'Elevator':
                            closer_z = cell.z1 if abs(self.maze[y][x].z - cell.z1) < abs(self.maze[y][x].z - cell.z2) else cell.z2
                            toAdd[k].append((x + dx, y + dy, closer_z))
                        elif cell.type == 'Tile':
                            toAdd[k].append((x + dx, y + dy, cell.z))
                        
            if self.maze[y][x].type == 'Elevator':
                if z == self.maze[y][x].z1:
                
                    k = abs(target_x - x - 1) + abs(target_y - y - 1)
                    if k not in toAdd:
                        toAdd[k] = [(x,y,self.maze[y][x].z2)]
                    else:
                        toAdd[k].append((x,y,self.maze[y][x].z2))
                elif z == self.maze[y][x].z2:
                    k = abs(target_x - x + 1) + abs(target_y - y + 1)
                    if k not in toAdd:
                        toAdd[k] = [(x,y,self.maze[y][x].z1)]
                    else:
                        toAdd[k].append((x,y,self.maze[y][x].z1))
                    
                    
            for key in reversed(dict(sorted(toAdd.items()))):
                for val in random.sample(toAdd[key], len(toAdd[key])):
                    if val not in visited:
                        paths.append(current + [val])
     


