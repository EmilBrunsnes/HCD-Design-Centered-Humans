import pygame
import sys
window_width = 1000
window_height = 600
pygame.init()
window = pygame.display.set_mode((window_width,window_height))
window.fill((255, 255, 255))

canvas = pygame.Surface((window_width,window_height)) #used to draw on
canvas.fill((255, 255, 255))

class Drawer(pygame.sprite.Sprite):
    def __init__(self, color = (0,0,0), height=10, width=10):
        super().__init__()
        
        self.brush_size = width
        self.image = pygame.Surface([width, height])
        self.image.fill((255,255,255))

        pygame.draw.rect(self.image, color, pygame.Rect(0, 0, width, height),2)

        self.rect = self.image.get_rect() 
        
    def move(self, direction, speed=1):
        self.rect.x += direction[0]*self.brush_size*speed
        self.rect.y += direction[1]*self.brush_size*speed
        
        window_size = window.get_rect()
        self.rect.clamp_ip(window_size)
        
    def draw(self, colour):
        pygame.draw.rect(canvas,
                        colour,
                        [ self.rect.x,self.rect.y,self.brush_size,self.brush_size],
                        0)
             
running = True
drawers = pygame.sprite.Group()
drawer = Drawer(3)
drawers.add(drawer)
clock = pygame.time.Clock()

movement_dict = {
    pygame.K_w : [0,-1] ,
    pygame.K_s : [0,1] ,
    pygame.K_a : [-1,0] ,
    pygame.K_d : [1,0]
}

color_dict = {
    pygame.K_r: (255,0,0),
    pygame.K_g: (0,255,0),
    pygame.K_b: (0,0,255),
    pygame.K_t: (0, 255, 255),
    pygame.K_w: (255,255,255)
}

while running:
    window.fill((255,255,255))
    window.blit(canvas, (0,0))
    drawer.update()  
    drawers.draw(window)
    pygame.display.flip()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            sys.exit()
            
        if event.type == pygame.KEYDOWN:
            if event.key in color_dict:
                drawer.draw(color_dict[event.key])
            
                
    keys = pygame.key.get_pressed()
    
    for key, direction in movement_dict.items():
        if keys[key]:
            drawer.move(direction)
                
    clock.tick(10)
pygame.quit()

