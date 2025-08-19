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
            'tile_top': load_image('top.png'),
            'entity': load_image('monster.png'),
            'ramp_right': load_image('ramp.png'),
            'ramp_left': pygame.transform.flip(load_image('ramp.png'), True, False),
            'wall': load_image('wall.png'),
            'player': load_image('player.png'),
            # 'player': load_image('Bird_2.png'),
            'gem': load_image('gem1.png')
        }
        
        self.level = 0
        # self.maze = Maze(self, 21,21, 'tile', 'elevator', color_table=None, stair_prob=0, sparsity=(100,100), )
        self.maze = Maze(self, 21,21, 'tile', 'elevator', 'tile_top', color_table={(255,0,0):(255,110,89), (0,0,255):(18,83,89)}, stair_prob=0, sparsity=(100,100), )
        self.entities = []
        self.gems = set()
        self.tile_outline = self.maze.get_tile_outline()
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
        self.display.fill((255,255,255))
        # self.display.fill((40,20,40))
        self.maze.draw_map(self.display, offset=offset, entities=entities, paused=self.paused)
        if player is not None:
            tile = self.player.at
            if tile.type == 'Elevator':
                if tile.time_stopped <= 0:
                    dz = tile.direction * 0.5
                    
        for px, py in self.tile_outline:
            self.display.set_at((px + offset[0], py + offset[1]), (25,20,26))
        for y in range(self.maze.h):
            for x in range(self.maze.w):
                if (x,y) in entities:
                    for e in entities[(x,y)]:
                            e.render(self.display, offset)
        pygame.transform.scale(self.display, self.screen.get_size(), self.screen)
        pygame.display.flip()
        if self.paused:
            return 0
        return dz
    

    
    def test(self):
        ''' Returns render offset for player to be center of the screen '''
        p_x, p_y = self.maze.maze[self.player.y][self.player.x].render_pos

        center_x = self.display.get_width() // 2   
        center_y = self.display.get_height() // 2  
        return [center_x - p_x, center_y - p_y]


    def reset(self):
        self.paused = False
        self.level = min(6, self.level + 1)
        self.player.path = []
        self.gems = set()
        self.entities = []
        color_table={(255,0,0):(255,110,89), (0,0,255):(18,83,89)}
        # color_table = None
        print("LEVEL", self.level)
        while 1:
            try:
                WIDTH, HEIGHT = random.randint(3,10) * 2 + 1, random.randint(3,10) * 2 + 1 
                i = random.randint(0,5)
                sprite = 'tile'
                if self.level % 2 == 0:
                    
                    self.maze = Maze(self, WIDTH, HEIGHT, sprite, 'elevator', 'tile_top', color_table, random.choice([0,1,2,3,None]),
                                 random.randint(0,100), random.randint(-5,10), [random.randint(0,100), random.randint(0,100)],
                                 random.randint(-20,100))
                else:
                    self.maze = Maze(self, WIDTH, HEIGHT, sprite, 'elevator', 'tile_top', color_table, random.choice([0,3,3,3,None]),
                                 random.randint(0,100), random.randint(-5,10), [0,0],
                                 random.randint(-20,100))
                self.player.pos = [self.maze.w - 2, self.maze.h - 2]
                self.render_offset = self.test()
                pos_dict = set()
                self.entities = [Enemy(self, (x,y), self.assets['entity'], render_offset=[0,-8], e_type='Enemy') for x,y in self.maze.get_spawnpoints(1,1,random.randint(1,min(10, self.level)))]
                self.tile_outline = self.maze.get_tile_outline()
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
                pos_dict = {tuple(v.pos):v for v in self.entities}
                for gem in self.gems.copy():
                    if tuple(self.player.pos) == gem:
                        self.gems.remove(gem)
                    else:
                        entity_dict.setdefault(gem, []).append(Gem(self, gem, self.assets['gem'], e_type='Gem'))
                    
                for entity in self.entities.copy():
                    if entity.hp > 0:
                        entity.update(pos_dict)
                        
                        if (entity.x, entity.y) in self.gems:
                            self.gems.remove((entity.x, entity.y))
                        
                        if entity.pos == self.player.pos:
                            print("PLAYER GET")
                            self.paused = True
                        entity_dict.setdefault((entity.x, entity.y), []).append(entity)
                    else:
                        self.entities.remove(entity)

            

            # self.render_offset[1] += self.render(self.maze, self.player, self.render_offset, entities=entity_dict)
            self.render_offset[1] += self.render(self.maze, self.player, [self.render_offset[0], int(self.render_offset[1])], entities=entity_dict)
            
                
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
        
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_m:
                        print('==============================')
                        for k,v in self.maze.settings.items():
                            print(k, v)
                        print('==============================')
                        
                    if event.key == pygame.K_k:
                        self.entities = []
                    if event.key == pygame.K_i:
                        self.gems = set()
                    if event.key == pygame.K_MINUS:
                        x,y = self.display.get_size()
                        self.display = pygame.Surface((min(800, x + 4), min(y + 3, 600)), pygame.SRCALPHA)
                        print(self.display.get_size())
                        
                    if event.key == pygame.K_EQUALS:
                        x,y = self.display.get_size()
                        self.display = pygame.Surface((max(4, x - 4), max(y - 3, 3)), pygame.SRCALPHA)
                        print(self.display.get_size())
                    if event.key == pygame.K_o:
                        locs = self.maze.generate_gems()
                        for l in locs:
                            self.gems.add(l)
                        print("Number of gems :", len(self.gems))
                    if event.key == pygame.K_e:
                        self.maze.add_elevators(60)
                        self.tile_outline = self.maze.get_tile_outline()
                    if event.key == pygame.K_l:
                        print(self.player.pos, self.player.type)
                        for e in self.entities:
                            print(e.pos, e.type, e.movement_offset)
                    if event.key == pygame.K_p:
                        self.maze.print_maze(spacing="\n=============0====================\n")
                    if event.key == pygame.K_c:
                        self.reset()
                       
                    if event.key == pygame.K_r:
                        self.paused = not self.paused
                    if event.key == pygame.K_t:
                        self.player.path = self.maze.trace(self.player.pos, (self.maze.w-2, self.maze.h-2))
                        print(self.player.path)
                    if event.key == pygame.K_SPACE:
                        print(self.player.render_pos)
                        self.maze.maze = self.maze.fix_maze(self.maze.maze)
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
