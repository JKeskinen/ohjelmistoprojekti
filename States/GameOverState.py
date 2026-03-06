import pygame
from States.GameState import GameState
from States.MainMenuState import MainMenuState

class GameOverState(GameState):

    def update(self, events):

        for event in events:
            if event.type == pygame.KEYDOWN:
                self.manager.set_state(
                    MainMenuState(self.manager)
                )

    def draw(self, screen):
        screen.fill((0,0,0))