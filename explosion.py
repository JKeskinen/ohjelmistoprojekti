#bossin räjähdys
import pygame

class Explosion:
    def __init__(self, frames, pos, fps=20):
        self.frames = frames
        self.pos = pygame.Vector2(pos)
        self.fps = fps
        self.t = 0.0
        self.idx = 0
        self.dead = False

        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def update(self, dt_ms):
        if self.dead:
            return

        dt = dt_ms / 1000.0
        self.t += dt

        frame_time = 1.0 / max(1, self.fps)
        while self.t >= frame_time:
            self.t -= frame_time
            self.idx += 1
            if self.idx >= len(self.frames):
                self.dead = True
                return
            self.image = self.frames[self.idx]
            self.rect = self.image.get_rect(center=self.rect.center)

    def draw(self, screen, camera_x=0, camera_y=0):
        # maailma-koord -> ruutu-koord
        screen.blit(self.image, (self.rect.x - camera_x, self.rect.y - camera_y))