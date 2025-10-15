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

def in_tile(pos, dx, dy):
    return abs(pos[0] + dx) / 2 + abs(pos[1] + dy) <= 4

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
            self.game.sounds['create_egg'].play()

            
    def destroy_egg(self):
        if self.egg is not None:
            self.pos = self.egg
            self.game.render_offset = self.game.test()
            self.game.sounds['destroy_egg'].play()
            
        self.egg = None
        
    @property
    def img(self):
        if self.action == 'walking' or self.idle > 100:
            return self.sprite.img()
        return self.sprite.images[0]

    def render(self, screen, offset, rect):
        x,y = self.render_pos
        if not self.rect((x,y),offset).colliderect(rect):
            return
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

    def process_movement(self, movement):
        # print(movement[1] - movement[3], movement[0] - movement[2])
        # new_movement = [movement[1] - movement[3], movement[0] - movement[2]]
        # if new_movement[0] != 0 and new_movement[1] != 0:
        #     return 'Diagonal'
        # if new_movement[0] != 0 or new_movement[1] != 0:
        #     return 'Straight'
        return 'None'


    def get_fallback_by_quadrant(self, q, dx, dy):
        pairs = {
            1: [(1, 0), (0, -1)],
            2: [(-1, 0), (0, -1)],
            3: [(-1, 0), (0, 1)],
            4: [(1, 0), (0, 1)],
        }
        if q not in pairs:
            return None

        a, b = pairs[q]

        if (dx, dy) == a:
            fx, fy = b
        elif (dx, dy) == b:
            fx, fy = a
        else:
            return None  # Not a simple cardinal move

        # Flip both signs for fallback
        return (-fx, -fy)



    def move_player(self, dx, dy):
        """
        Move player on a 2D array of isometric tiles with offsets.
        dx, dy: NESW movement deltas (exactly one nonzero)
        """
        # print(self.movement_offset)  # debug

        ox, oy = self.movement_offset
        tx, ty = self.at.x, self.at.y
        print(dx,dy)
        # Apply move with proper X scaling
        dx_ = dx
        dy_ = dy
        _ox = ox - dx
        _oy = oy + dy
        dx *= -2
        dy *= 1

        new_ox = ox + dx
        new_oy = oy + dy

        if in_tile([ox, oy], dx,dy):
            self.movement_offset = [new_ox, new_oy]
            # print(self.movement_offset, self.pos)
            return -1

        new_tx, new_ty = tx, ty
        quadrant = -1
        # What does -8,0 go to? It maps to Q2 and Q3 in this, we need to add edge cases for axis unforatnutely..sadasdadasjld;a
        if 0 <= _ox and _oy <= 0:        # Q1
            quadrant = 1
            if sign(dx) == 1 or sign(dy) == -1:
                new_tx -= 1
        elif _ox <= 0 and _oy <= 0:     # Q2
            quadrant = 2
            if sign(dx) == -1 or sign(dy) == -1:
                new_ty -= 1
        elif _ox < 0 and 0 < _oy:       # Q3
            quadrant = 3
            if sign(dx) == -1 or sign(dy) == 1:
                new_tx += 1
        elif 0 <= _ox and 0 <= _oy:       # Q4
            quadrant = 4
            if sign(dx) == 1 or sign(dy) == 1:
                new_ty += 1
        else:
            print("IDK")
            # Axis-aligned (ox==0 or oy==0)
            if dx != 0:
                new_tx = -1
                new_ty = 1
            elif dy != 0:
                new_ty += -1 if oy >= 0 else 1

        # print("Quadrant", quadrant, self.movement_offset, self.pos)
        new_offset = move([ox,oy],dx,dy)
        
        # Check if next tile is valid
        if tx != new_tx or ty != new_ty:
            if cell_valid([new_tx, new_ty], self.game.maze):
                next_cell = self.game.maze.maze[new_ty][new_tx]
                # Optional: check height difference or blocking tiles
                if -3 < next_cell.z - self.at.z < 2:
                    self.pos = [next_cell.x, next_cell.y]
                    self.movement_offset = new_offset
                    return -1
        return quadrant



    def update(self, tick, movement=[0,0,0,0]):
        if movement != [False, False, False, False]:
            self.process_movement(movement)
        if tick % self.tick == 0:
            if self.invincibility > 0:
                self.invincibility -= 1
                self.stun = 0

            elif self.stun > 0:
                self.stun -= 1
                return
                    

            if self.at.type == 'Player_Tile':
                self.at.deactivate()
            diff = [movement[1] - movement[3], movement[0] - movement[2]]
            # if self.test:
            #     if diff != [0,0]:
            #         if (q := self.move_player(*diff)) > 0:
            #             m = self.get_fallback_by_quadrant(q, *diff)
            #             if m is not None:
            #                 print("New movement", m)
            #                 self.move_player(*m)
            #     return
            if diff[0] != 0 and diff[1] != 0:
                old = random.choice([ [ 0, diff[1] ], [ diff[0], 0 ] ])
            else:
                old = diff
            if old != [0,0]:
                self.idle = 0
                if self.action == 'idle':
                    self.sprite = self.game.assets['player/walking']
                self.action = 'walking'
                self.sprite.update()
                
                
                diff = coord_transform(*old)
                
                if sign(diff[0]) == -1:
                    self.flip = False
                elif sign(diff[0]) == 1:
                    self.flip = True
                
                if not in_tile(self.movement_offset, *diff):
                    new_player, diff2 = self.game.maze.border_check(self.pos, old)
                    if abs(diff2[1]) == 10:
                        self.z -= sign(diff2[1])
                    next_cell = self.game.maze.maze[new_player[1]][new_player[0]]
                    if next_cell.type == 'Glass_Tile':
                        if not next_cell.active:
                            return
                    elif next_cell.type == 'Enemy_Tile' and self.invincibility <= 0:
                        if next_cell.active:
                            return

                    if self.pos != new_player:
                        old = self.movement_offset
                        self.movement_offset = move(self.movement_offset, *diff)
                        if self.at.type == 'Glass_Tile':
                            self.game.maze.maze[self.y][self.x].deactive()
                    
                    self.pos = new_player

                else:
                    old = self.movement_offset
                    self.movement_offset = move(self.movement_offset, *diff)
                    

            else:
                self.action = 'idle'
                self.sprite = self.game.assets['player/idle']
                if self.idle <= 0:
                    self.action = 'idle'
                elif self.idle > 100:
                    self.sprite.update()
                    
                self.idle = min(self.idle + 1, 101)


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
                            self.game.maze.maze[tile.y][tile.x] = Enemy_Tile(self.game.maze, tile.z, tile.x, tile.y, cooldown=None)
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