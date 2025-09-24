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
    def __init__(self, maze, z, x, y, player_tile=False):
        self.maze = maze
        self.pos = z
        self.x, self.y = x, y
        sprite_variant = stable_randint(x, y, z, self.maze.game.level)
        sprite = self.type
        self.sprite = self.maze.assets[sprite][sprite_variant]
        self.player_tile = player_tile
        self.tile_outline = set()
        self.back_neighbors = []
        
       
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
    
    def rect(self, pos=None, offset=(0,0)):
        x, y = pos if pos is not None else self.render_pos
        ox, oy = offset
        return pygame.Rect(x + ox, y + oy, 20,24)

    def get_accessible_neighbor(self, dx,dy):
        ''' Gets the neighboring cell in the direction of dx and dy to the tile.
            Assumes dx,dy is reduced
        '''
        def reduce_coord(x, y):
            if abs(x) <= 1 and abs(y) <= 1:
                return x, y
            if abs(x) > 1:
                return int(x/abs(x)), 0  
            elif abs(y) > 1:
                return 0, int(y/abs(y))   
            return x,y
        dx,dy = reduce_coord(dx,dy)
        if (cell_valid([dx + self.x, dy + self.y], self.maze)):
            n = self.maze.maze[dy + self.y][dx + self.x]
            for z in self.all_z:
                for other_z in n.all_z:
                    if abs(z - other_z) <= 1:
                        return n
        if (cell_valid([2 * dx + dy + self.x, 2 * dy + dx + self.y], self.maze)):
            n = self.maze.maze[2 * dy + dx + self.y][2 * dx + dy + self.x]
            for z in self.all_z:
                for other_z in n.all_z:
                    if other_z - z == -2:
                        return n
        return None

    def get_neighbor(self, dx, dy):
        ''' Gets the neighboring cell in the direction of dx and dy to the tile.
            Assumes dx,dy is reduced
            Doesn't get if -2 
        '''
        def reduce_coord(x, y):
            if abs(x) <= 1 and abs(y) <= 1:
                return x, y
            if abs(x) > 1:
                return int(x/abs(x)), 0  
            elif abs(y) > 1:
                return 0, int(y/abs(y))   
            return x,y
        dx,dy = reduce_coord(dx,dy)
        
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


    def render(self, screen, h, offset, wall_spacing, rect):
        x,y = self.render_pos
        
        for i in reversed(range(0,h)):
            self_rect = self.rect((x, y + wall_spacing * i),offset)
            if rect.colliderect(self_rect):
                screen.blit(self.sprite, (x + offset[0], y + offset[1] + wall_spacing * i))
            
        self_rect = self.rect((x,y),offset)
        if rect.colliderect(self_rect):
            for px, py in self.tile_outline:
                screen.fill((95,87,79), (px+offset[0],py+offset[1],1,1))
            
    def update(self):
        pass
    
    def z_check(self, other):
        if self.type != 'Elevator' and other.type != 'Elevator':
            return [other.z - self.z]
        elif other.type == 'Elevator':
            return [other.z2 - self.z, other.z1 - self.z]
        elif self.type == 'Elevator':
            return [other.z - self.z1, other.z - self.z2]
        

    def init_outline(self):
        n_types = ('Tile', 'Plant_Tile', 'Player_Tile', 'Enemy_Tile', 'Portal_Tile')
        self.back_neighbors = []
        for dx,dy in [(-1,0),(0,-1)]:
            neighbor = self.get_neighbor(dx,dy)
            if neighbor is not None:
                self.back_neighbors.append( (neighbor.x, neighbor.y) )
        
        self.tile_outline |= self.get_outline()
        
        n0 = False
        n1 = self.get_neighbor(0,1)
        n2 = self.get_neighbor(1,0)
        _n1 = self.get_neighbor(-1,0)
        _n2 = self.get_neighbor(0,-1)
        if n1 is not None:
            if _n1 is None or _n1.type not in n_types or abs(_n1.z1-self.z1) % 2 != 0:        
                if n1.type in n_types:
                    nx,ny = n1.render_pos
                    n1.tile_outline |= {(9+nx,ny),(10+nx,ny)}
        if n2 is not None:
            if _n2 is None or _n2.type not in n_types or abs(_n2.z1-self.z1) % 2 != 0:                
                if n2.type in n_types:
                    nx,ny = n2.render_pos
                    n2.tile_outline |= {(10+nx,ny),(9+nx,ny)}
            

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
        neighbor_types = ('Elevator', 'Glass_Tile', 'Temp_Tile')
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

    def render(self, screen, h, offset, wall_spacing, rect):
        super().render(screen, 1, offset, wall_spacing, rect)
        
       
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
            self.sprite_grid.set_at((px,py), (95,87,79))
        self.back_neighbors = []
        
    @property
    def type(self):
        return 'Glass_Tile'
    
    def deactive(self):
        self.time = 600
    
    @property
    def active(self):
        return self.time <= 0
        
    def update(self):
        if self.time > 0:
            self.time -= 1
            
    def render(self, screen, h, offset, wall_spacing, rect):
        if self.active:
            x,y = self.render_pos
            if self.rect((x,y),offset).colliderect(rect):
                screen.blit(self.sprite, (x + offset[0], y + offset[1]), special_flags=pygame.BLEND_ALPHA_SDL2)
                color = (95,87,79)
            
                for dx,dy in get_border_points():
                    screen.fill(color, (x+dx+offset[0], y+dy+offset[1],1,1))
            # screen.blit(self.sprite_grid, (x + offset[0], y + offset[1]))
        

class Player_Tile(Tile):
    def __init__(self, maze, z, x, y):
        self.maze = maze
        self.pos = z
        self.x, self.y = x, y
        self.sprite = self.maze.assets[self.type][0]
        self.time = 60
        self.active = True
        self.tile_outline = set()
        self.back_neighbors = []

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
                self.maze.maze[self.y][self.x] = Tile(self.maze, self.z1, self.x, self.y, player_tile=True)
                self.maze.maze[self.y][self.x].sprite = self.sprite
                self.maze.maze[self.y][self.x].tile_outline = self.tile_outline
                
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
        self.tile_outline = set()
        self.back_neighbors = []
        
    
    @property
    def type(self):
        return 'Enemy_Tile'
    
    @property
    def active(self):
        return self.time > 0
        
    def update(self):
        if self.cooldown is not None:
            if abs(self.time) == 1:
                if self.maze.game.player.pos == [self.x, self.y] and self.maze.game.player.invincibility <= 0:
                    self.maze.game.player.stun = 10
                self.time = -self.time * self.cooldown
                    
                    
                    
            else:
                self.time -= sign(self.time)
                
            
    def render(self, screen, h, offset, wall_spacing, rect):
        if self.active:
            sprite = self.sprite[0]
        else:
            sprite = self.sprite[1]

        x,y = self.render_pos
        if self.rect((x,y), offset).colliderect(rect):
            screen.blit(sprite, (x + offset[0], y + offset[1]))
            for px, py in self.tile_outline:
                screen.fill((95,87,79), (px+offset[0],py+offset[1],1,1))

        
class Plant_Tile(Tile):
    
    def __init__(self, maze, z, x, y):
        self.maze = maze
        self.pos = z
        self.x, self.y = x, y
        self.sprite = self.maze.assets['Plant_Tile']
        self.occupied = False
        self.back_neighbors = []
        self.tile_outline = set()
        
    @property
    def type(self):
        return 'Plant_Tile'
    

class Portal_Tile(Tile):
    
    def __init__(self, maze, z, x, y):
        self.maze = maze
        self.pos = z
        self.x, self.y = x, y
        self.sprite = self.maze.assets[self.type]
        self.animation = self.maze.assets[self.type + '_']
        self.active = False
        self.tile_outline = set()
        self.back_neighbors = []
        intensity = .6
        alpha = int(255 * intensity)


    @property
    def type(self):
        return 'Portal_Tile'

    def update(self):
        if self.maze.game.player.gems >= 100:
            if self.maze.game.player.pos == [self.x, self.y]:
                self.maze.game.skip = True
            else:
                self.active = True
                self.animation.update()
                
        else:
            self.active = False
            
    def render(self, screen, h, offset, wall_spacing, rect):
        sprite = self.sprite
        
        if self.active:
            sprite = self.animation.img()

        x,y = self.render_pos
        for i in reversed(range(0,h // 2)):
            self_rect = self.rect((x,wall_spacing * i + y), offset)
            screen.blit(sprite, (x + offset[0], y + offset[1] + wall_spacing * i))
        if self.rect((x,y), offset).colliderect(rect):
            for px, py in self.tile_outline:
                screen.fill((95,87,79), (px+offset[0],py+offset[1],1,1))
            

class Temp_Tile(Tile):
    def __init__(self, maze, z, x, y):
        self.maze = maze
        self.pos = z
        self.x, self.y = x, y
        self.sprite = self.maze.assets['Temp_Tile']
        self.back_neighbors = []
        for dx,dy in [(0,1),(1,0)]:
            n = self.get_neighbor(dx,dy)
            if n is not None:
                n.back_neighbors.append((self.x,self.y))
        

    def render(self, screen, h, offset, wall_spacing, rect):
        x,y = self.render_pos
        if self.rect((x,y), offset).colliderect(rect):
            screen.blit(self.sprite, (x + offset[0], y + offset[1]))
        
    @property
    def type(self):
        return 'Temp_Tile'

STRUCTURE_MAP = {
    "Tile": Tile,
    "Glass_Tile": Glass_Tile,
    "Player_Tile": Player_Tile,
    "Enemy_Tile": lambda maze, z, x, y: Enemy_Tile(maze, z, x, y, maze.enemy_cooldown(x, y)),
    "Plant_Tile": Plant_Tile,
    "Temp_Tile": Temp_Tile,
    "Portal_Tile": Portal_Tile,
}
def structures_factory(maze, struct_type, z, x, y):
    try:
        return STRUCTURE_MAP[struct_type](maze, z, x, y)
    except KeyError:
        raise ValueError(f"Unknown structure type: {struct_type}")
