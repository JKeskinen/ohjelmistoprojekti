import pygame
from GameStateManager import GameStateManager
from States.MainMenuState import MainMenuState

def main():
    pygame.init()

    manager = GameStateManager(MainMenuState(None))

    manager.run()

if __name__ == "__main__":
    main()