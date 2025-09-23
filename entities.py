from utils import to_iso

class Entity:
    def __init__(self, game, pos, sprite):
        self.game = game
        self.pos = list(pos)
        self.sprite = sprite
        self.path = None
        
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
    
    def render(self, screen, h, offset):
        x,y = self.render_pos
        screen.blit(self.sprite, (x + offset[0], y + offset[1]))
