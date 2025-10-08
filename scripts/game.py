import pygame
import random
from scripts.animation import Animation
from scripts.entities import Constructor, Converter, Enemy, Entity, Gem, Plant, Player, Trapper, Wisp, Gemstone
from scripts.maze import Maze
from scripts.structures import Plant_Tile, Portal_Tile
from scripts.utils import *

NEIGHBORS = {(-1,0),(0,-1),(1,0),(0,1)}
FILL = (242,242,255)
BLACK = (25,20,26)
colors = list({(255, 201, 0), (255, 203, 205), (251, 255, 235), (231, 220, 185), (245, 0, 112), (255, 97, 91), (150, 255, 194), (178, 255, 0), (0, 125, 141), (255, 155, 217), (154, 160, 245), (178, 19, 185), (49, 110, 255), (12, 0, 107), (174, 181, 0)})


class Game:
    def __init__(self, controller):
        self.controller = controller
        self.sprite = "tile"
        self.display = pygame.Surface((240,180), pygame.SRCALPHA)
        self.scaled_display = pygame.Surface((720, 540), pygame.SRCALPHA)

        self.render_offset = [0,0]
        self.movement = [False, False, False, False]
        self.load_assets()
        self.load_sounds()
        self.settings = {
            'sparsity': [max(0,random.randint(-5,5)), max(0,random.randint(-5,5))],
            'room_attempts': 1,
            'elevator_prob': random.randint(0,100),
            'stair_prob': 0,
            'glass_prob': 0,
            'player_prob': 0,
            'enemy_prob': 0,
            'wall_height':1
            }
        
        self.color_table={(255,0,0):(255,110,89), (0,0,255):(18,83,89)}
        self.level = 0
        self.maze = Maze(self, 21,21, self.assets['gem'], color_table={(255,0,0):(255,110,89), (0,0,255):(18,83,89)}, stair_prob=0, sparsity=(100,100), )
        self.entities = []
        self.gems = set()
        self.traps = {}
        self.gemstones = set()
        self.paused = False
        self.score = 0
        self.stage = True
        self.lives = 5
        self.gem_count = 0
        self.skip = False
        self.start_level()

    @property 
    def at(self):
        return self.player.at
    
    def load_sounds(self):
        self.sounds = {
            'gem': load_sounds("gem"),
            'powerup': load_sound("powerup.wav"),
            'player_tile': load_sound('player_tile.wav'),
            'death': load_sound('death.wav'),
            'wisp': load_sound('wisp.wav')
            }
        
    def load_assets(self):
        
        self.assets = {
            'entity': load_image('monster.png'),
            'player/walking': Animation(load_images('player/flying'), img_dur=5),
            'player/idle': Animation(load_images('player/idle'), img_dur=45),
            'egg': load_image('egg.png'),
            'gem': load_image('gem1.png'),
            'Wisp': Animation(load_images('wisp')),
            'Converter': load_images('Converter'),
            'Constructor': load_image('constructor.png'),
            'Plant/idle': Animation(load_images('Plant/idle')),
            'Plant/walking': Animation(load_images('Plant/walking'), img_dur=120),
            'gemstone': load_image('gemstone.png'),
            'Trap':load_image('trap.png'),
            'Trapper':load_image('trapper/0.png'),
            
        }

        
    def start_level(self):
        self.player = Player(self, [1,1], self.assets['player/idle'], render_offset=[0,-12], e_type='Player')
        self.entities = []
        self.tick = [0, 60]
        self.paused = False
        self.reset()
        

    def add_enemies(self, count):
        
        self.entities = []
        
        base_weights = [0.4, 0.1, 0.2, 0.2, 0.2, 0.2]
        chaos = int(self.level / 5)

        weights = [
            max(0.01, w + random.uniform(-0.05, 0.05) * chaos)
            for w in base_weights
        ]

        total = sum(weights)
        weights = [w / total for w in weights]
        for x,y in self.maze.get_spawnpoints(1,1,count):
            factory = [Enemy(self, (x,y), self.assets['entity'], render_offset=[0,-8], e_type='Enemy'),Wisp(self, (x,y), self.assets['gem'], render_offset=[0,-15], e_type='Enemy'),
                Plant(self, (x,y), None, render_offset=[0,-12], e_type='Enemy'),Converter(self, (x,y), [replace_colors(img, self.color_table) for img in self.assets['Converter']], render_offset=[0,-2], e_type='Enemy'),
                Constructor(self, (x,y), replace_colors(self.assets['Constructor'], self.color_table), render_offset=[0,-8], e_type='Enemy'),
                Trapper(self, (x,y), self.assets['Trapper'], render_offset=[0,-4], e_type='Enemy')
                ]
            result = random.choices(factory,weights=weights,k=1)[0]
            self.entities.append(result)
            


    def render(self, screen, maze, player=None, offset=(0,0), entities={}):
        K = (player.x, player.y)
        entities.setdefault(K, []).append(player)

        self.display.fill((0,0,0))
        self.maze.draw_map(self.display, offset=offset, entities=entities, rect=self.controller.screen_rect, paused=self.paused)
        pygame.transform.scale_by(self.display, 3.0, self.scaled_display)  # scale into reusable surface
        screen.blit(self.scaled_display, (0, 0)) 
        # self.scaled_display = pygame.transform.scale(self.display, screen.get_size())
        # screen.blit(self.scaled_display, (0, 0))
        
        pygame.draw.rect(screen, self.color_table[(255,0,0)], (25,5,140,80))
        pygame.draw.rect(screen, BLACK, (30,10,130,70))
        self.controller.font.render(screen, str(self.score), (40,15))
        self.controller.font.render(screen, '@' * self.lives, (40,35))
        self.controller.font.render(screen, f'{min(self.player.gems, 100)}/{self.player.cooldown}', (40,55))
        
        pygame.draw.rect(screen, self.color_table[(0,0,255)], (480,5,140,80))
        pygame.draw.rect(screen, BLACK, (485,10,130,70))
        self.controller.font.render(screen, f'Level {self.level}', (500,15))
        self.controller.font.render(screen, f'Stage {self.stage + 1}', (500,35))
    

    
    def test(self):
        ''' Returns render offset for player to be center of the screen '''
        p_x, p_y = self.maze.maze[self.player.y][self.player.x].render_pos

        center_x = self.display.get_width() // 2   
        center_y = self.display.get_height() // 2  
        return [center_x - p_x, center_y - p_y]


    def reset(self, skip=False):
        WIDTH, HEIGHT = random.randint(5,10) * 2 + 1, self.maze.width
        if self.stage:
            times = 5 if skip else 1
            for _ in range(times):
                if self.level % 10 == 0 and self.level > 0:
                    self.player.cooldown = min(self.player.cooldown + 1, 100)
                if self.level % 5 == 0 and self.level > 0:
                    self.lives = min(self.lives + 1, 8)
                changes = [
                    (5, 0),   
                    (0, 5),   
                    (5, 5),  
                    (-5, 0), 
                    (0, -5)
                 ]

                weights = [0.5, 0.5, 0.25, 0.05, 0.05]
                change = random.choices(changes, weights=weights, k=1)[0]
                self.settings['sparsity'][0] = (self.settings['sparsity'][0] + change[0]) % 100
                self.settings['sparsity'][1] = (self.settings['sparsity'][1] + change[1]) % 100

                weights = [0.5, 0.2, 0.1, 0.05]
                changes = [2,5,10, -10]
                self.settings['room_attempts'] = (self.settings['room_attempts'] + random.choices(changes, weights=weights, k=1)[0]) % 50 if random.randint(0,1) == 1 else self.settings['room_attempts']
                self.settings['elevator_prob'] = (self.settings['elevator_prob'] + random.choices(changes, weights=weights, k=1)[0]) % 101 if self.level % 2 == 0 else random.randint(-20,100)
                changes = [2,3,7, -2]
                self.settings['stair_prob'] = (self.settings['stair_prob'] + random.choices(changes, weights=weights, k=1)[0]) % 101 
        
                self.settings['glass_prob'] = 0 if self.level % 4 != 0 or self.level < 5 else random.randint(WIDTH+HEIGHT, 100)
                self.settings['player_prob'] = 0 if self.level % 2 != 0 or self.level < 7 else random.randint(WIDTH+HEIGHT, 100-HEIGHT)
                self.settings['enemy_prob'] = 0 if self.level % 3 != 0 or self.level < 6 else random.randint(WIDTH+HEIGHT, 100-WIDTH)
                self.settings['wall_height'] = random.choice((2,3,4,5,6,7,8,None))
                self.color_table={(255,0,0):self.color_table[(0,0,255)], (0,0,255):random.choice(colors), (25,20,26):(95,87,79)}
                self.level += 1
        self.stage = not self.stage
        self.paused = False
        self.gems = set()
        self.gemstones = set()
        self.traps = {}
        self.player.reset()
        for i in range(50):
            try:
                sprite = 'tile'
                self.maze = Maze(self, WIDTH, HEIGHT, self.assets['gem'], self.color_table, self.settings['stair_prob'], self.settings['room_attempts'],
                                 self.settings['sparsity'], self.settings['elevator_prob'], self.settings['player_prob'], self.settings['enemy_prob'], 30, self.settings['glass_prob'],
                                 wall_height=self.settings['wall_height'])
                if skip:
                    self.maze.maze[HEIGHT - 2][WIDTH - 2] = Portal_Tile(self.maze, self.maze.maze[HEIGHT - 2][WIDTH - 2].z1, WIDTH - 2, HEIGHT - 2)
                
                portal_tile = 0
                self.player.pos = [self.maze.w - 2, self.maze.h - 2]
                self.render_offset = self.test()
                pos_dict = set()
                
                if not self.stage:
                    self.add_enemies(5 + (self.level % 5))
                else:
                    for i, pos in enumerate(self.maze.get_spawnpoints(1,1,len(self.entities))):
                            self.entities[i].pos = list(pos)
                            self.entities[i].path = []
                for enemy in self.entities:
                    if isinstance(enemy, Plant):
                        for x,y in self.maze.generate_gems(20,0)[0]:
                            self.maze.maze[y][x] = Plant_Tile(self.maze, self.maze.maze[y][x].z, x,y)
                            

                for i in range(10):
                    gems, gemstones = self.maze.generate_gems(20, 1 + self.level // 2)
                    for l in gems:
                        self.gems.add(l)
                    for x,y in gemstones:
                        if portal_tile < 3 and random.randint(0,1) == 0:
                            at = self.maze.maze[y][x]
                            self.maze.maze[y][x] = Portal_Tile(self.maze, at.z1, x,y)
                                
                        else:
                            self.gemstones.add(Gemstone(self,(x,y), self.assets['gemstone'],hp=1))
                        
                collected = {tuple(g.pos) for g in self.gemstones}

                self.gems = {
                    (x, y) for (x, y) in self.gems
                    if (x, y) not in collected and self.maze.maze[y][x].type != 'Portal_Tile'
                }
                self.gemstones = {
                    gem for gem in self.gemstones
                    if gem.at != 'Portal_Tile'
                }
                self.maze.set_tile_outline()
                self.player.z = self.player.at.z
                return
            except RuntimeError:
                pass
        

    def quit(self):
        stats_screen = self.controller.windows['Stats']
        stats_screen.load_from_game(self)
        self.controller.mode = 'Stats'

    def death(self):
        self.sounds['death'].play()
        maze = self.maze.maze
        d1 = random.randint(5, 22 - (self.lives * 2) ) if self.level % 2 == 0 else 1
        d2 = random.randint(5, max(5, (self.lives - 8) ** 2)) if self.level % 2 == 1 else 1
                            
        self.maze.combine(self.maze.maze, self.maze.carve(self.maze.create_maze(self.maze.width, self.maze.height)), [d1, d2], preserve_current=True)
        for i in range(2):
            self.maze.fix_maze(self.maze.maze)
        self.maze.add_elevators(90 - 15 * self.lives)
        
        if not self.maze.connectivity():
            self.maze.maze = maze
        for i, row in enumerate(self.maze.maze):
            for j, cell in enumerate(row):
                if self.maze.maze[i][j] is not None:
                    self.maze.maze[i][j].tile_outline = set()

        self.maze.set_tile_outline()
        egg = self.player.egg
        self.lives -= 1
        self.player.reset()
        self.player.egg = egg
        self.player.pos = [self.maze.w - 2, self.maze.h - 2]
        count = len(self.entities)
        spawnpoints = [list(pos) for pos in self.maze.get_spawnpoints(1,1, count)]
        self.player.gems = 0
        for i,entity in enumerate(self.entities):
            entity.pos = spawnpoints[i]
            entity.path = []
            entity.movement_offset = [0,0]
            entity.active = True
            
            

    def update(self, events, screen):
            if self.skip:
                self.skip = False
                self.stage = True
                self.gems = set()
                self.gemstones = set()
                self.player.gems = 0
                self.reset(True)
                return
            
            if self.gems == set():
                if self.stage:
                    self.score += 2000 
                else:
                    self.score += 1000
                self.reset()
                return
            
            self.sound = [None,0]
            entity_dict = {}
            
            if not self.paused and self.maze.w*self.maze.h == self.maze.render_counter:
                self.tick[0] = (self.tick[0] + 1) % self.tick[1]
            
                self.player.update(self.tick[0], movement=self.movement)
                
                pos_dict = {tuple(v.pos):v for v in self.entities} | {w: None for w in self.gemstones}
                self.traps = {
                    pos: trap for pos, trap in self.traps.items()
                    if trap.hp > 0
                }
                for pos in self.traps:
                        trap = self.traps[pos]
                        trap.update()
                        entity_dict.setdefault((trap.x, trap.y), []).append(trap)
                
                alive_gemstones = set()

                for gem in self.gemstones:
                    if gem.hp <= 0:
                        self.score += 10 * (1 + self.player.gems)
                        self.sound =[self.sounds['powerup'], 1]
                    else:
                        gem.update()
                        entity_dict.setdefault((gem.x, gem.y), []).append(gem)
                        alive_gemstones.add(gem)

                self.gemstones = alive_gemstones
                    
                to_remove = set()
                for gem in self.gems:
                    if tuple(self.player.pos) == gem or gem in self.gemstones:
                        if self.sound[0] is None:
                            self.sound =[self.sounds['gem'][int(self.player.z) % 7],0]
                        to_remove.add(gem)
                        self.player.gems = min(100, self.player.gems + 1)
                        self.score += self.player.gems + 1
                    else:
                        entity_dict.setdefault(gem, []).append(Gem(self, gem, self.maze.assets['Gem'], e_type='Gem', render_offset=[0,0]))

                self.gems.difference_update(to_remove)
                self.entities = [e for e in self.entities if e.hp > 0]
                for entity in self.entities:
                        entity.update(pos_dict)
                        if (entity.x, entity.y) in self.gems:
                            self.gems.remove((entity.x, entity.y))
                            if self.sound[0] is None:
                                self.sound =[random.choice(self.sounds['gem']),0]
                            entity.gems += 1
                        if entity.type == "Enemy" and self.player.invincibility <= 0:
                            if entity.pos == self.player.pos and 12 > abs(self.player.movement_offset[0] - entity.movement_offset[0] + self.player.movement_offset[1] - entity.movement_offset[1]):
                                e_mask, player_mask = pygame.mask.from_surface(entity.img), pygame.mask.from_surface(self.player.img)
                                e_pos = [entity.render_pos[0]+entity.render_offset[0]+entity.movement_offset[0],entity.render_pos[1]+entity.render_offset[1]+entity.movement_offset[1]]
                                p_pos = [self.player.render_pos[0]+self.player.movement_offset[0]+self.player.render_offset[0],self.player.render_pos[1]+self.player.movement_offset[1]+self.player.render_offset[1]]
                                if player_mask.overlap(e_mask, (e_pos[0]-p_pos[0],e_pos[1]-p_pos[1])): 
                                    if self.lives > 0:
                                        self.death()
                                        continue
                                    else:
                                        self.quit()
                        entity_dict.setdefault((entity.x, entity.y), []).append(entity)


            if self.player.egg is not None:
                ex,ey = self.player.egg
                entity_dict.setdefault((ex, ey), []).append(Entity(self,(ex,ey),self.assets['egg']))
                    
            padding = 45
            x,y = self.player.render_pos
            x += int(self.render_offset[0]) + self.player.movement_offset[0] + self.player.render_offset[0]
            y += int(self.render_offset[1]) + self.player.movement_offset[1] + self.player.render_offset[1]
            if x > self.display.get_width() - padding:
                self.render_offset[0] -= (x - self.display.get_width() / 2) / 20
            if x < 0 + padding:
                self.render_offset[0] -= (x - self.display.get_width() / 2) / 20
            if y > self.display.get_height() - padding:
                self.render_offset[1] -= (y - self.display.get_height() / 2) / 20
            if y < 0 + padding:
                self.render_offset[1] -= (y - self.display.get_height() / 2) / 20

            if not self.paused:
                self.render(screen, self.maze, self.player, [int(self.render_offset[0]), int(self.render_offset[1])], entities=entity_dict)
            
            if self.sound[0] is not None:
                self.sound[0].play()
            
            
            for event in events:
                if event.type == pygame.QUIT:
                    self.quit()
        
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_0, pygame.K_o, pygame.K_v):
                        if self.player.egg is not None:
                            self.player.destroy_egg()
                    if event.key in (pygame.K_9, pygame.K_i, pygame.K_c):
                            self.player.create_egg()
                    if event.key == pygame.K_x:
                        self.maze.print_maze()
                    if event.key == pygame.K_z:
                        self.gems = set()
                        self.sounds['gem'][int(self.player.z) % 7].play()
                    if event.key == pygame.K_p:
                        self.paused = not self.paused
                    if not self.paused:
                        if event.key in (pygame.K_w, pygame.K_UP):
                            self.movement[2] = True
                        elif event.key in (pygame.K_d, pygame.K_RIGHT):
                            self.movement[3] = True
                        elif event.key in (pygame.K_s, pygame.K_DOWN):
                            self.movement[0] = True
                        elif event.key in (pygame.K_a, pygame.K_LEFT):
                            self.movement[1] = True
                        
                if event.type == pygame.KEYUP:
                    if event.key in (pygame.K_w, pygame.K_UP):
                        self.movement[2] = False
                    elif event.key in (pygame.K_d, pygame.K_RIGHT):
                        self.movement[3] = False
                    elif event.key in (pygame.K_s, pygame.K_DOWN):
                        self.movement[0] = False
                    elif event.key in (pygame.K_a, pygame.K_LEFT):
                        self.movement[1] = False
            
            
                    if event.key in [pygame.K_q,pygame.K_ESCAPE]:
                        self.quit()
    

                            
                    
        
