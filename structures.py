import random
from utils import *

def in_range(coord, maze):
    return 0 <= coord[0] < len(maze[0]) and 0 <= coord[1] < len(maze)

class Tile:
    def __init__(self, game, z, sprite):
        self.game = game
        self.pos = z
        
        # self.sprite = game.assets[sprite]
       
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

class Elevator(Tile):
    def __init__(self, game, z, sprite, other_z):
        super().__init__(game, int(z), sprite)
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

    def update(self):
        if self.time_stopped <= 0:
            self.current_z += self.direction * 0.1
            self.current_z = round(self.current_z,2)
        
        
            if (self.direction > 0 and self.current_z >= self.pos) or (self.direction < 0 and self.current_z <= self.z2):
                self.direction *= -1
                self.time_stopped = 60
        else:
            self.time_stopped -= 1 
            

