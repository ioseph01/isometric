from scripts.utils import replace_colors, load_image
import pygame

# PLEASE NOTE, HEART SYMBOL IS '@'

def clip(surf,x,y,x_size,y_size):
    handle_surf = surf.copy()
    clipR = pygame.Rect(x,y,x_size,y_size)
    handle_surf.set_clip(clipR)
    image = surf.subsurface(handle_surf.get_clip())
    return image.copy()

class Font():
    def __init__(self, path, color=(255,255,255)):
        self.spacing = 1
        self.character_order = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','.','-',',',':','+','\'','!','?','0','1','2','3','4','5','6','7','8','9','(',')','/','_','=','\\','[',']','*','"','<','>',';', '@']
        font_img = load_image(path)
        current_char_width = 0
        self.characters = {}
        character_count = 0
        skip = False
        for x in range(font_img.get_width()):
            c = font_img.get_at((x, 0))
            if c[0] == 127:
                if not skip:
                    char_img = clip(font_img, x - current_char_width, 0, current_char_width, font_img.get_height())
                    self.characters[self.character_order[character_count]] = replace_colors(char_img.copy(), {(255,0,0):color})
                    character_count += 1
                    current_char_width = 0
                    skip = True
                    
            else:
                current_char_width += 1
                skip = False
                
        self.space_width = self.characters['A'].get_width()

    def render(self, surf, text, loc):
        x_offset = 0
        for char in text:
            if char != ' ':
                surf.blit(self.characters[char], (loc[0] + x_offset, loc[1]))
                x_offset += self.characters[char].get_width() + self.spacing
            else:
                x_offset += self.space_width + self.spacing
                
    def get_width(self, text):
        width = 0
        for char in text:
            if char != ' ' and char in self.characters:
                width += self.characters[char].get_width() + self.spacing
            else:
                width += self.space_width + self.spacing
        return width
