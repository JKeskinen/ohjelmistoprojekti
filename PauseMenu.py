import pygame
import sys

pygame.init()

# Näytön asetukset
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# Värit
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_BLUE = (52, 78, 91)
LIGHT_BLUE = (100, 150, 200)
HOVER_COLOR = (150, 200, 255)
SEMI_TRANSPARENT = (0, 0, 0, 150)

# Fontit
title_font = pygame.font.Font(None, 80)
button_font = pygame.font.Font(None, 50)


class Button:
    """Nappi-luokka pauseluokalle"""
    
    def __init__(self, x, y, width, height, text, color, text_color, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.action = action
        self.is_hovered = False
    
    def draw(self, surface):
        """Piirtää napin"""
        current_color = HOVER_COLOR if self.is_hovered else self.color
        pygame.draw.rect(surface, current_color, self.rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, self.rect, 3, border_radius=10)
        
        text_surf = button_font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    
    def is_clicked(self, pos):
        """Tarkistaa onko nappia klikattu"""
        return self.rect.collidepoint(pos)
    
    def update(self, pos):
        """Päivittää hover-tilan"""
        self.is_hovered = self.rect.collidepoint(pos)


class PauseMenu:
    """Pausemenun hallinta"""
    
    def __init__(self):
        self.buttons = [
            Button(
                SCREEN_WIDTH // 2 - 150,
                SCREEN_HEIGHT // 2 - 100,
                300,
                80,
                "CONTINUE",
                LIGHT_BLUE,
                WHITE,
                action="continue"
            ),
            Button(
                SCREEN_WIDTH // 2 - 150,
                SCREEN_HEIGHT // 2 + 20,
                300,
                80,
                "SETTINGS",
                LIGHT_BLUE,
                WHITE,
                action="settings"
            ),
            Button(
                SCREEN_WIDTH // 2 - 150,
                SCREEN_HEIGHT // 2 + 140,
                300,
                80,
                "QUIT",
                LIGHT_BLUE,
                WHITE,
                action="quit"
            ),
        ]
        self.clock = pygame.time.Clock()
        self.running = True
    
    def handle_events(self):
        """Käsittelee näppäimistö ja hiiri-eventit"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "continue"
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                for button in self.buttons:
                    if button.is_clicked(mouse_pos):
                        return button.action
        
        return None
    
    def draw(self, background_surface):
        """Piirtää pausemenun"""
        # Piirrä taustaväri semi-transparentilla
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        background_surface.blit(overlay, (0, 0))
        
        # Piirtää otsikko
        title_surf = title_font.render("PAUSED", True, WHITE)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 100))
        background_surface.blit(title_surf, title_rect)
        
        # Piirtää napit
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.update(mouse_pos)
            button.draw(background_surface)
        
        pygame.display.update()
    
    def run(self, background_surface):
        """Pääsilmukka pauselle"""
        while self.running:
            action = self.handle_events()
            
            if action == "continue":
                return "continue"
            elif action == "settings":
                return "settings"
            elif action == "quit":
                return "quit"
            
            self.draw(background_surface)
            self.clock.tick(60)
        
        return "continue"
