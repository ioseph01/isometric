import pygame
import random
from scripts.noise import pnoise2
from scripts.animation import Animation
from scripts.structures import Elevator, Enemy_Tile, Glass_Tile, Player_Tile, Tile, structures_factory
from scripts.utils import *

NEIGHBORS = [(-1,0), (0,-1), (1,0), (0,1)]

class Maze:
    def __init__(self, game, width, height, gem_asset, color_table=None, stair_prob=0, room_attempts=0, sparsity=[0,0], elevator_prob=0,
                 friendlies_prob=0, enemies_prob=0, enemies_cooldown=None, glass_prob=0, wall_height=4):
        self.game = game
        self.maze = self.create_maze(width, height)
        self.width = width 
        self.height = height
        self.TILE_WIDTH, self.TILE_HEIGHT = 20, 10
        self.wall_height = wall_height
        
        self.init_settings = {
            'width': width, 'height': height, 'stair_probability': stair_prob, 'room attempts': room_attempts,
            'sparsity setting': sparsity, 'elevator_prob': elevator_prob, 'friendlies_prob': friendlies_prob, 'enemies_prob': enemies_prob,
            'glass_prob': glass_prob
            }
        self.load_assets(color_table, gem_asset)
        self.render_counter = 0
        self.render_mode = True

        self.enemy_tile_cooldown = enemies_cooldown
        self.maze = self.generate_rooms(room_attempts)
        self.combine(self.carve(self.maze, stair_prob=stair_prob), self.carve(self.create_maze(self.width, self.height)), sparsity=sparsity, friendlies_prob=friendlies_prob, enemies_prob=enemies_prob, glass_prob=glass_prob)
        self.maze = self.fix_maze(self.maze)
        self.add_elevators(elevator_prob)
        
        for i in range(10):
            self.init_settings['elevator_prob'] = max(i * 10 + elevator_prob, elevator_prob, 15)
            # self.maze = self.fix_maze(self.maze)
            if not self.connectivity() or self.trace([1,1], [self.w - 2, self.h - 2]) == []:
                self.add_elevators(i * 10 + elevator_prob)
                self.maze = self.fix_maze(self.maze)
            else:
                # self.maze = self.fix_maze(self.maze)
                break
        else:
            raise RuntimeError
        

    def enemy_cooldown(self, x=0, y=0):
        if self.enemy_tile_cooldown == 0:
            result = pnoise2(x / self.w, y / self.h, octaves=1, base=self.game.level)
            return int(round(3 + ((result + 1) / 2) * 57)) * 10
        return self.enemy_tile_cooldown

    @property
    def settings(self):
        return self.init_settings

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

    @property
    def dim(self):
        return (self.width, self.height)
    
    def load_assets(self, color_table, gem_asset):
        self.assets = {
            'Tile': [replace_colors(img, color_table) for img in load_images('tiles')],
            'Tile_Cover': load_image('tile_cover.png'),
            'Elevator': [replace_colors(img, color_table) for img in load_images('elevators')],
            'Player_Tile': [replace_colors(img, color_table) for img in load_images('player_tiles')],
            'Enemy_Tile': [replace_colors(img, color_table) for img in load_images('enemy_tiles')],
            'Glass_Tile': load_image('glass_tile.png'),
            'Plant_Tile': replace_colors(load_image('plant_tile.png'), color_table),
            'Plant_Cover': replace_colors(load_image('plant_cover.png'), color_table),
            'Portal_Tile_': Animation([replace_colors(img, color_table) for img in load_images('portal_tiles/active')], img_dur=30),
            'Portal_Tile': replace_colors(load_image('portal_tiles/off/0.png'), color_table),
            'Gem': gem_asset,
            'Temp_Tile': replace_colors(load_image('elevators/0.png'), color_table)
        }
        
    def create_maze(self, width, height):
        if width % 2 == 0:
            width += 1
        if height % 2 == 0:
            height += 1
    
        return [[None for _ in range(width)] for _ in range(height)]

        
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
        
                if layout[cy][cx] == ".":
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
        def check(a,b, comparator=max):
            coords = []
            if a is not None:
                coords.append(a)
            if b is not None:
                coords.append(b)
            if len(coords) <= 0:
                return None
            return comparator(coords)
            
        for row_i, row in enumerate(maze):
            for cell_i, cell in enumerate(row):
                if cell is not None:
                    if cell.type == 'Elevator':
                        top = check(cell.get_accessible_neighbor(-1,0), cell.get_accessible_neighbor(0,-1),min)
                        bottom = check(cell.get_accessible_neighbor(1,0), cell.get_accessible_neighbor(0,1),max)
                        if top is not None and bottom is not None and (top.all_z[-1] - bottom.z1 >= 2):
                            cell.pos = top.all_z[-1]
                            cell.other_z = bottom.z1
                        elif bottom is None:    
                            self.maze[row_i][cell_i] = Tile(self, cell.z1, cell_i, row_i)
                        else:
                            self.maze[row_i][cell_i] = Tile(self, cell.z2, cell_i, row_i)
                               
                    for dx in range(-1,100):
                    
                        dy = dx + 1 if dx > -1 else 1
                        dz = dx + dy if dx > -1 else 1
                        dx = abs(dx)
                        offset = 0 if dx < 3 else 1
                        if (a:= in_range([cell_i + dx, row_i + dy], self)):
                            to_check = maze[row_i + dy][cell_i + dx]
                            if to_check is not None:
                                if to_check.z - cell.z > dz - 1 and cell.type != 'Elevator':
                                    # maze[row_i + dy][cell_i + dx] = Tile(self, max(0, cell.z + dz - offset - random.choice([1,2,2,2,2,2])), cell_i + dx, row_i + dy)
                                    maze[row_i + dy][cell_i + dx] = structures_factory(self, cell.type, max(0, cell.z + dz - offset - random.choice([1,2,2,2,2,2])), cell_i + dx, row_i + dy)
                            
                        if (b:= in_range([cell_i + dy, row_i + dx], self)):
                            to_check = maze[row_i + dx][cell_i + dy]
                            if to_check is not None:
                                if to_check.z - cell.z > dz - 1  and cell.type != 'Elevator':
                                    maze[row_i + dx][cell_i + dy] = structures_factory(self, cell.type, max(0, cell.z + dz - offset - random.choice([1,2,2,2,2,2])), cell_i + dy, row_i + dx)
                        if not a and not b:
                            break
                        

             
        self.maze = maze
        # if self.settings['friendlies_prob'] >= 50 or self.settings['enemies_prob'] >= 50:
        if self.trace((1,1), (self.w - 2, self.h - 2)) != []:
            for px, py, pz in self.trace((1,1), (self.w - 2, self.h - 2)) + self.trace((self.w - 2, self.h - 2), (1,1)):
                cell = self.maze[py][px]
                if cell.type in ('Enemy_Tile', 'Player_Tile'):
                    self.maze[py][px] = random.choices([structures_factory(self, 'Tile', pz, px, py), structures_factory(self, 'Glass_Tile', pz, px, py)], weights=[80,5], k=1)[0]
                        
        return self.maze

    def add_elevators(self, probability=80):
        if probability <= 0:
            return
        maze = self.maze
        def check(a,b, tile_type, comparator=max):
            coords = []
            if get_cell_type(a, self) not in (None, 'Elevator'):
                coords.append(maze[a[1]][a[0]])
            if get_cell_type(b, self) not in (None, 'Elevator'):
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
                        if (maze[row_i][cell_i - 1] is not None or maze[row_i - 1][cell_i]) is not None:
                            other = check([cell_i, row_i + 1], [cell_i + 1, row_i], 'Tile')
                            if other is None:
                                other = check([cell_i + 2, row_i + 1], [cell_i + 1, row_i + 2], 'Tile')
                                if other is not None:
                                    diag = maze[row_i + 1][cell_i + 1].z1 if cell_valid([cell_i + 1, row_i + 1], self) else 0
                                    if cell.z - other.z1 >= 2 and probability > random.randint(0,100) and diag + 1 <= other.z1:
                                        maze[row_i][cell_i] =  Elevator(self, cell.z, max(0, other.z - 1), cell_i, row_i)
                            elif cell.z - other.z >= 2 and probability > random.randint(0,100):
                                maze[row_i][cell_i] =  Elevator(self, cell.z, other.z, cell_i, row_i)

    

    def combine(self, layout, other, sparsity, friendlies_prob=0, enemies_prob=0, glass_prob=0, preserve_current=False):
        
        def makeTile(z,x,y):
            return Tile(self, z,x,y)
        
        def makePlayerTile(z,x,y):
            return Player_Tile(self, z, x, y)

        def makeEnemyTile(z,x,y):
            return Enemy_Tile(self,z,x, y, self.enemy_cooldown(x,y))
           
        def makeGlassTile(z,x,y):
            return Glass_Tile(self, z,x,y)
        
        
        if sparsity == [0,0]:
            return
        
        new_tiles = []
        for y in range(1, len(other) - 1):
            for x in range(1, len(layout[y]) - 1):
                if preserve_current and self.maze[y][x] is not None:
                            continue
                tile = makeTile
                if (layout[y][x] is None or None is other[y][x]):
                    if random.randint(0,100) < sparsity[0]:
                        tile = makeTile
                        if random.randint(0,100) < glass_prob:
                            tile = makeGlassTile
                        elif random.randint(0,100) < friendlies_prob and (x,y) :
                            tile = makePlayerTile
                        elif random.randint(0,100) < enemies_prob and (x,y):
                            tile = makeEnemyTile
                        for z in [layout[y][x], layout[y - 1][x], layout[y][x - 1]]:
                            if z is not None:
                                layout[y][x] = tile(z.z1, x, y)
                                break
                        continue
                            
                    if x != 0 and x != len(layout[0]) - 1 and y != 0 and y != len(layout) - 1 and x % 2 != 1 and y % 2 != 1:
                        
                        if random.randint(0,100) < sparsity[1]:
                            tile = makeTile
                            if random.randint(0,100) < glass_prob:
                                tile = makeGlassTile
                            elif random.randint(0,100) < friendlies_prob and (x,y):
                                tile = makePlayerTile
                            elif random.randint(0,100) < enemies_prob and (x,y):
                                tile = makeEnemyTile
                            
                            for z in [layout[y][x - 1], layout[y - 1][x]]:
                                if z is not None:
                                    layout[y][x] = tile(z.z1, x, y)
                                    break
    
        self.maze = layout
        return new_tiles

    

    def draw_map(self, screen, offset=(0,0), entities={}, border_layer=None, rect=None, paused=False):
        ''' Maze render function '''
        if self.render_counter >= self.rows * self.cols and self.render_mode:
            
            screen.blit(self.static_surface,(offset[0] + self.offset[0], offset[1] + self.offset[1]))
            for x,y in self.animated_tiles:
                self.maze[y][x].render(screen,rect,offset)
            for x,y in self.elevator_tiles:
                self.maze[y][x].render(screen,rect,offset)
            for x,y in self.glass_tiles:
                self.maze[y][x].render(screen,rect,offset)
            for y in range(self.h):
                for x in range(self.w):
                    cell = self.maze[y][x]
                    if cell is not None:
                        cell.update()
                        if (x,y) in entities:
                            for e in entities[(x,y)]:
                                e.render(screen,offset, rect)
            
            return
        counter = 0
        for y in range(self.h):
            for x in range(self.w):
                if counter >= self.render_counter:
                    self.render_counter += 1
                    return
                tile = self.maze[y][x]
                if tile is not None:
                    
                    if not paused and self.w*self.h <= self.render_counter:
                        tile.update()
                    if tile.type in ("Enemy_Tile", "Portal_Tile"):
                        pass
                    else:
                        tile.render(screen, rect, offset)
                    if (x,y) in entities:
                        for e in entities[(x,y)]:
                            e.render(screen, offset, rect)
                            
                    for nx, ny in tile.back_neighbors:
                        if (nx,ny) in entities:
                            if self.maze[ny][nx].z <= tile.z:
                                for entity in entities[(nx,ny)]:
                                    entity.render(screen, offset,rect)
                counter += 1
                    


    def border_check(self, player, direction):
        if direction == [0,0]:
            if self.maze[player[1]][player[0]].type == 'Tile':
                return player, [0,0]
        elif self.maze[player[1]][player[0]].type == 'Elevator':
            if self.maze[player[1]][player[0]].time_stopped > 50:
                return player,[0,0]
            
        sign_ = sign(direction[0]) if sign(direction[0]) != 0 else sign(direction[1]) 
        if abs(direction[0]) == 2 or abs(direction[1]) == 2:
            direction = [direction[0] - sign_, direction[1] - sign_]
        elif abs(direction[0]) == 1 and abs(direction[1]) == 1:
            direction = random.choice(([direction[0], 0],[0,direction[1]]))
        pos = [player[0] + direction[0], player[1] + direction[1]]
        locs = [10000,*player]
        diff = [0,0]
        for i in range(21):
            if not self.in_range(pos):
                return locs[1:], diff
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
                
                if dx <= 10 and dy <= 10 and dx + dy + abs(new_tile - tile) < locs[0]:
                    locs = [dx + dy + abs(new_tile - tile), *pos]
                    diff = [i_x - ix, i_y - iy]
            pos = [pos[0] + sign_, pos[1] + sign_]
        return locs[1:], diff
        


    def trace(self, player, target, limit=1000):
        
        x,y = player
        target_x, target_y = target
    
        if self.maze[y][x].type != 'Elevator':
            visited = {(x, y, self.maze[y][x].z)}
            paths = [[(x, y, self.maze[y][x].z)]]
        else:
            visited = {(x, y, self.maze[y][x].z1)}
            paths = [[(x, y, self.maze[y][x].z1)]]
            visited.add((x, y, self.maze[y][x].z2))
            paths += [[(x, y, self.maze[y][x].z2)]]
        
        if player == target:
            return [(*player, self.maze[target[1]][target[0]].z1)]
        
        WALKABLES = ('Enemy_Tile', 'Tile', 'Elevator', 'Glass_Tile', 'Plant_Tile', 'Temp_Tile')
        while len(paths) > 0 :
            
            current = paths.pop(-1)
            x, y, z = current[-1]
            
            if x == target_x and y == target_y:
                return current
            
            visited.add((x, y, z))
            if len(current) > limit:
                continue
            
            toAdd = {}
            
            dirs = [(-1,0,range(2)),(1,0,range(-1,1)),(0,1,range(-1,1)),(0,-1,range(2)),(2,1,range(1,3)),(1,2,range(1,3)),(-2,-1,range(-2,0)),(-1,-2,range(-2,0))]
            for dx,dy,dz in dirs:
                if in_range((x + dx, y + dy), self):
                    cell = self.maze[y + dy][x + dx]
                    
                    if cell != None:
                        if cell.type not in WALKABLES:
                            continue
                        if cell.type != 'Elevator' and self.maze[y][x].type != 'Elevator':
                            if cell.z - self.maze[y][x].z not in dz or (x + dx, y + dy, cell.z) in visited:
                                continue
                        elif cell.type != 'Elevator' and self.maze[y][x].type == 'Elevator':
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
                        elif cell.type != 'Elevator':
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
                    
                    
            all_positions = [
                (dist + random.random(), pos)
                for dist, vals in toAdd.items()
                for pos in vals
            ]

            for _, pos in reversed(sorted(all_positions)):
                if pos not in visited:
                    visited.add(pos)
                    paths.append(current + [pos])
        return []

    def generate_gems(self, gems:int, gemstones:int):
        gem_locs = set()
        gemstone_locs = set()
        
        GRID_WIDTH = 40
        GRID_HEIGHT = 40

        SCALE = 15.0
        THRESHOLD = -.15
        CLUSTER_ATTEMPTS = 100
        CLUSTER_SIZE = (2, 5)

        noise_map = [[pnoise2(x / SCALE, y / SCALE, octaves=3)
                      for x in range(GRID_WIDTH)] for y in range(GRID_HEIGHT)]

        for _ in range(CLUSTER_ATTEMPTS):
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)

            if noise_map[y][x] > THRESHOLD:
                num_plants = random.randint(*CLUSTER_SIZE)
                for _ in range(num_plants):
                    dx = int(random.gauss(0, 2))
                    dy = int(random.gauss(0, 2))
                    nx, ny = x + dx, y + dy
                    if (nx,ny) == (1,1) or (nx,ny) == (self.w - 2, self.h - 2):
                        continue
                    
                    if cell_type((nx, ny), self):
                        if 1 == len(self.maze[ny][nx].adjacent_cells) and len(gemstone_locs) < gemstones:
                            gemstone_locs.add((nx,ny))
                        elif len(gem_locs) < gems:   
                            gem_locs.add((nx, ny))
                        else:
                            return gem_locs, gemstone_locs
                        
        return gem_locs, gemstone_locs


    def set_tile_outline(self):
        self.animated_tiles = set()
        self.elevator_tiles = set()
        self.glass_tiles = set()
        
        for i,row in enumerate(self.maze):
            for j,tile in enumerate(row):
                if tile is not None:
                    if tile.type in ('Tile', 'Player_Tile', 'Enemy_Tile', 'Plant_Tile', 'Portal_Tile'):
                        tile.init_outline()
                        
        x0, x1 = 20000000, 0
        y0, y1 = 20000000, 0
        for col in self.maze:
            for cell in col:
                if cell is not None:
                    x,y = cell.render_pos
                    x0 = min(x0, x)
                    y0 = min(y0, y)
                    x1 = max(x1, x)
                    y1 = max(y1, y)
        x1 *= 2
        y1 *= 2
        self.offset = (x0, y0)
        self.static_surface = pygame.Surface((x1-x0, y1-y0), pygame.SRCALPHA)
        rect = pygame.Rect(0,0,1000000,10000000)
        for col in self.maze:
            for cell in col:
                if cell is not None:
                    x,y = cell.render_pos
                    if cell.type not in ("Elevator", "Glass_Tile"):
                        
                            cell.render(self.static_surface,rect,[-self.offset[0],-self.offset[1]])
                            
                    if cell.type not in ('Player_Tile', 'Tile', 'Plant_Tile', 'Temp_Tile'):
                        if cell.type == 'Elevator':
                            self.elevator_tiles.add((cell.x,cell.y))
                        else:
                            if cell.type != 'Glass_Tile':
                                self.animated_tiles.add((cell.x,cell.y))
                                Tile(self,cell.z1,cell.x,cell.y).render(self.static_surface, rect, [-self.offset[0], -self.offset[1]])
                            else:
                                self.glass_tiles.add((cell.x,cell.y))
                                cell.time = 0

        self.glass_tiles = sorted(list(self.glass_tiles))
        self.animated_tiles = sorted(list(self.animated_tiles))
        self.elevator_tiles = sorted(list(self.elevator_tiles))
        

    

    def get_spawnpoints(self, x, y, count):
        if cell_type([x,y], self):
            visited = set()
            spawn_points = set()
            toVisit = [(x,y)]
            while toVisit and len(spawn_points) < count:
                cx,cy = toVisit.pop(0)
                if (cx, cy) in visited:
                    continue
                cell = self.maze[cy][cx]
                visited.add((cx,cy))
                for next_cell in cell.adjacent_cells:
                    pos = (next_cell.x, next_cell.y)
                    
                    if pos not in spawn_points:
                        if next_cell.type in ('Tile', 'Plant_Tile', 'Glass_Tile'):
                            spawn_points.add((next_cell.x, next_cell.y))
                            if len(spawn_points) >= count:
                                return spawn_points
                    if pos not in visited:
                        toVisit.append(pos)
            return spawn_points
        return []


    def connectivity(self):
        ALL = {(j.x, j.y) for row in self.maze for j in row if j is not None}
        if not ALL:
                return False
        
        visited = set()
        start = next(iter(ALL))  
        toVisit = {start}
        while toVisit:
            x,y = toVisit.pop()
            if (x, y) in visited:
                continue
            visited.add((x,y))
            cell = self.maze[y][x]
            for dx,dy in NEIGHBORS:
                adjacent = cell.get_accessible_neighbor(dx,dy)
                if adjacent is None:
                    continue
                if (adjacent.x, adjacent.y) not in visited:
                    toVisit.add((adjacent.x, adjacent.y))
                    
        return ALL == visited
        

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
                    col += symbol(int(self.maze[y][x].z))
                else:
                    col += "#"
            print(col)
        print(spacing, end="")

        