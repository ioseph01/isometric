from scripts.utils import cell_type, cell_valid, get_cell_type, in_range, sign, to_iso
from scripts.structures import Enemy_Tile, Player_Tile, Tile
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
        self.flip = True
        self.tick = 5
        self.active = True
        

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
    
    def render(self, screen, offset):
        x,y = self.render_pos
        screen.blit(pygame.transform.flip(self.sprite, self.flip, False), (x + offset[0] + self.render_offset[0] + self.movement_offset[0], int(y) + offset[1] + self.render_offset[1] + self.movement_offset[1]))


    def update(self):
        pass
        

class Gem(Entity):
    def update(self):
        if self.pos == self.game.player.pos:
            self.hp = 0


class Player(Entity):
    
    def __init__(self, game, pos, sprite, hp=1, render_offset=[0, 0], e_type=None):
        super().__init__(game, pos, sprite, hp, render_offset, e_type)
        self.idle = 0
        self.stun = 0
        self.action = 'idle'
        
    def render(self, screen, offset):
        x,y = self.render_pos
        x = int(x + offset[0] + self.render_offset[0] + self.movement_offset[0])
        y = int(y + offset[1] + self.render_offset[1] + self.movement_offset[1])
        if self.action == 'walking':
            screen.blit(pygame.transform.flip(self.sprite.img(), self.flip, False), (x,y))
        elif self.idle > 100:
            screen.blit(pygame.transform.flip(self.sprite.img(), self.flip, False), (x,y))
        else:
            screen.blit(pygame.transform.flip(self.sprite.images[0], self.flip, False), (x,y))

    @property
    def next_in_path(self):
        if self.path == [] or self.path is None:
            return None
        
        return self.path[0]


    def update(self, tick, movement=[0,0,0,0]):
        
        if tick % 2 == 0:
            
            if self.stun > 0:
                self.stun -= 1
                return
                    

            if self.at.type == 'Player_Tile':
                self.at.deactivate()
            diff = [movement[1] - movement[3], movement[0] - movement[2]]
            
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
                    next_cell = self.game.maze.maze[new_player[1]][new_player[0]]
                    if next_cell.type == 'Glass_Tile':
                        if not next_cell.active:
                            return
                    elif next_cell.type == 'Enemy_Tile':
                        if next_cell.active:
                            return

                    if self.pos != new_player:
                        old = self.movement_offset
                        self.movement_offset = move(self.movement_offset, *diff)
                        self.game.render_offset[0] -= diff[0]
                        self.game.render_offset[1] -= diff[1] + diff2[1] - 5 * sign(diff2[1])
                        if self.at.type == 'Glass_Tile':
                            self.game.maze.maze[self.y][self.x].deactive()
                    
                    self.pos = new_player

                else:
                    old = self.movement_offset
                    self.movement_offset = move(self.movement_offset, *diff)
                    self.game.render_offset[0] -= self.movement_offset[0] - old[0]
                    self.game.render_offset[1] -= self.movement_offset[1] - old[1]
                    

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
        return('Enemy_Tile', 'Elevator', 'Tile', 'Glass_Tile', 'Plant_Tile')

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
                print("tracking player")
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
    
    def render(self, screen, offset):
        if self.active:
            x,y = self.render_pos
            screen.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (x + self.render_offset[0] + self.movement_offset[0] + offset[0], y + self.render_offset[1] + self.movement_offset[1] + offset[1]))
        else:
            return super().render(screen, [offset[0], offset[1] - self.render_offset[1]])
        
    def deactivate(self):
        self.active = False
        self.path = []
        
    def update(self, pos_dict):
        path = self.game.maze.trace(self.pos, self.game.player.pos, 10)
        if abs(self.x + self.y - self.game.player.x - self.game.player.y) >= 10 and ((self.x, self.y) in self.game.gems or random.randint(0,100) <= 10):
            self.deactivate()
        elif len(self.path) > 0:
            if self.path[-1][:2] == self.game.player.pos:
                self.active = True
        elif len(path) in range(1,6):
            self.active = True
            self.path = path
        if self.active:
            self.animation.update()
            super().update(pos_dict)
        

class Plant(Enemy):
    def __init__(self, game, pos, sprite, hp=1, render_offset=[0, 0], e_type=None):
        super().__init__(game, pos, sprite, hp, render_offset, e_type)
        self.tick = 6
        self.sprite = self.game.assets['Plant/walking']
     
    @property
    def action(self):
        if self.active:
            return 'walking'
        return 'idle'
        
    def render(self, screen, offset):
        x,y = self.render_pos
        y = y + 2 if self.action == 'idle' else y
        screen.blit(pygame.transform.flip(self.game.assets['Plant/' + self.action].img(), self.flip, False), (x + self.render_offset[0] + self.movement_offset[0] + offset[0], y + self.render_offset[1] + self.movement_offset[1] + offset[1]))
        
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
    
    def render(self, screen, offset):
        x,y = self.render_pos
        if self.path != []:
            _sign = sign(self.path[0][0] - self.x) if sign(self.path[0][0] - self.x) != 0 else sign(self.path[0][1] - self.y) 
            if _sign < 0 :
                self.variant = 1
            elif _sign > 0:
                self.variant = 0

        screen.blit(pygame.transform.flip(self.sprite[self.variant], self.flip, False), (x + self.render_offset[0] + self.movement_offset[0] + offset[0], y + self.render_offset[1] + self.movement_offset[1] + offset[1]))
        

    def update(self, pos_dict):
        if self.at.type == 'Tile' and self.movement_offset == [0,0]:
            if self.at.player_tile:
                for tile in self.at.adjacent_cells | {self.at}:
                    if tile.type == 'Tile':
                        if tile.player_tile:
                            self.game.maze.maze[tile.y][tile.x] = Enemy_Tile(self.game.maze, tile.z, tile.x, tile.y, cooldown=None)
                self.hp = 0
                return
        super().update(pos_dict)
