import pygame
import random
from entities import Entity
from maze import Maze
from structures import Elevator, Tile
from utils import *

NEIGHBORS = {(-1,0),(0,-1),(1,0),(0,1)}


class Game:
    def __init__(self):
        pygame.init()
        
        self.sprite = "block3"
        self.screen = pygame.display.set_mode((800, 600))
        self.display = pygame.Surface((400,300), pygame.SRCALPHA)
        self.clock = pygame.time.Clock()
        pygame.display.set_caption("Isometric")
        
        self.render_offset = [0,0]
        self.movement = [False, False, False, False]

        self.assets = {
            'elevator': load_image('elevator1.png'),
            'block': load_image('block.png'),
            'block1': load_image('block1.png'),
            'block2': load_image('block2.png'),
            'block3': load_image('block3.png'),
            'block4': load_image('block4.png'),
            'block5': load_image('block5.png'),
            'entity': load_image('ball.png'),
            'ramp_right': load_image('ramp.png'),
            'ramp_left': pygame.transform.flip(load_image('ramp.png'), True, False),
            'wall': load_image('wall.png'),
            'player': load_image('gem.png')
        }
        self.maze = Maze(self, 21,21, 'block1', 'elevator')
        self.start_level()
        
    def start_level(self):
        self.player = Entity(self, [1,1], self.assets['player'])
        self.tick = [0, 60]


    def render(self, maze, player=None, offset=(0,0), entities=[]):
        dz = 0

        self.display.fill((40, 0, 40))
        self.maze.draw_map(self.display, offset=offset)
        if player is not None:
            tile = self.player.at
            if tile.type == 'Elevator':
                if tile.time_stopped <= 0:
                    dz = .5 * tile.direction
            self.player.render(self.display, self.maze.WALL_HEIGHT, offset=offset)
        # for e in entities:
        #     print(maze[e[1]][e[0]].z)
        #     print( [offset[0], offset[1] - 12], "entity")
            
        #     draw_block(display, e[0], e[1], 1, maze[e[1]][e[0]].z, offset=[offset[0], offset[1] - 12], sprite="entity")
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
        while 1:
            try:
                WIDTH, HEIGHT = random.randint(3,10) * 2 + 1, random.randint(3,10) * 2 + 1 
                i = random.randint(0,5)
                sprite = 'block' + str(i) if i != 0 else 'block'
                self.maze = Maze(self, WIDTH, HEIGHT, sprite, 'elevator', random.randint(0,100), random.randint(-5,10), [random.randint(0,100), random.randint(0,100)], random.randint(-20,100))
                self.player.pos = [1,1]
                self.render_offset = self.test()
                self.player.path = []
                
                return
            except RuntimeError:
                pass

    def run(self):
        running = True
        while running:
            self.tick[0] = (self.tick[0] + 1) % self.tick[1]
            diff = [0,0]
            if self.tick[0] % 5 == 0:
        
                if self.player.path == [] or self.player.path is None:
                    new_player, diff = self.maze.border_check(self.player.pos, [self.movement[1] - self.movement[3], self.movement[0] - self.movement[2]])
                else:
                    next_coord = self.player.path[0]
                    cell, next_cell = self.player.at, self.maze.maze[next_coord[1]][next_coord[0]]
                    if next_cell.z == next_coord[2]:
                        new_player, diff = self.maze.border_check(self.player.pos, [next_coord[0] - self.player.x, next_coord[1] - self.player.y])
                        if list(next_coord[:2]) == new_player:
                            self.player.path.pop(0)
                # print(diff)
                self.render_offset[1] -= diff[1]
                self.render_offset[0] -= diff[0]
                self.player.pos = new_player
    
            # if self.player.pos == [WIDTH - 2, HEIGHT - 2] and self.tick[0] == 0:
            #     r = reset()
            #     WIDTH = r['w']
            #     HEIGHT = r['h']
            #     maze = r['maze']
            #     player = r['player']
            #     render_scroll = r['scroll']
            #     path = r['path']
            #     sprite = 'block1'
            #     print(sprite)
            # print(sprite)
            # if entity_path == [] or entity_path is None:
            #     entity_path = trace(entity, player, maze)
            # elif tick[0] % 5 == 0:
            #     entity = entity_path.pop(0)
    
            self.render_offset[1] += self.render(self.maze, self.player, self.render_offset, [], )
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
        
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_e:
                        self.maze.add_elevators(60)
                    if event.key == pygame.K_p:
                        self.maze.print_maze(spacing="\n=============0====================\n")
                    if event.key == pygame.K_c:
                        self.reset()
                        continue

                    # if event.key == pygame.K_b:
                    #     for i in range(100):
                    #         WIDTH, HEIGHT = random.randint(3,10) * 2 + 1, random.randint(3,10) * 2 + 1
                    #         print(WIDTH,HEIGHT)
                    #         maze = create_maze(WIDTH, HEIGHT)
                    #         maze = carve(generate_rooms(maze, random.randint(0,10)), stair_prob=random.randint(-20,100))
                    #         maze = combine(maze, carve(create_maze(WIDTH,HEIGHT), 0), (random.randint(0,100),random.randint(0,100)))
                    #         fix_maze(maze)
                    #         player = [1,1]
                    #         print_maze(maze)
                    #         render_scroll = test(maze, display)
                    #         print(render_scroll, "pos player")
                    #         path = trace(player, (WIDTH - 2, HEIGHT - 2), maze)
                    #         if (path is None):
                    #             print("ATTEMPT", i + 1, '#')
                    #             break
                    
                    #     continue

                    if event.key == pygame.K_t:
                        self.player.path = self.maze.trace(self.player.pos, (self.maze.width - 2, self.maze.height - 2)) 
                    # if event.key == pygame.K_SPACE:
                    #     player = [1,1]
                    #     fix_maze(maze)
                    #     print_maze(maze, "\n=====================================\n")
                    #     render_scroll = test(maze, display)
                    #     print(render_scroll)
                
                    if event.key == pygame.K_UP:
                        self.render_offset[1] += 10
                
                    elif event.key == pygame.K_DOWN:
                        self.render_offset[1] -= 10
                
                    elif event.key == pygame.K_RIGHT:
                        self.render_offset[0] -= 10
                
                    elif event.key == pygame.K_LEFT:
                        self.render_offset[0] += 10
                    if event.key == pygame.K_w:
                        self.movement[2] = True
                    elif event.key == pygame.K_d:
                        self.movement[3] = True
                    elif event.key == pygame.K_s:
                        self.movement[0] = True
                    elif event.key == pygame.K_a:
                        self.movement[1] = True
                    if event.key == pygame.K_r:
                        WALL_SPACING = (WALL_SPACING + 1) % 46
                
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
