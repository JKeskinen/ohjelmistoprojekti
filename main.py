"""
Peli entry point - Käynnistää MainMenu:n ensin
"""
import sys
import os

# Lisää ohjelmiston hakemisto Python-polkuun
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from MainMenu import MainMenu
import pygame

def main():
    """Käynnistää pelin"""
    pygame.init()
    
    # Näytä päävalikko
    menu = MainMenu()
    result = menu.run()
    
    # Jos käyttäjä valitsi "START GAME"
    if result == "start_game":
        # Tuo RocketGame ja käynnistä peli
        from RocketGame import start_game
        start_game()
    
    # Muussa tapauksessa peli sulkeutuu


if __name__ == "__main__":
    main()
