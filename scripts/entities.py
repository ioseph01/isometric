
from scripts.maze import NEIGHBORS
from scripts.utils import cell_type, cell_valid, get_cell_type, in_range, sign, to_iso, stable_randint
from scripts.structures import Enemy_Tile, Player_Tile, Tile, structures_factory
import pygame
import random 

def move(pos, dx, dy):
    new_x, new_y = pos[0] + dx, pos[1] + dy
    if abs(new_y) + abs(new_x) / 2 > 4:
        return [pos[0] - 8 * sign(new_x), pos[1] - 4 * sign(new_y)]
    return [new_x, new_y]

def in_tile(pos, dx, dy, R=5):
    return abs(pos[0] + dx) / 2 + abs(pos[1] + dy) <= R

def coord_transform(x,y):
    result = [-2*x + 2*y, x + y]
    return [-2*x + 2*y, x + y]

def change_color(img, color):
        mask = pygame.mask.from_surface(img)
        mask = mask.to_surface(unsetcolor=(0, 0, 0, 0), setcolor=(*color, 255))
        eyes = []
        for x in range(img.get_width()):
            for y in range(img.get_height()):
                if img.get_at((x,y)) == (251,255,235,255):
                    eyes.append((x,y))

        for ix,iy in eyes:
            mask.fill((251,255,235),(ix,iy,1,1))
        return mask

colors = [
        (255,0,77),(255,108,36),(255,236,39),(0,228,54),(6,90,181),(126,37,83)
    ]


def wrap_to_diamond_grid(x, y, R=5):
    """
    Wrap any (x, y) into the infinite diamond grid and return
    the diamond center and relative coordinates inside it.
    """
    # The diamond lattice: center spacing
    DX = 2 * R  # x offset between adjacent diamonds
    DY = R      # y offset between adjacent diamonds
    
    # First, compute which "lattice cell" in x and y we are in
    # This maps x, y to a coordinate system of diamond centers
    # The diamond at 0,0 is the main diamond
    # Diamond lattice vectors: (+10,+5), (+10,-5)
    
    # Solve for integer lattice coordinates i, j
    # lattice vectors: a = (10,5), b = (10,-5)
    # x = 10*(i+j), y = 5*(i-j) -> i = (x/10 + y/5)/2, j = (x/10 - y/5)/2
    i = round((x/DX + y/DY)/2)
    j = round((x/DX - y/DY)/2)
    
    # Compute center of diamond
    cx = DX*(i + j)
    cy = DY*(i - j)
    
    # Compute relative coordinates inside this diamond
    rx = x - cx
    ry = y - cy
    
    # Make sure point is inside diamond (project to boundary if necessary)
    if abs(rx/2) + abs(ry) > R:
        scale = R / (abs(rx/2) + abs(ry))
        rx *= scale
        ry *= scale
    
    return {
        "center": (cx, cy),
        "rel_coords": [rx, ry]
    }

class Entity:
    def __init__(self, game, pos, sprite, hp=1, render_offset=[0,0], e_type=None):
        self.game = game
        self.pos = list(pos)
        self.sprite = sprite
        self.path = []
        self.hp = 1
        self.render_offset = render_offset
        self.movement_offset = [0,0]
        self.type = e_type
        self.flip = False
        self.tick = 8
        self.active = True
        self.gems = 0

    def rect(self,pos=None, offset=(0,0)):
        x,y = pos if pos is not None else self.render_pos
        w,h = self.img.get_size()
        return pygame.Rect(x + offset[0] + self.movement_offset[0] + self.render_offset[0],y + offset[1] + self.movement_offset[1] + self.render_offset[1],w,h)

    @property
    def img(self):
        return self.sprite

    @property
    def mask(self):
        return pygame.mask.from_surface(pygame.transform.flip(self.img, self.flip, False))

    @property
    def at(self):
        return self.game.maze.maze[self.y][self.x]

    @property
    def x(self):
        return self.pos[0]
    
    @property
    def y(self):
        return self.pos[1]
    
    @property
    def render_pos(self):
        ''' Returns calculated x and y of to_iso adjusted to tile height '''
        iso_x, iso_y = to_iso(self.x, self.y, self.game.maze.TILE_WIDTH, self.game.maze.TILE_HEIGHT)
        iso_y -= self.at.z * (self.game.maze.TILE_HEIGHT // 2)  
        return [iso_x, iso_y]
    

    def cutout(self, img):
        
        x,y = self.render_pos
        x = round(x) + self.render_offset[0] + self.movement_offset[0]
        y = round(y) + self.render_offset[1] + self.movement_offset[1]
        if self.game.maze.render_mode:
            for dy in range(0,3):
                for dx in range(0,3):
                    if dx == 0 and dy == 0:
                        continue
                    if not self.game.maze.in_range((self.x + dx, self.y + dy)):
                        continue
                    neighbor = self.game.maze.maze[dy + self.y][dx + self.x]
                    if neighbor is not None:
                        if neighbor.type != "Glass_Tile" and (self.at.z < neighbor.z):
                            ox, oy = neighbor.render_pos

                            diff = (ox - x, oy - y)
                            overlap = self.mask.overlap_mask(neighbor.mask, diff)
                            if overlap.count() > 0:
                                result = self.mask.copy()
                                result.erase(overlap, (0, 0))
                                cutout = result.to_surface(setcolor=(255, 255, 255, 255),
                                                            unsetcolor=(0, 0, 0, 0))
                                cutout.set_colorkey((0, 0, 0))
                                img.blit(cutout, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        return img

    def render(self, screen, offset, rect):
        x,y = self.render_pos
        if self.rect((x,y),offset).colliderect(rect):
            screen.blit(self.cutout(pygame.transform.flip(self.sprite, self.flip, False)), (x + offset[0] + self.render_offset[0] + self.movement_offset[0], int(y) + offset[1] + self.render_offset[1] + self.movement_offset[1]))


    def update(self):
        pass
        
class Gemstone(Entity):
    def __init__(self, game, pos, sprite, hp=1, render_offset=[0, 0], e_type=None):
        super().__init__(game, pos, sprite, hp, render_offset, e_type)
        self.tick = [0,200]

    def update(self):
        self.tick[0] = (self.tick[0] + 1) % self.tick[1]
        if self.pos == self.game.player.pos:
            self.hp = 0
            self.game.player.invincibility = min(100 + self.game.level + (5 - self.game.lives) * 2, 150)
            
    def render(self, screen, offset, rect):
        i = (self.tick[0] % (20 * len(colors))) // 20
        img = change_color(self.sprite,colors[i])
        x,y = self.render_pos
        if self.rect((x,y),offset).colliderect(rect):
            screen.blit(pygame.transform.flip(img, self.flip, False), (x + offset[0] + self.render_offset[0] + self.movement_offset[0], int(y) + offset[1] + self.render_offset[1] + self.movement_offset[1]))


class Trap(Entity):
    def __init__(self, game, pos, sprite, hp=1, render_offset=[0, 0], e_type=None):
        super().__init__(game, pos, sprite, hp, render_offset, e_type)
        self.hp = 100
        self.tick = [0,10]
    
    def update(self):
        self.tick[0] = (self.tick[0] + 1) % self.tick[1]
        if self.tick[0] % self.tick[1] == 0:
            self.hp -= 1
        if self.pos == self.game.player.pos:
            if self.game.player.invincibility <= 0:
                self.game.player.stun += 4
                self.game.player.gems = max(0, self.game.player.gems - 1)
                self.game.sound[0] = self.game.sounds['trap']
            self.hp = 0
            
    
class Gem(Entity):

    def update(self):
        if self.pos == self.game.player.pos:
            self.hp = 0


class Player(Entity):
    
    def __init__(self, game, pos, sprite, hp=1, render_offset=[0, 0], e_type=None):
        super().__init__(game, pos, sprite, hp, render_offset, e_type)
        self.idle = 0
        self.stun = 0
        self.egg = None
        self.egg_offset = [0,0]
        self.action = 'idle'
        self.invincibility = 0
        self.tick = 2
        self.cooldown = 10
        self.z = self.at.z
        self.gems = 0
        self.test = True


    def reset(self):
        self.path = []
        self.idle = 0
        self.action = 'idle'
        self.stun = 0
        self.egg = None
        self.z = stable_randint(self.x, self.y, self.at.z, self.game.level, min_val=0, max_val=6)
        self.movement_offset = [0,0]
        self.invincibility = 0

    def create_egg(self):
        if self.at.type not in ('Glass_Tile','Enemy_Tile') and self.gems >= self.cooldown:
            self.egg_offset = self.movement_offset    
            self.egg = self.pos
            self.gems -= self.cooldown
            if self.game.controller.sfx:
                self.game.sounds['create_egg'].play()

            
    def destroy_egg(self):
        if self.egg is not None:
            self.pos = self.egg
            self.game.render_offset = self.game.test()
            if self.game.controller.sfx:
                self.game.sounds['destroy_egg'].play()
            
        self.egg = None
        
    @property
    def img(self):
        if self.action == 'walking' or self.idle > 100:
            return self.sprite.img()
        return self.sprite.images[0]

    def render(self, screen, offset, rect):
        x,y = self.render_pos
        x += offset[0] + self.movement_offset[0] + self.render_offset[0]
        y += offset[1] + self.movement_offset[1] + self.render_offset[1]

        if self.action == 'walking' or self.idle > 0:
            img = self.sprite.img()
            
            if self.invincibility > 0:
                img = change_color(img, colors[self.game.tick[0] % len(colors)])

            screen.blit(self.cutout(pygame.transform.flip(img, self.flip, False)), (x,y))
        # elif self.idle > 100:
        #     screen.blit(pygame.transform.flip(self.sprite.img(), self.flip, False), (x,y))
        else:
            img = self.sprite.images[0]
            if self.invincibility > 0:
                img = change_color(img, colors[self.game.tick[0] % len(colors)])

            screen.blit(self.cutout(pygame.transform.flip(img, self.flip, False)), (x,y))
           
            
    @property
    def next_in_path(self):
        if self.path == [] or self.path is None:
            return None
        
        return self.path[0]



    def quadrant(self, rx, ry):
        if rx == 0 and ry > 0:
            return 6
        elif rx == 0 and ry < 0:
            return 8
        elif ry == 0 and rx > 0:
            return 5
        elif ry == 0 and rx < 0:
            return 7
        elif rx > 0 and ry > 0:
            return 1
        elif rx < 0 and ry > 0:
            return 2
        elif rx < 0 and ry < 0:
            return 3
        elif rx > 0 and ry < 0:
            return 4
        else:
            return None  # exactly at center


    def update(self, tick, movement=[0,0,0,0]):

        if tick % self.tick == 0:
            if self.invincibility > 0:
                self.invincibility -= 1
                self.stun = 0

            elif self.stun > 0:
                self.stun -= 1
                return
                    

            if self.at.type == 'Player_Tile':
                self.at.deactivate()

            S, A, W, D = movement
            DX, DY = D - A, S - W
            if DX == 0 and DY == 0:
                return
            self.idle = 0

            if self.action == 'idle':
                self.sprite = self.game.assets['player/walking']
            self.action = 'walking'
            self.sprite.update()
            if DX != 0:
                self.flip = True if DX > 0 else False
                self.move(DX,0)
            if DY != 0:
                self.move(0,DY)
            elif DX == 0:
                self.action = 'idle'
                self.sprite = self.game.assets['player/idle']
                if self.idle <= 0:
                    self.action = 'idle'
                elif self.idle > 100:
                    self.sprite.update()
                    
                self.idle = min(self.idle + 1, 101)


    def validate_cell(self, next_cell):
        if next_cell.type == 'Glass_Tile':
            if not next_cell.active:
                return False
        elif next_cell.type == 'Enemy_Tile' and self.invincibility <= 0:
            if next_cell.active:
                return False
        return True

    def move(self, DX, DY):

        x,y, = self.render_pos
        self.last = [self.movement_offset[0] + x, self.movement_offset[1] + y]
        DX *= 2

        if not in_tile(self.movement_offset, DX, DY, R=5):
            QUADRANT = self.quadrant(*self.movement_offset)
            iso_x, iso_y = 0,0
            
            if DX == -2:
                if DY == 1:
                    iso_y = 1
                elif DY == -1:
                    iso_x = -1
                elif QUADRANT in (1,2,6):
                    iso_x = 1
                elif QUADRANT in (3,4,8):
                    iso_y = -1
                else:
                    return self.axis_movement(QUADRANT, DX, DY)
            elif DX == 2:
                if DY == 1:
                    iso_x = 1
                elif DY == -1:
                    iso_y = -1
                elif QUADRANT in (1,2,6):
                    iso_y = 1
                elif QUADRANT in (3,4,8):
                    iso_x = -1
                else:
                    return self.axis_movement(QUADRANT, DX, DY)
            elif DY == 1:
                if QUADRANT in (2,3,7):
                    iso_x = 1
                elif QUADRANT in (1,4,5):
                    iso_y = 1
                else:
                    return self.axis_movement(QUADRANT, DX, DY)
            elif DY == -1:
                if QUADRANT in (2,7,3):
                    iso_y = -1
                elif QUADRANT in (1,4,5):
                    iso_x = -1
                else:
                    return self.axis_movement(QUADRANT, DX, DY)


            next_coords, render_differnce = self.game.maze.border_check(self.pos, (iso_x,iso_y))
            if self.pos != next_coords:
                if self.validate_cell(self.game.maze.maze[next_coords[1]][next_coords[0]]):
                    if self.at.type == 'Glass_Tile':
                        self.game.maze.maze[self.y][self.x].deactive()

                    self.movement_offset = wrap_to_diamond_grid(self.movement_offset[0] + DX, self.movement_offset[1] + DY)['rel_coords']
                    self.pos = next_coords

            else:
                self.bounce(QUADRANT,DX,DY)

        else:
            self.movement_offset[0] = self.movement_offset[0] + DX
            self.movement_offset[1] = self.movement_offset[1] + DY

    def axis_movement(self, QUADRANT, dx, dy):
        next_coords = None
        next_movement_offset = self.movement_offset
        if dx == -2 and QUADRANT == 7:
            if self.game.maze.trace(self.pos, (self.x + 1, self.y - 1), limit=2) != []:
                next_coords = [self.x + 1, self.y - 1]
                next_movement_offset = [9,0]
        elif dx == 2 and QUADRANT == 5:
            if self.game.maze.trace(self.pos, (self.x - 1, self.y + 1), limit=2) != []:
                next_coords = [self.x - 1, self.y + 1]
                next_movement_offset = [-9,0]
        elif dy == -1 and QUADRANT == 8:
            if self.game.maze.trace(self.pos, (self.x - 1, self.y - 1), limit=2) != []:
                next_coords = [self.x - 1, self.y - 1]
                next_movement_offset = [0,4]
        elif dy == 1 and QUADRANT == 6:
            if self.game.maze.trace(self.pos, (self.x + 1, self.y + 1), limit=2) != []:
                next_coords = [self.x + 1, self.y + 1]
                next_movement_offset = [0,-4]

        if next_coords is not None:
            if self.validate_cell(self.game.maze.maze[next_coords[1]][next_coords[0]]):
                if self.at.type == 'Glass_Tile':
                    self.game.maze.maze[self.y][self.x].deactive()

                self.movement_offset = next_movement_offset
                self.pos = next_coords
        else:
            self.bounce(QUADRANT,dx,dy)
    
   
    def bounce(self, quadrant, dx, dy):
        if dx != 0 and dy == 0:
            if quadrant in (1,2):
                self.movement_offset[1] -= 1
            elif quadrant in (3,4):
                self.movement_offset[1] += 1
            elif quadrant == 5:
                if self.game.maze.border_check(self.pos,(0, 1))[0] != self.pos:
                    self.movement_offset[1] += 1
                if self.game.maze.border_check(self.pos,(-1,0))[0] != self.pos:
                    self.movement_offset[1] -= 1

            elif quadrant == 7:
                if self.game.maze.border_check(self.pos,(1, 0))[0] != self.pos:
                    self.movement_offset[1] += 1

                elif self.game.maze.border_check(self.pos,(0, - 1))[0] != self.pos:
                    self.movement_offset[1] -= 1


        elif dx == 0 and dy != 0:
            if quadrant in (2,3):
                self.movement_offset[0] += 1
                self.flip = True
            elif quadrant in (1,4):
                self.movement_offset[0] -= 1
                self.flip = False

            elif quadrant == 6:
                if self.game.maze.border_check(self.pos,(1,0))[0] != self.pos:
                    self.movement_offset[0] -= 2
                    self.flip = False

                elif self.game.maze.border_check(self.pos,(0,1))[0] != self.pos:
                    self.movement_offset[0] += 2
                    self.flip = True


            elif quadrant == 8:
                if self.game.maze.border_check(self.pos,(-1,0))[0] != self.pos:
                    self.movement_offset[0] += 2
                    self.flip = True
                    
                elif self.game.maze.border_check(self.pos,(0,-1))[0] != self.pos:
                    self.movement_offset[0] -= 2
                    self.flip = False




class Enemy(Entity):
    
    @property
    def walkables(self):
        return('Enemy_Tile', 'Elevator', 'Tile', 'Glass_Tile', 'Plant_Tile', 'Portal_Tile', 'Temp_Tile')

    def greedy_move_toward_player(self):
        def cheb_dist(pos):
            return max(abs(self.game.player.x - pos[0]), abs(self.game.player.y - pos[1]))
    
        current_dist = cheb_dist(self.pos)
        neighbors = list(self.at.adjacent_cells)
        candidates = []
        for n in neighbors:
            if n.type in self.walkables:
                dist = cheb_dist([n.x, n.y])
                improvement = current_dist - dist
                if improvement >= 0:
                    weight = improvement + 1
                    candidates.append(([n.x, n.y, min(n.all_z, key=lambda x: abs(x - self.at.z))], weight))

        if not candidates:
            return [self.x, self.y, self.at.z]

        positions, weights = zip(*candidates)
        chosen = random.choices(positions, weights=weights, k=1)[0]
        return chosen

        
    def goToNext(self, next_coord):
        cell, next_cell = self.at, self.game.maze.maze[next_coord[1]][next_coord[0]]
        for z in next_cell.all_z:
            if z == next_coord[2]:
                break
        else:
            self.path.pop(0)
            return
        if next_cell.type == 'Glass_Tile':
            if not next_cell.active:
                self.path = []
                return
        if cell == next_cell and self.movement_offset != [0,0]:
            self.movement_offset[0] -= 2 * sign(self.movement_offset[0])
            self.movement_offset[1] -= 1 * sign(self.movement_offset[1])
        elif next_cell.z == next_coord[2]:
            old = [next_coord[0] - self.x, next_coord[1] - self.y]
            if old == [0,0]:
                new_pos, diff = self.game.maze.border_check(self.pos, [next_coord[0] - self.x, next_coord[1] - self.y])
                if list(next_coord[:2]) == new_pos and self.movement_offset == [0,0]:
                    self.path.pop(0)
                self.pos = new_pos
            else:
                diff = coord_transform(*old)
                
                if sign(diff[0]) == -1:
                    self.flip = False
                elif sign(diff[0]) == 1:
                    self.flip = True
                
                if not in_tile(self.movement_offset, *diff):
                    new_player, diff2 = self.game.maze.border_check(self.pos, old)
                    if self.pos != new_player:
                        old = self.movement_offset
                        self.movement_offset = move(self.movement_offset, *diff)
                    if self.at.type == 'Glass_Tile':
                        self.game.maze.maze[self.y][self.x].deactive()
                    self.pos = new_player

                else:
                    # old = self.movement_offset
                    self.movement_offset = move(self.movement_offset, *diff)
                
                
    def update(self, pos_dict):
        if self.path is None or self.path == []:
            self.path = [self.greedy_move_toward_player()]
            if random.randint(0,100) == 0:
                path = self.game.maze.trace(self.pos, self.game.player.pos)[:random.randint(35,50)]
                self.path = path if path is not None else self.path
        elif self.game.tick[0] % self.tick == 0:
            next_coord = self.path[0]
            if tuple(next_coord[:2]) in pos_dict:
                if pos_dict[tuple(next_coord[:2])] is not self:
                    if pos_dict[tuple(next_coord[:2])].active:
                        self.path = []
                        return
               
            old_pos = self.pos
            self.goToNext(next_coord)
            if self.pos != old_pos:
                if tuple(old_pos) in pos_dict:
                    pos_dict.pop(tuple(old_pos))
                pos_dict[tuple(self.pos)] = self
                

class Wisp(Enemy):
    def __init__(self, game, pos, sprite, hp=1, render_offset=[0, 0], e_type=None):
        super().__init__(game, pos, sprite, hp, render_offset, e_type)
        self.tick = 2
        self.animation = self.game.assets['Wisp']
        
    @property
    def img(self):
        if self.active:
            return self.animation.img()
        return self.sprite
    
    def render(self, screen, offset, rect):
        if self.active:
            x,y = self.render_pos
            if self.rect((x,y),offset).colliderect(rect):
                screen.blit(self.cutout(pygame.transform.flip(self.animation.img(), self.flip, False)), (x + self.render_offset[0] + self.movement_offset[0] + offset[0], y + self.render_offset[1] + self.movement_offset[1] + offset[1]))
        else:
            return super().render(screen, [offset[0], offset[1] - self.render_offset[1]], rect)
        
    def deactivate(self):
        self.active = False
        self.path = []
        

    def update_sound(self):
        if not self.active:
            if self.game.sound[-1] < 3:
                self.game.sound = [self.game.sounds['wisp'], 3]
        self.active = True
                
        
    def update(self, pos_dict):
         x,y = self.render_pos
         x += int(self.game.render_offset[0]) + self.movement_offset[0] + self.render_offset[0]
         y += int(self.game.render_offset[1]) + self.movement_offset[1] + self.render_offset[1]
         if x not in range(0, self.game.display.get_width()) or y not in range(0,self.game.display.get_height()):
             self.active = True
         else:
            path = self.game.maze.trace(self.pos, self.game.player.pos, 10)
            if abs(self.x + self.y - self.game.player.x - self.game.player.y) >= 10 and ((self.x, self.y) in self.game.gems or random.randint(0,100) <= 10):
                self.deactivate()
            elif len(self.path) > 0:
                if self.path[-1][:2] == self.game.player.pos:
                    self.update_sound()

            elif len(path) in range(1,6):
                self.update_sound()
                self.path = path
         if self.active:
            self.animation.update()
            super().update(pos_dict)
        

class Plant(Enemy):
    def __init__(self, game, pos, sprite, hp=1, render_offset=[0, 0], e_type=None):
        super().__init__(game, pos, sprite, hp, render_offset, e_type)
        self.tick = 4
        self.sprite = self.game.assets['Plant/walking']
     
    @property
    def action(self):
        if self.active:
            return 'walking'
        return 'idle'
    
    @property
    def img(self):
        return self.game.assets['Plant/' + self.action].img()
        
    def render(self, screen, offset, rect):
        x,y = self.render_pos
        y = y + 2 if self.action == 'idle' else y
        if self.rect((x,y),offset).colliderect(rect):
            screen.blit(self.cutout(pygame.transform.flip(self.game.assets['Plant/' + self.action].img(), self.flip, False)), (x + self.render_offset[0] + self.movement_offset[0] + offset[0], y + self.render_offset[1] + self.movement_offset[1] + offset[1]))
        
    def pot(self):
        self.active = False
        self.movement_offset = [0,0]
        sprite = self.game.assets['Plant/idle']
        if sprite != self.sprite:
            self.sprite = sprite
        else:
            self.sprite.update()

    def update(self, pos_dict):
        sprite = self.sprite
        if abs(self.x - self.game.player.x) < self.game.maze.w / 2 and abs(self.y - self.game.player.y) < self.game.maze.h / 3 and self.at.type == 'Plant_Tile':
            if (self.x, self.y) in pos_dict:
                if pos_dict[(self.x, self.y)] is self:
                    self.pot()
                    return
            else:
                self.pot()
                return
            
        self.active = True
        sprite = self.game.assets['Plant/walking']
        if sprite != self.sprite:
            self.sprite = sprite
        else:
            self.sprite.update()
        super().update(pos_dict)
            
        

class Converter(Enemy):
    def __init__(self, game, pos, sprite, hp=1, render_offset=[0, 0], e_type=None):
        super().__init__(game, pos, sprite, hp, render_offset, e_type)
        self.variant = 0
    

    @property
    def img(self):
        return self.sprite[0]

    def render(self, screen, offset, rect):
        x,y = self.render_pos
        if not self.rect((x,y),offset).colliderect(rect):
            return
        if self.path != []:
            _sign = sign(self.path[0][0] - self.x) if sign(self.path[0][0] - self.x) != 0 else sign(self.path[0][1] - self.y) 
            if _sign < 0 :
                self.variant = 1
            elif _sign > 0:
                self.variant = 0

        screen.blit(self.cutout(pygame.transform.flip(self.sprite[self.variant], self.flip, False)), (x + self.render_offset[0] + self.movement_offset[0] + offset[0], y + self.render_offset[1] + self.movement_offset[1] + offset[1]))
        

    def update(self, pos_dict):
        if self.at.type == 'Tile' and self.movement_offset == [0,0]:
            if self.at.player_tile:
                ox, oy = self.game.maze.offset
                for tile in self.at.adjacent_cells | {self.at}:
                    if tile.type == 'Tile':
                        if tile.player_tile:
                            self.game.maze.maze[tile.y][tile.x] = Enemy_Tile(self.game.maze, tile.z, tile.x, tile.y, cooldown=random.randint(1,10) * 10)
                            x_, y_ = self.game.maze.maze[tile.y][tile.x].render_pos
                            self.game.maze.static_surface.blit(self.game.maze.maze[tile.y][tile.x].cutout,(x_ - ox, y_ - oy))

                self.hp = 0
                return
        super().update(pos_dict)


class Constructor(Enemy):
    def __init__(self, game, pos, sprite, hp=1, render_offset=[0, 0], e_type=None):
        super().__init__(game, pos, sprite, hp, render_offset, e_type)
        self.tick = 5
        self.cooldown = [0,max(900 - self.game.level * 10, 30)]
        
    def random_step(self, dx, dy):
        options = []
        if dx > 0:
            options.append((1, 0))
        elif dx < 0:
            options.append((-1, 0)) 
        if dy > 0:
            options.append((0, 1))
        elif dy < 0:
            options.append((0, -1)) 
        if not options:
            return (0, 0)  

        return random.choice(options)
        
    def update(self, pos_dict):
        def neighbor_check(tile):
            a = tile.get_accessible_neighbor(1,0)
            if a is not None:
                if a.z1 > tile.z1:
                    return False
            a = tile.get_accessible_neighbor(0,1)
            if a is not None:
                if a.z1 > tile.z1:
                    return False   
            b = tile.get_accessible_neighbor(-1,0)
            if b is not None:
                if b.all_z[-1] < tile.z1:
                    return False   
            b = tile.get_accessible_neighbor(0,-1)
            if b is not None:
                if b.all_z[-1] < tile.z1:
                    return False  
            c = self.game.maze.maze[tile.y + 1][tile.x + 1]
            if c is not None:
                if c.z1 > tile.all_z[-1]:
                    return False
            c = self.game.maze.maze[tile.y - 1][tile.x - 1]
            if c is not None:
                if c.all_z[-1] < tile.z1:
                    return False
            return True

        self.cooldown[0] = min(self.cooldown[0] + 1, self.cooldown[1])
        if self.gems >= 2 or self.cooldown[0] == self.cooldown[1]:
            nx,ny = self.random_step(self.game.player.x - self.x, self.game.player.y - self.y)
            px,py = nx + self.x, ny + self.y
            
            if self.at.get_accessible_neighbor(nx,ny) is None:
                if not cell_valid((px,py), self.game.maze):
                    self.game.maze.maze[py][px] = structures_factory(self.game.maze, 'Temp_Tile', self.at.z1, px,py)
                    cell = self.game.maze.maze[py][px]
                    x_,y_ = cell.render_pos
                    ox, oy = self.game.maze.offset
                    if neighbor_check(self.game.maze.maze[py][px]):
                        if self.cooldown[0] == self.cooldown[1]:
                            self.cooldown[0] = 0
                        else:
                            self.gems = max(self.gems - 2, 0)   
                        self.game.maze.static_surface.blit(cell.cutout,(x_ - ox, y_ - oy))
                    else:
                        self.game.maze.maze[py][px] = None
        super().update(pos_dict)
        self.flip = False
        


class Trapper(Enemy):
    def __init__(self, game, pos, sprite, hp=1, render_offset=[0, 0], e_type=None):
        super().__init__(game, pos, sprite, hp, render_offset, e_type)
        self.capcacity = max(10, self.game.level // 1.5)
        self.cooldown = [0,45]

    def lay_trap(self):
        if len(self.game.traps) < self.capcacity and abs(self.x - self.game.player.x) < 10 and abs(self.y - self.game.player.y) < 10:
            if (self.x, self.y) not in self.game.traps and self.at.type in ('Tile', 'Temp_Tile', 'Elevator'):
                self.game.traps[(self.x,self.y)] = Trap(self.game, self.pos, self.game.assets['Trap'])

    def update(self, pos_dict):
        if self.cooldown[0] == 0:
            self.lay_trap()
        self.cooldown[0] = (self.cooldown[0] + 1) % self.cooldown[1]
        super().update(pos_dict)
