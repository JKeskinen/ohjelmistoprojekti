import pygame
from States.GameState import GameState
from States.PlayState import PlayState

class LevelCompleteState(GameState):

    def update(self, events):

        for event in events:
            if event.type == pygame.KEYDOWN:
                self.manager.set_state(
                    PlayState(self.manager)
                )

    def draw(self, screen):
        screen.fill((0,0,0))