from utils import sign, to_iso
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
        self.tick = [0,300]    

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
        screen.blit(pygame.transform.flip(self.sprite, self.flip, False), (x + offset[0] + self.render_offset[0] + self.movement_offset[0], y + offset[1] + self.render_offset[1] + self.movement_offset[1]))

    def update(self):
        pass
        

class Gem(Entity):
    def update(self):
        if self.pos == self.game.player.pos:
            self.hp = 0


class Player(Entity):
    @property
    def next_in_path(self):
        if self.path == [] or self.path is None:
            return None
        
        return self.path[0]
    

    def update(self, tick, movement=[0,0,0,0]):
        
        if tick % 2 == 0:
            diff = [movement[1] - movement[3], movement[0] - movement[2]]
            
            if diff[0] != 0 and diff[1] != 0:
                old = random.choice([ [ 0, diff[1] ], [ diff[0], 0 ] ])
            else:
                old = diff
            if old != [0,0]:
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
                        self.game.render_offset[0] -= diff[0]
                        self.game.render_offset[1] -= diff[1] + diff2[1] - 5 * sign(diff2[1])
                    
                    self.pos = new_player

                else:
                    old = self.movement_offset
                    self.movement_offset = move(self.movement_offset, *diff)
                    self.game.render_offset[0] -= self.movement_offset[0] - old[0]
                    self.game.render_offset[1] -= self.movement_offset[1] - old[1]
            


class Enemy(Entity):
    
    def greedy_move_toward_player(self):
        def cheb_dist(pos):
            return max(abs(self.game.player.x - pos[0]), abs(self.game.player.y - pos[1]))
    
        current_dist = cheb_dist(self.pos)
        neighbors = list(self.at.adjacent_cells)
        candidates = []
        for n in neighbors:
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
                    
                    self.pos = new_player

                else:
                    old = self.movement_offset
                    self.movement_offset = move(self.movement_offset, *diff)
                
                
    def update(self, entity_dict):
        if self.path is None or self.path == []:
            self.path = [self.greedy_move_toward_player()]
        elif self.game.tick[0] % 5 == 0:
            next_coord = self.path[0]
            if (next_coord[0], next_coord[1]) in entity_dict:
                for e in entity_dict[(next_coord[0], next_coord[1])]:
                    if e.type == 'Enemy':
                        break
                else:    
                    self.goToNext(next_coord)
            else:
                self.goToNext(next_coord)
