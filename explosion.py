"""Räjähdykset: valittava spritekansio (dynamite tai bomb_cartoon).

Oletuksena käytetään edelleen Explosions_dynamiteStyle-kansiota.
Halutessa voidaan vaihtaa esimerkiksi bomb_cartoon-kansioon ilman,
että muu peli-integraatio muuttuu.
"""

import os
import re

import pygame


class Explosion:
    """Yksittäinen räjähdysanimaatio."""

    def __init__(self, frames, pos, fps=20):
        if not frames:
            raise ValueError("Explosion requires at least one frame")

        self.frames = frames
        self.pos = pygame.Vector2(pos)
        self.frame_time = 1.0 / max(1, fps)
        self.time_acc = 0.0
        self.frame_index = 0
        self.dead = False

        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def update(self, dt_ms):
        if self.dead:
            return

        self.time_acc += dt_ms / 1000.0
        while self.time_acc >= self.frame_time:
            self.time_acc -= self.frame_time
            self.frame_index += 1
            if self.frame_index >= len(self.frames):
                self.dead = True
                return
            self.image = self.frames[self.frame_index]
            self.rect = self.image.get_rect(center=self.rect.center)

    def draw(self, screen, camera_x=0, camera_y=0):
        screen.blit(self.image, (self.rect.x - camera_x, self.rect.y - camera_y))


class ExplosionManager:
    """Hallinnoi aktiivisia räjähdyksiä valitulla räjähdysspritekansiolla."""

    _SLICE_PATTERN = re.compile(r"slice(\d+)\.png$", re.IGNORECASE)

    def __init__(
        self,
        boss_size=(150, 150),
        enemy_size=(60, 60),
        hit_size=(64, 64),
        sprite_folder="Explosions_dynamiteStyle",
    ):
        self.explosions = []
        self.boss_size = boss_size
        self.enemy_size = enemy_size
        self.hit_size = hit_size
        self.sprite_folder = sprite_folder
        self.frames_by_type = {
            "boss": [],
            "enemy": [],
            "hit": [],
        }

    @staticmethod
    def _make_dark_background_transparent(image, max_r=85, max_g=55, max_b=55):
        """Poistaa dynamite-kuvien tumman punaruskean taustan."""
        img = image.copy()
        width, height = img.get_size()
        for y in range(height):
            for x in range(width):
                r, g, b, a = img.get_at((x, y))
                if a <= 0:
                    continue
                if r <= max_r and g <= max_g and b <= max_b and r >= g and r >= b:
                    img.set_at((x, y), (r, g, b, 0))
        return img

    @classmethod
    def _load_frames_from_folder(cls, folder_name, size):
        folder = os.path.join(os.path.dirname(__file__), "images", folder_name)
        if not os.path.isdir(folder):
            return []

        numbered_files = []
        for filename in os.listdir(folder):
            match = cls._SLICE_PATTERN.fullmatch(filename)
            if not match:
                continue
            numbered_files.append((int(match.group(1)), filename))

        numbered_files.sort(key=lambda item: item[0])

        frames = []
        for _, filename in numbered_files:
            path = os.path.join(folder, filename)
            image = pygame.image.load(path).convert_alpha()
            image = pygame.transform.scale(image, size)
            image = cls._make_dark_background_transparent(image)
            frames.append(image)
        return frames

    def load_all_defaults(self):
        """Lataa boss/enemy/hit-kehykset valitusta spritekansiosta."""
        self.frames_by_type["boss"] = self._load_frames_from_folder(self.sprite_folder, self.boss_size)
        self.frames_by_type["enemy"] = self._load_frames_from_folder(self.sprite_folder, self.enemy_size)
        self.frames_by_type["hit"] = self._load_frames_from_folder(self.sprite_folder, self.hit_size)

    def _spawn_from_type(self, explosion_type, pos, fps):
        frames = self.frames_by_type.get(explosion_type) or []
        if not frames:
            return
        self.explosions.append(Explosion(frames, pos, fps=fps))

    def spawn_boss(self, pos, fps=20):
        self._spawn_from_type("boss", pos, fps)

    def spawn_enemy(self, pos, fps=20):
        self._spawn_from_type("enemy", pos, fps)

    def spawn_hit(self, pos, fps=24):
        frames = self.frames_by_type.get("hit") or self.frames_by_type.get("enemy")
        if not frames:
            return
        self.explosions.append(Explosion(frames, pos, fps=fps))

    def update(self, dt_ms):
        alive = []
        for ex in self.explosions:
            ex.update(dt_ms)
            if not ex.dead:
                alive.append(ex)
        self.explosions = alive

    def draw(self, screen, camera_x=0, camera_y=0):
        for ex in self.explosions:
            ex.draw(screen, camera_x, camera_y)