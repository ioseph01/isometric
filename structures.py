import random
from scripts.utils import *


def reduce_coord(x, y):
    if abs(x) <= 1 and abs(y) <= 1:
        return x, y
    if abs(x) > 1:
        return int(x/abs(x)), 0  
    else:
        return 0, int(y/abs(y))   
        
    
class Tile:
    def __init__(self, maze, z, x, y):
        self.maze = maze
        self.pos = z
        self.x, self.y = x, y
        sprite_variant = self.maze.sprite_variant if self.maze.sprite_variant is not None else stable_randint(x, y, z, self.maze.game.level)
        sprite = self.type
        self.sprite = self.maze.assets[sprite][sprite_variant]
       
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
        ''' Returns cells that are connected to the tile '''
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
    

    def get_neighbor(self, dx, dy):
        ''' Gets the neighboring cell in the direction of dx and dy to the tile.
            Assumes dx,dy is reduced
        '''
        def reduce_coord(x, y):
            if abs(x) <= 1 and abs(y) <= 1:
                return x, y
            if abs(x) > 1:
                return int(x/abs(x)), 0  
            else:
                return 0, int(y/abs(y))   
            
        neighbors = self.adjacent_cells
        for n in neighbors:
            x,y = reduce_coord(n.x - self.x, n.y - self.y)
            if x == dx and y == dy:
                return n
        return None
    @property
    def render_pos(self):
        ''' Returns calculated x and y of to_iso adjusted to tile height '''
        iso_x, iso_y = to_iso(self.x, self.y, self.maze.TILE_WIDTH, self.maze.TILE_HEIGHT)
        iso_y -= self.z * (self.maze.TILE_HEIGHT // 2)  
        return [iso_x, iso_y]


    def render(self, screen, h, offset, wall_spacing):
        x,y = self.render_pos
        for i in reversed(range(0,h)):
            screen.blit(self.sprite, (x + offset[0], y + offset[1] + wall_spacing * i))
            
    def update(self):
        pass
    
    def z_check(self, other):
        if self.type != 'Elevator' and other.type != 'Elevator':
            return [other.z - self.z]
        elif other.type == 'Elevator':
            return [other.z2 - self.z, other.z1 - self.z]
        elif self.type == 'Elevator':
            return [other.z - self.z1, other.z - self.z2]
        

    def get_outline(self):
        ''' Returns the points that make up its top grid lines '''
        def generate_points(x_start=0, y_start=0, slope=1, n=10):
            return [(x_start + i, y_start + slope * ((i + 1) // 2)) for i in range(n)]
        
        _ = {
            ( 0,-1): generate_points(x_start=0,  y_start=5,  slope=-1), 
            ( 0, 1): generate_points(x_start=10, y_start=10, slope=-1),
            (-1, 0): generate_points(x_start=10, y_start=0,  slope= 1), 
            ( 1, 0): generate_points(x_start=0,  y_start=5,  slope= 1), 
            }
        border_points = set()
        neighbor_types = ('Elevator', 'Glass_Tile')
        if self.type != 'Elevator':
            neighbors = self.adjacent_cells
            borders = {k for k in _}
                    
            for neighbor in neighbors:
                if neighbor.type not in neighbor_types and abs(neighbor.z1 - self.z1) != 1:
                    dx,dy = reduce_coord(neighbor.x - self.x, neighbor.y - self.y)
                    borders.discard((dx,dy))
                            
            new_surface = self.sprite.copy()
            for dx,dy in borders:
                points = _[(dx,dy)]
                pos = self.render_pos
                border_points |= set([(x + pos[0], y + pos[1]) for x,y in points])

        return border_points


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
        
       
class Glass_Tile(Tile):
    
    def __init__(self, maze, z, x, y):
        self.maze = maze
        self.pos = z
        self.x, self.y = x, y
        self.time = 0
        self.sprite = self.maze.assets[self.type]
        intensity = .6
        alpha = int(255 * intensity)
        self.sprite.set_alpha(alpha)
        self.sprite_grid = pygame.Surface(self.sprite.get_size(), pygame.SRCALPHA)
        for px,py in get_border_points():
            self.sprite_grid.set_at((px,py), (25,20,26))
        
    @property
    def type(self):
        return 'Glass_Tile'
    
    def deactive(self):
        self.time = 600
        print("GN!")
    
    @property
    def active(self):
        return self.time <= 0
        
    def update(self):
        if self.time > 0:
            self.time -= 1
            
            

    def render(self, screen, h, offset, wall_spacing):
        if self.active:
            x,y = self.render_pos
            screen.blit(self.sprite, (x + offset[0], y + offset[1]), special_flags=pygame.BLEND_ALPHA_SDL2)
            screen.blit(self.sprite_grid, (x + offset[0], y + offset[1]))
        

class Player_Tile(Tile):
    def __init__(self, maze, z, x, y):
        self.maze = maze
        self.pos = z
        self.x, self.y = x, y
        self.sprite = self.maze.assets[self.type][0]
        self.time = 60
        self.active = True


    @property
    def type(self):
        return 'Player_Tile'

    def deactivate(self):
        if self.active:
            self.active = False
            self.sprite = self.maze.assets[self.type][1]

    def update(self):
            
        if not self.active:
            if self.time <= 0:
                self.maze.maze[self.y][self.x] = Tile(self.maze, self.z1, self.x, self.y)
                self.maze.maze[self.y][self.x].sprite = self.sprite
                
            else:
                self.time -= 1
            

    
class Enemy_Tile(Tile):
    
    def __init__(self, maze, z, x, y, cooldown=None):
        self.maze = maze
        self.pos = z
        self.x, self.y = x, y
        self.time = cooldown if cooldown is not None else 2
        self.cooldown = cooldown
        self.sprite = self.maze.assets[self.type]
        
    
    @property
    def type(self):
        return 'Enemy_Tile'
    
    @property
    def active(self):
        return self.time > 0
        
    def update(self):
        if self.cooldown is not None:
            if abs(self.time) == 1:
                if self.maze.game.player.pos != [self.x, self.y]:
                    self.time = -self.time * self.cooldown
                    
                    
            else:
                self.time -= sign(self.time)
                
            
    def render(self, screen, h, offset, wall_spacing):
        if self.active:
            sprite = self.sprite[0]
        else:
            sprite = self.sprite[1]

        x,y = self.render_pos
        screen.blit(sprite, (x + offset[0], y + offset[1]))

        
class Gem_Tile(Tile):
    
    def __init__(self, maze, z, x, y):
        self.maze = maze
        self.maze = maze
        self.pos = z
        self.x, self.y = x, y
        self.sprite = self.maze.assets['Gem_Tile']
