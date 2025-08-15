import pygame
import random
from entities import Enemy, Entity, Gem, Player
from maze import Maze
from structures import Elevator, Tile
from utils import *

NEIGHBORS = {(-1,0),(0,-1),(1,0),(0,1)}


class Game:
    def __init__(self):
        pygame.init()
        
        self.sprite = "tile"
        self.screen = pygame.display.set_mode((800, 600))
        self.display = pygame.Surface((320,240), pygame.SRCALPHA)
        self.display = pygame.Surface((200,150), pygame.SRCALPHA)
        self.clock = pygame.time.Clock()
        pygame.display.set_caption("Isometric")
        
        self.render_offset = [0,0]
        self.movement = [False, False, False, False]

        self.assets = {
            'elevator': load_images('elevators'),
            'tile': load_images('tiles'),
            'entity': load_image('monster.png'),
            'ramp_right': load_image('ramp.png'),
            'ramp_left': pygame.transform.flip(load_image('ramp.png'), True, False),
            'wall': load_image('wall.png'),
            'player': load_image('player.png'),
            'gem': load_image('gem1.png')
        }
        
        self.level = 0
        self.maze = Maze(self, 21,21, 'tile', 'elevator', color_table=None, stair_prob=0, sparsity=(100,100), )
        self.entities = []
        self.gems = set()
        self.paused = False
        self.start_level()
        
    def start_level(self):
        self.player = Player(self, [1,1], self.assets['player'], render_offset=[0,-12], e_type='Player')
        self.entities = [Entity(self, [self.maze.w - 2, self.maze.h - 2], self.assets['entity'])]
        self.entities = []
        self.tick = [0, 60]
        self.paused = False
        


    def render(self, maze, player=None, offset=(0,0), entities={}):
        K = (player.x, player.y)
        entities.setdefault(K, []).append(player)

        dz = 0
        self.display.fill((220,200,240))
        self.maze.draw_map(self.display, offset=offset, entities=entities, paused=self.paused)
        if player is not None:
            tile = self.player.at
            if tile.type == 'Elevator':
                if tile.time_stopped <= 0:
                    dz = .5 * tile.direction
        pygame.transform.scale(self.display, self.screen.get_size(), self.screen)
        pygame.display.flip()
    
        return dz
    

    
    def test(self):
        ''' Returns render offset for player to be center of the screen '''
        player_x, player_y = 1, 1
        player_z = self.maze.maze[1][1].z  # or however you access the z value

        player_screen_x, player_screen_y = to_iso(player_x, player_y, self.maze.TILE_WIDTH, self.maze.TILE_HEIGHT)
        player_screen_y -= player_z * (self.maze.TILE_HEIGHT // 4)  

        center_x = self.display.get_width() // 2   
        center_y = self.display.get_height() // 2  
        
        return [center_x - player_screen_x, center_y - player_screen_y]


    def reset(self):
        self.paused = False
        self.level += 1
        self.player.pos = [1,1]
        self.player.path = []
        self.gems = set()
        print("LEVEL", self.level)
        while 1:
            try:
                WIDTH, HEIGHT = random.randint(3,10) * 2 + 1, random.randint(3,10) * 2 + 1 
                i = random.randint(0,5)
                sprite = 'tile'
                if self.level % 2 == 0:
                    self.maze = Maze(self, WIDTH, HEIGHT, sprite, 'elevator', None, random.choice([0,1,2,3,None]),
                                 random.randint(0,100), random.randint(-5,10), [random.randint(0,100), random.randint(0,100)],
                                 random.randint(-20,100))
                else:
                    self.maze = Maze(self, WIDTH, HEIGHT, sprite, 'elevator', None, random.choice([0,1,2,3,None]),
                                 random.randint(0,100), random.randint(-5,10), [0,0],
                                 random.randint(-20,100))
                self.render_offset = self.test()
                self.entities = [Enemy(self, [self.maze.w - 2, self.maze.h - 2], self.assets['entity'], render_offset=[0,-8], e_type='Enemy') for i in range(min(10, self.level))]
                return
            except RuntimeError:
                pass

    def run(self):
        running = True
        while running:
            if not self.paused:
                self.tick[0] = (self.tick[0] + 1) % self.tick[1]
            
                self.player.update(self.tick[0], movement=self.movement)
    
                entity_dict = {}
                for gem in self.gems.copy():
                    if tuple(self.player.pos) == gem:
                        self.gems.remove(gem)
                    else:
                        entity_dict.setdefault(gem, []).append(Gem(self, gem, self.assets['gem']))
                    
                for entity in self.entities.copy():
                    if entity.hp > 0:
                        entity.update(entity_dict)
                        if (entity.x, entity.y) in self.gems:
                            self.gems.remove((entity.x, entity.y))
                        
                        if entity.pos == self.player.pos:
                            print("PLAYER GET")
                            self.paused = True
                        entity_dict.setdefault((entity.x, entity.y), []).append(entity)
                    else:
                        self.entities.remove(entity)

            

            self.render_offset[1] += self.render(self.maze, self.player, self.render_offset, entities=entity_dict)
                
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
        
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_k:
                        self.entities = []
                    if event.key == pygame.K_i:
                        self.gems = set()
                    if event.key == pygame.K_o:
                        locs = self.maze.generate_gems()
                        for l in locs:
                            self.gems.add(l)
                        print("Number of gems :", len(self.gems))
                    if event.key == pygame.K_e:
                        self.maze.add_elevators(60)
                    if event.key == pygame.K_l:
                        print(self.player.pos)
                    if event.key == pygame.K_p:
                        self.maze.print_maze(spacing="\n=============0====================\n")
                    if event.key == pygame.K_c:
                        self.reset()
                       
                    if event.key == pygame.K_r:
                        self.paused = not self.paused
                    if event.key == pygame.K_t:
                        for entity in self.entities:
                            entity.path = self.maze.trace(entity.pos, self.player.pos)
                    if event.key == pygame.K_SPACE:
                        pass
                    if event.key == pygame.K_UP:
                        self.render_offset[1] += 10
                
                    elif event.key == pygame.K_DOWN:
                        self.render_offset[1] -= 10
                
                    elif event.key == pygame.K_RIGHT:
                        self.render_offset[0] -= 10
                
                    elif event.key == pygame.K_LEFT:
                        self.render_offset[0] += 10
                    if not self.paused:
                        
                        if event.key == pygame.K_w:
                            self.movement[2] = True
                        elif event.key == pygame.K_d:
                            self.movement[3] = True
                        elif event.key == pygame.K_s:
                            self.movement[0] = True
                        elif event.key == pygame.K_a:
                            self.movement[1] = True
                        
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_w:
                        self.movement[2] = False
                    if event.key == pygame.K_d:
                        self.movement[3] = False
                    if event.key == pygame.K_s:
                        self.movement[0] = False
                    if event.key == pygame.K_a:
                        self.movement[1] = False
            
            
                    if event.key in [pygame.K_q,pygame.K_ESCAPE]:
                        running = False
    

            self.clock.tick(60)

        pygame.quit()
        


Game().run()
