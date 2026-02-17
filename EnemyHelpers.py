"""
Module: EnemyHelpers.py
Dependencies: pygame, math, random, typing
Provides: helper functions `angle_dir`, `advance_frames` and classes `EnemyBullet`, `Muzzle` (projectile and muzzle animations)
Used by: enemy.py, boss_enemy.py, RocketGame.py, EnemyAI.py
"""

import math
import random
import pygame
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from enemy import Enemy


    # Tässä luokassa ladataan vihollisten sprite-kuvat ja hallitaan vihollisten ammuksia 
    # (EnemyBullet) ja lähtöpistettä (Muzzle) varten. 
    # Käytetään SpriteSettings-luokkaa, joka on suunniteltu lataamaan ja hallitsemaan sprite-kuvia, mukaan lukien vihollisten kuvat.


def angle_dir(angle: float) -> pygame.Vector2:
    return pygame.Vector2(math.cos(angle), -math.sin(angle))


def advance_frames(frames: list, frame_index: int, anim_timer: int, anim_speed: int, dt_ms: int, loop: bool = True):
    if not frames or anim_speed <= 0:
        return frame_index, anim_timer, (frames[0] if frames else None)
    anim_timer += int(dt_ms)
    while anim_timer >= anim_speed:
        anim_timer -= anim_speed
        frame_index += 1
        if frame_index >= len(frames):
            if loop:
                frame_index = frame_index % len(frames)
            else:
                return frame_index, anim_timer, frames[-1]
    return frame_index, anim_timer, frames[frame_index]


class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, pos: pygame.Vector2, vel: pygame.Vector2,
                 start_frames: Optional[list] = None,
                 flight_frames: Optional[list] = None,
                 explode_frames: Optional[list] = None,
                 speed: float = 420,
                 parent_enemy: Optional['Enemy'] = None):
        super().__init__()
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.speed = speed

        # animation lists
        self.start_frames = list(start_frames) if start_frames else []
        self.flight_frames = list(flight_frames) if flight_frames else []
        self.explode_frames = list(explode_frames) if explode_frames else []

        # animation state
        self.state = 'start' if self.start_frames else ('flight' if self.flight_frames else 'idle')
        self.frame_index = 0
        self.anim_timer = 0
        self.anim_speed = 80
        self.dead = False
        # if provided, attach start-frame animation to this enemy until it switches to flight
        self.parent_enemy: Optional['Enemy'] = parent_enemy
        # homing support: optional target (sprite) and remaining homing time in ms
        self.homing_target: Optional[object] = None
        self.homing_time_ms: int = 0
        self.homing_turn_rate_deg: float = 180.0
        # direction vector for spawn / attachment
        if self.vel.length_squared() > 0:
            self.dir_vec = self.vel.normalize()
        else:
            self.dir_vec = pygame.Vector2(1, 0)

        # initial image/rect
        if self.start_frames:
            self.image = self.start_frames[0]
        elif self.flight_frames:
            self.image = self.flight_frames[0]
        else:
            self.image = pygame.Surface((4,4), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    @classmethod
    def from_enemy(cls, enemy: 'Enemy', speed: float = 420):
        shots = getattr(enemy, 'shots', None)
        if not shots:
            return None

        start = shots.get('shotStart') or shots.get('shot_start') or shots.get('start') or shots.get('shotStart'.lower())
        flight = shots.get('shot4_asset') or shots.get('flight') or shots.get('shot')
        explode = shots.get('shot4_exp2') or shots.get('shot4_exp1') or shots.get('explode') or shots.get('exp')

        start_list = list(start) if start else []
        flight_list = list(flight) if flight else []
        explode_list = list(explode) if explode else []

        angle = enemy.display_angle
        dir_vec = angle_dir(angle)
        if dir_vec.length_squared() == 0:
            dir_vec = pygame.Vector2(1, 0)
        dir_vec.normalize_ip()

        spawn = pygame.Vector2(enemy.rect.center) + dir_vec * (max(enemy.rect.width, enemy.rect.height) // 2 + 6)
        vel = dir_vec * speed
        return cls(spawn, vel, start_frames=start_list, flight_frames=flight_list, explode_frames=explode_list, speed=speed, parent_enemy=enemy)

    def update(self, dt_ms: int, world_rect: pygame.Rect | None = None):
        if self.state == 'start':
            if self.parent_enemy is not None:
                p = self.parent_enemy
                angle = getattr(p, 'display_angle', 0.0)
                dir_vec = angle_dir(angle)
                if dir_vec.length_squared() == 0:
                    dir_vec = pygame.Vector2(1, 0)
                dir_vec.normalize_ip()
                self.dir_vec = dir_vec
                spawn = pygame.Vector2(p.rect.center) + dir_vec * (max(p.rect.width, p.rect.height) // 2 + 6)
                self.pos = spawn
                self.rect.center = (int(self.pos.x), int(self.pos.y))

            if self.start_frames:
                self.frame_index, self.anim_timer, img = advance_frames(self.start_frames, self.frame_index, self.anim_timer, self.anim_speed, dt_ms, loop=False)
                if self.frame_index >= len(self.start_frames):
                    self.state = 'flight' if self.flight_frames else 'idle'
                    self.frame_index = 0
                    self.parent_enemy = None
                    if self.state == 'flight' and self.flight_frames:
                        self.image = self.flight_frames[0]
                else:
                    self.image = img
            else:
                self.state = 'flight' if self.flight_frames else 'idle'
                if self.state == 'flight' and self.flight_frames:
                    self.image = self.flight_frames[0]
        elif self.state == 'flight':
            if self.flight_frames:
                self.frame_index, self.anim_timer, self.image = advance_frames(self.flight_frames, self.frame_index, self.anim_timer, self.anim_speed, dt_ms, loop=True)

            dt = dt_ms / 1000.0
            if self.homing_target is not None and self.homing_time_ms > 0:
                try:
                    target_pos = pygame.Vector2(self.homing_target.rect.center)
                    to_target = target_pos - self.pos
                    if to_target.length_squared() > 0.0001:
                        desired_angle = math.atan2(to_target.y, to_target.x)
                        cur_angle = math.atan2(self.vel.y, self.vel.x)
                        diff = (desired_angle - cur_angle + math.pi) % (2 * math.pi) - math.pi
                        max_turn = math.radians(self.homing_turn_rate_deg) * dt
                        if diff > max_turn:
                            diff = max_turn
                        elif diff < -max_turn:
                            diff = -max_turn
                        new_angle = cur_angle + diff
                        speed = self.vel.length() or (self.speed or 420)
                        self.vel.x = math.cos(new_angle) * speed
                        self.vel.y = math.sin(new_angle) * speed
                except Exception:
                    pass

                self.homing_time_ms -= int(dt_ms)
                if self.homing_time_ms <= 0:
                    self.homing_target = None
                    try:
                        self.explode()
                    except Exception:
                        self.dead = True

            self.pos += self.vel * dt
            self.rect.center = (int(self.pos.x), int(self.pos.y))

            if world_rect is not None and not world_rect.colliderect(self.rect):
                self.dead = True
        elif self.state == 'explode':
            if self.parent_enemy is not None:
                try:
                    p = self.parent_enemy
                    self.pos = pygame.Vector2(p.rect.center)
                    self.rect.center = (int(self.pos.x), int(self.pos.y))
                except Exception:
                    pass

            self.anim_timer += int(dt_ms)
            if self.anim_timer >= self.anim_speed:
                self.anim_timer -= self.anim_speed
                self.frame_index += 1
                if self.frame_index >= len(self.explode_frames):
                    self.dead = True
                else:
                    self.image = self.explode_frames[self.frame_index]

    def explode(self, parent: Optional['Enemy'] = None):
        if self.explode_frames:
            self.explode_frames = list(self.explode_frames)[:6]
            self.state = 'explode'
            self.frame_index = 0
            self.image = self.explode_frames[0]
            self.anim_timer = 0
            try:
                self.vel = pygame.Vector2(0, 0)
            except Exception:
                pass
            self.parent_enemy = parent
        else:
            self.dead = True

    def draw(self, screen: pygame.Surface, camera_x: int, camera_y: int):
        try:
            vx, vy = float(self.vel.x), float(self.vel.y)
            if abs(vx) > 0.001 or abs(vy) > 0.001:
                angle = math.atan2(-vy, vx)
                deg = math.degrees(angle)
                rotated = pygame.transform.rotate(self.image, deg)
                rrect = rotated.get_rect(center=(self.rect.centerx - camera_x, self.rect.centery - camera_y))
                screen.blit(rotated, rrect.topleft)
                return
        except Exception:
            pass

        screen.blit(self.image, (self.rect.x - camera_x, self.rect.y - camera_y))


class Muzzle:
    def __init__(self, parent_enemy: 'Enemy', frames: list, anim_speed: int = 80):
        self.parent = parent_enemy
        self.frames = list(frames)
        self.frame_index = 0
        self.anim_timer = 0
        self.anim_speed = anim_speed
        self.dead = False

    def update(self, dt_ms: int):
        if self.dead:
            return
        self.frame_index, self.anim_timer, img = advance_frames(self.frames, self.frame_index, self.anim_timer, self.anim_speed, dt_ms, loop=False)
        if self.frame_index >= len(self.frames):
            self.dead = True
            return

    def draw(self, screen: pygame.Surface, camera_x: int, camera_y: int):
        if self.dead or not self.parent:
            return
        img = self.frames[self.frame_index if self.frame_index < len(self.frames) else -1]
        angle = getattr(self.parent, 'display_angle', 0.0)
        dir_vec = angle_dir(angle)
        if dir_vec.length_squared() == 0:
            dir_vec = pygame.Vector2(1, 0)
        dir_vec.normalize_ip()
        pos = pygame.Vector2(self.parent.rect.center) + dir_vec * (max(self.parent.rect.width, self.parent.rect.height) // 2 + 6)
        screen.blit(img, (int(pos.x - camera_x - img.get_width() / 2), int(pos.y - camera_y - img.get_height() / 2)))


