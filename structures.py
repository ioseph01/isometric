import random
from utils import *


class Tile:
    def __init__(self, maze, z, x, y):
        self.maze = maze
        self.pos = z
        self.x, self.y = x, y
        self.sprite_variant = self.maze.sprite_variant if self.maze.sprite_variant is not None else stable_randint(x, y, z, self.maze.game.level)
       
    @property
    def z(self):
        return self.pos
    
    def __lt__(self, other):
        return self.z < other.z
    
    @property
    def type(self):
        return "Tile"

    @property
    def z1(self):
        return self.pos
    
    @property
    def all_z(self):
        return [self.pos]

    @property
    def adjacent_cells(self):
        cells = set()
        dirs = [(-1,0,range(2)),(1,0,range(-1,1)),(0,1,range(-1,1)),(0,-1,range(2)),(2,1,range(1,3)),(1,2,range(1,3)),(-2,-1,range(-2,0)),(-1,-2,range(-2,0))]
        for dx, dy, dz in dirs:
            if not self.maze.in_range([dx + self.x, dy + self.y]):
                continue
            cell = self.maze.maze[dy + self.y][dx + self.x]
            if cell is not None:
                if abs(dx) <= 1 and abs(dy) <= 1:
                    for diff in self.z_check(cell):
                        if diff in dz:
                            cells.add(cell)
                elif abs(dx) >= 1 and abs(dy) >= 1:
                    for diff in self.z_check(cell):
                        if diff in dz:
                            cells.add(cell)
                            

        return cells
    
    @property
    def render_pos(self):
        ''' Returns calculated x and y of to_iso adjusted to tile height '''
        iso_x, iso_y = to_iso(self.x, self.y, self.maze.TILE_WIDTH, self.maze.TILE_HEIGHT)
        iso_y -= self.z * (self.maze.TILE_HEIGHT // 2)  
        return [iso_x, iso_y]


    def render(self, screen, h, offset, wall_spacing):
        x,y = self.render_pos
        for i in reversed(range(h)):
            screen.blit(self.maze.assets[self.type][self.sprite_variant], (x + offset[0], y + offset[1] + wall_spacing * i))
            
    def update(self):
        pass
    
    def z_check(self, other):
        if self.type == 'Tile' and other.type == 'Tile':
            return [other.z - self.z]
        elif other.type == 'Elevator':
            return [other.z2 - self.z, other.z1 - self.z]
        elif self.type == 'Elevator':
            return [other.z - self.z1, other.z - self.z2]


class Elevator(Tile):
    def __init__(self, game, z, other_z, x, y):
        super().__init__(game, int(z), x, y)
        self.z2 = int(other_z)
        self.current_z = z
        self.direction = -1
        self.time_stopped = 0
        
    def __bool__(self): # returns if stopped
        return self.time_stopped <= 0
        
    @property
    def type(self):
        return "Elevator"
    
    @property
    def z(self):
        return self.current_z
        
    @property
    def z1(self):
        return self.pos
    
    @property
    def all_z(self):
        return [self.z1, self.z2]

    def update(self):
        if self.time_stopped <= 0:
            self.current_z += self.direction * 0.1
            self.current_z = round(self.current_z,2)
        
        
            if (self.direction > 0 and self.current_z >= self.pos) or (self.direction < 0 and self.current_z <= self.z2):
                self.direction *= -1
                self.time_stopped = 60
        else:
            self.time_stopped -= 1 

    def render(self, screen, h, offset, wall_spacing):
        super().render(screen, 1, offset, wall_spacing)
            

