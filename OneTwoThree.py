import pygame as pg
import sys
import random

pg.init() # câu lệnh có tác dụng khởi tạo tất cả các module được sử dụng trong thư viện pygame
# Khởi tạo màn hình
screen= pg.display.set_mode((800,600))
pg.display.set_caption("Kéo púa pao hadmade")
# Khởi tạo các biến
clock = pg.time.Clock() #đây là đối tượng đồng hồ để giúp chúng ta điều chỉnh tốc độ của game
BLUE = (223,236,255)
WHITE = (255,255,255)
background = pg.image.load("assets/background.png")
running= True
#tạo 1 nút không có chức năng
class Button:
    def __init__(self, text, x, y, width, height,radius, color, hover_color):
        self.text = text
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.radius = radius
        self.color = color
        self.hover_color = hover_color
        self.rect = pg.Rect(x, y, width, height)
        self.clicked = False
        self.hovered = False
        Button.draw_button(self)
    
    def draw_button(self):
        pg.draw.rect(screen, self.hover_color if self.hovered else self.color, self.rect)
        font = pg.font.Font(None, 36)
        text = font.render(self.text, True, BLUE)
        text_rect = text.get_rect(center = self.rect.center)
        screen.blit(text, text_rect)
        #border
        pg.draw.rect(screen, BLUE, self.rect, 2)

    def check_hover(self, mouse_pos):
        if self.rect.collidepoint(mouse_pos):
            self.hovered = True
        else:
            self.hovered = False
        Button.draw_button(self)

# Vòng lặp chính
while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
        if event.type == pg.MOUSEBUTTONDOWN:
            if play_button.rect.collidepoint(event.pos):
                print("Button clicked")

        if event.type == pg.MOUSEMOTION:
            play_button.check_hover(event.pos)

    screen.fill(BLUE)
    screen.blit(background,(0,0)) # vẽ hình ảnh lên màn hình
    play_button= Button("Play", 300, 200, 200, 80,20, WHITE, BLUE)
    pg.display.flip()
    clock.tick(60)
pg.quit()