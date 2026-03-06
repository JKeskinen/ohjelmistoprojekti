import pygame


class GameStateManager:

    def __init__(self, initial_state):
        pygame.init()

        self.screen = pygame.display.set_mode((1600, 800))
        pygame.display.set_caption("Rocket Game")

        self.clock = pygame.time.Clock()
        self.running = True

        self.state = initial_state
        self.state.manager = self

    def set_state(self, new_state):
        """Vaihtaa pelitilan"""
        self.state = new_state
        self.state.manager = self

    def run(self):
        """Pelin pääsilmukka"""

        while self.running:

            events = pygame.event.get()

            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False

            # Päivitä state
            if self.state:
                self.state.update(events)

            # Piirrä state
            if self.state:
                self.state.draw(self.screen)

            pygame.display.flip()

            self.clock.tick(60)

        pygame.quit()