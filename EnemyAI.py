"""
Module: EnemyAI.py
Dependencies: pygame, math, random, enemy (class Enemy)
Provides: `StraightEnemy`, `CircleEnemy` (movement/AI behaviors: figure-8, magnet steering, circle behaviors)
Used by: RocketGame.py
"""

import math
import random
import pygame
from typing import Optional
from enemy import Enemy


class StraightEnemy(Enemy):
    """Lentää suoraan valittuun suuntaan"""
    def __init__(self, image, x, y, speed=220, path_type: str = 'random', pattern_params: dict | None = None):
        super().__init__(image, x, y)
        angle = random.uniform(0, math.tau)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.speed = speed

        # use float position for smooth movement
        self.pos = pygame.Vector2(self.rect.center)

        # velocity vector for physics (px / s)
        self.vel = pygame.Vector2(self.vx, self.vy)

        # boost/turbo flags (can be assigned externally)
        self.turbo = False
        self.turbo_multiplier = 1.5

        # exhaust/shot lists can be attached externally (e.g. RocketGame)
        # self.exhaust_turbo = []
        # self.exhaust_normal = []
        # self.shots = []

        # simple exhaust animation state
        self.exhaust_index = 0
        self._exhaust_timer = 0
        self.exhaust_speed_ms = 80
        # random motion nudges
        self.random_motion = True
        self._change_timer = 0
        self._change_interval_min = 400
        self._change_interval_max = 1200
        self._change_interval = random.randint(self._change_interval_min, self._change_interval_max)
        # simple bounce settings: when colliding with world bounds, perform a short bounce
        self.simple_bounce = True
        self.bouncing = False
        self.bounce_duration = 2.0  # seconds (longer, calmer bounce)
        self.bounce_timer = 0.0
        self.bounce_initial_vel = pygame.Vector2(0, 0)
        # Bounce tuning: strength scales initial reverse impulse,
        # oscillations = how many half-oscillations over duration,
        # damping controls how quickly oscillation amplitude decays.
        self.bounce_strength = 1.8
        self.bounce_oscillations = 2.0
        self.bounce_damping = 2.2
        # gravity / attraction settings
        self.gravity_enabled = False
        self.gravity_center = pygame.Vector2(0, 0)
        self.gravity_strength = 0.0
        self.max_speed = max(200, speed * 2)
        # ensure display_angle faces initial velocity
        self.display_angle = math.atan2(-self.vel.y, self.vel.x)

        # pathing mode: 'random' (legacy) or 'figure8'
        self.path_type = path_type
        params = pattern_params or {}
        # figure-8 parameters (pixels, seconds)
        self.pattern_A = float(params.get('A', 140.0))
        self.pattern_B = float(params.get('B', 80.0))
        self.pattern_period = float(params.get('period', 4.0))
        self._pattern_time = params.get('phase', random.uniform(0, self.pattern_period))
        self._pattern_center_set = False

        # Magneettinen vetovoima pelaajaan, joka saa vihollisen kiertämään pelaajaa ja yrittämään osua siihen. Vältetään seinäkiinnittymistä ja luodaan dynaamisempi liike.
        self.magnet_enabled = True
        self.magnet_radius = float(params.get('magnet_radius', 1000.0))
        self.magnet_strength = float(params.get('magnet_strength', 400.0))
        self.magnet_min_distance = float(params.get('magnet_min_distance', 48.0))

    def update(self, dt_ms, player=None, world_rect=None):
        # update animation frames from base
        super().update(dt_ms, player, world_rect)

        dt = dt_ms / 1000.0

        # If in simple bounce state, apply a damped oscillation (rubberband) to the bounce velocity
        if getattr(self, 'bouncing', False):
            try:
                # decrease timer
                self.bounce_timer -= dt
                # elapsed time since bounce start
                elapsed = float(self.bounce_duration) - max(0.0, float(self.bounce_timer))
                # normalized time in [0, bounce_duration]
                T = max(1e-6, float(self.bounce_duration))
                # oscillation frequency (rad/s)
                freq = float(getattr(self, 'bounce_oscillations', 2.0))
                omega = 2.0 * math.pi * (freq / T)
                # damping factor (controls exponential envelope)
                damping = float(getattr(self, 'bounce_damping', 2.2))
                envelope = math.exp(- (damping * elapsed) / T)
                # damped cosine oscillation (starts at 1.0 and oscillates)
                osc = math.cos(omega * elapsed)
                self.vel = pygame.Vector2(self.bounce_initial_vel) * (envelope * osc)
                # finish bounce when timer expired
                if self.bounce_timer <= 0.0:
                    self.bouncing = False
                    self.bounce_timer = 0.0
                    self.vel = pygame.Vector2(0, 0)
                # keep legacy vx/vy in sync for any animation code relying on them
                self.vx, self.vy = float(self.vel.x), float(self.vel.y)
            except Exception:
                pass

        # Figure-8 pathing: deterministic looping pattern that avoids wall-sticking
        if getattr(self, 'path_type', 'random') == 'figure8':
            # set path center once (prefer provided world bounds)
            if not self._pattern_center_set:
                try:
                    if world_rect is not None:
                        # ensure center is within world bounds with margin for amplitude
                        margin_x = int(self.pattern_A + 8)
                        margin_y = int(self.pattern_B + 8)
                        cx = max(world_rect.left + margin_x, min(self.pos.x, world_rect.right - margin_x))
                        cy = max(world_rect.top + margin_y, min(self.pos.y, world_rect.bottom - margin_y))
                        self.path_center = pygame.Vector2(cx, cy)
                    else:
                        self.path_center = pygame.Vector2(self.pos)
                except Exception:
                    self.path_center = pygame.Vector2(self.pos)
                self._pattern_center_set = True

            # advance pattern time and compute figure-8 (Lissajous-like) position
            self._pattern_time += dt
            A = self.pattern_A
            B = self.pattern_B
            period = max(0.001, self.pattern_period)
            omega = 2.0 * math.pi / period
            t = self._pattern_time
            x = self.path_center.x + A * math.sin(omega * t)
            y = self.path_center.y + B * math.sin(2.0 * omega * t)
            # derivative for velocity (dx/dt, dy/dt)
            dx = A * omega * math.cos(omega * t)
            dy = 2.0 * B * omega * math.cos(2.0 * omega * t)

            self.pos = pygame.Vector2(x, y)
            self.vel = pygame.Vector2(dx, dy)
            self.rect.center = (int(self.pos.x), int(self.pos.y))

            # exhaust animation update (reuse existing logic)
            speed_mag = self.vel.length()
            if speed_mag > 5.0:
                self._exhaust_timer += int(dt_ms)
                if self._exhaust_timer >= self.exhaust_speed_ms:
                    self._exhaust_timer -= self.exhaust_speed_ms
                    self.exhaust_index = (self.exhaust_index + 1) % max(1, len(getattr(self, 'exhaust_normal', []) or getattr(self, 'exhaust_turbo', [])))
            else:
                self.exhaust_index = 0

            # smoothly update facing based on instantaneous velocity
            if speed_mag > 0.001:
                target = math.atan2(-self.vel.y, self.vel.x)
                self._update_display_angle(dt_ms, target)

            return

        # apply gravity acceleration if enabled
        if self.gravity_enabled:
            dir_to_center = (pygame.Vector2(self.gravity_center) - self.pos)
            if dir_to_center.length_squared() > 0.0:
                acc = dir_to_center.normalize() * float(self.gravity_strength)
            else:
                acc = pygame.Vector2(0, 0)
            # integrate velocity
            self.vel += acc * dt

        # Magnetic attraction: gently steer towards player while avoiding overlap.
        if getattr(self, 'magnet_enabled', False) and player is not None:
            try:
                to_player = pygame.Vector2(player.rect.center) - self.pos
                dist = to_player.length()
                if dist > 0.0:
                    # within magnet radius -> attract with falloff
                    if dist < self.magnet_radius:
                        dirp = to_player.normalize()
                        strength = self.magnet_strength * max(0.0, (1.0 - dist / self.magnet_radius))
                        # apply as gentle acceleration
                        self.vel += dirp * (strength * dt)
                    # if too close, apply short-range repulsion to avoid collision
                    if dist < self.magnet_min_distance:
                        dirp = to_player.normalize()
                        repulse = -dirp * max(self.magnet_strength * 2.0, 160.0)
                        self.vel += repulse * dt
            except Exception:
                pass

        # apply turbo multiplier to movement (does not change vel permanently)
        mult = self.turbo_multiplier if self.turbo else 1.0
        move_vel = self.vel * mult
        # clamp speed
        if move_vel.length() > self.max_speed:
            move_vel.scale_to_length(self.max_speed)

        self.pos += move_vel * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))

        # advance exhaust animation when moving
        speed_mag = math.hypot(self.vx * mult, self.vy * mult)
        if speed_mag > 5.0:
            self._exhaust_timer += int(dt_ms)
            if self._exhaust_timer >= self.exhaust_speed_ms:
                self._exhaust_timer -= self.exhaust_speed_ms
                self.exhaust_index = (self.exhaust_index + 1) % max(1, len(getattr(self, 'exhaust_normal', []) or getattr(self, 'exhaust_turbo', [])))
        else:
            # reset to first frame when idle
            self.exhaust_index = 0

        if world_rect is not None:
            # robust wall-collision handling to avoid getting stuck
            collided_sides = []
            if self.rect.left <= world_rect.left:
                collided_sides.append('left')
            if self.rect.right >= world_rect.right:
                collided_sides.append('right')
            if self.rect.top <= world_rect.top:
                collided_sides.append('top')
            if self.rect.bottom >= world_rect.bottom:
                collided_sides.append('bottom')

            if collided_sides:
                # Compute penetration depth per side (positive values indicate overlap amount)
                overlap_left = max(0, world_rect.left - self.rect.left)
                overlap_right = max(0, self.rect.right - world_rect.right)
                overlap_top = max(0, world_rect.top - self.rect.top)
                overlap_bottom = max(0, self.rect.bottom - world_rect.bottom)

                # Choose dominant penetration to determine collision normal
                overlaps = {
                    'left': overlap_left,
                    'right': overlap_right,
                    'top': overlap_top,
                    'bottom': overlap_bottom,
                }
                side = max(overlaps, key=overlaps.get)
                pen = overlaps[side]
                if pen <= 0:
                    # fallback: compute summed normal
                    normal = pygame.Vector2(0, 0)
                    if 'left' in collided_sides:
                        normal += pygame.Vector2(1, 0)
                    if 'right' in collided_sides:
                        normal += pygame.Vector2(-1, 0)
                    if 'top' in collided_sides:
                        normal += pygame.Vector2(0, 1)
                    if 'bottom' in collided_sides:
                        normal += pygame.Vector2(0, -1)
                    if normal.length_squared() == 0:
                        normal = pygame.Vector2(1, 0)
                    normal = normal.normalize()
                    sep = 8
                else:
                    if side == 'left':
                        normal = pygame.Vector2(1, 0)
                    elif side == 'right':
                        normal = pygame.Vector2(-1, 0)
                    elif side == 'top':
                        normal = pygame.Vector2(0, 1)
                    else:
                        normal = pygame.Vector2(0, -1)
                    sep = pen + 1.0

                # Separate out of collision along normal. Push a bit extra to avoid
                # persistent contact when velocities are nearly tangent.
                try:
                    extra_push = max(4.0, min(32.0, pen * 0.5))
                    self.pos += normal * (sep + extra_push)
                except Exception:
                    pass
                self.rect.center = (int(self.pos.x), int(self.pos.y))

                # Simple short bounce: apply an outward impulse along the collision normal
                # (not merely reversing the possibly-tangential velocity) so the enemy
                # is reliably pushed away from the wall.
                if getattr(self, 'simple_bounce', True):
                    v = pygame.Vector2(self.vel)
                    # compute normal-aligned component of current velocity
                    v_norm_comp = v.dot(normal)
                    # ensure a meaningful outward speed: prefer a scaled normal component,
                    # but guarantee a minimum impulse based on enemy speed
                    base_min = float(self.speed) * 0.6
                    impulse_speed = max(abs(v_norm_comp) * float(getattr(self, 'bounce_strength', 1.8)), base_min, 120.0)
                    # initial impulse points outward along normal
                    self.bouncing = True
                    self.bounce_timer = float(self.bounce_duration)
                    self.bounce_initial_vel = normal * impulse_speed
                    # immediately apply initial bounce velocity and clamp
                    self.vel = pygame.Vector2(self.bounce_initial_vel)
                    if getattr(self, 'max_speed', None) and self.vel.length() > self.max_speed:
                        try:
                            self.vel.scale_to_length(self.max_speed)
                        except Exception:
                            pass
                    self.vx, self.vy = float(self.vel.x), float(self.vel.y)
                else:
                    # Physically based reflection: v' = v - (1 + e) (v·n) n
                    e = getattr(self, 'wall_restitution', 0.45)  # 0..1 (0 = inelastic, 1 = elastic)
                    mu = getattr(self, 'wall_friction', 0.28)    # tangential damping fraction
                    v = pygame.Vector2(self.vel)
                    vn = v.dot(normal)
                    v_normal = vn * normal
                    v_tangent = v - v_normal

                    # New normal component (reversed with restitution)
                    new_v_normal = - (1.0 + e) * v_normal
                    # Apply tangential friction (reduce tangential speed)
                    new_v_tangent = v_tangent * max(0.0, 1.0 - mu)

                    new_v = new_v_normal + new_v_tangent

                    # If new velocity is nearly zero, nudge along normal to avoid sticking
                    if new_v.length_squared() < 1.0:
                        new_v = normal * (self.speed * 0.6)

                    self.vel = new_v
                    # keep legacy vx/vy in sync
                    self.vx, self.vy = float(self.vel.x), float(self.vel.y)

            # ensure rect stays inside world
            self.rect.clamp_ip(world_rect)

        # keep legacy vx/vy in sync for rotation and external uses
        self.vx, self.vy = float(self.vel.x), float(self.vel.y)
        # update display angle smoothly towards current movement direction
        if abs(self.vel.x) > 0.001 or abs(self.vel.y) > 0.001:
            target = math.atan2(-self.vel.y, self.vel.x)
            self._update_display_angle(dt_ms, target)

        # periodic small random nudge so movement isn't perfectly linear
        if self.random_motion:
            self._change_timer += int(dt_ms)
            if self._change_timer >= self._change_interval:
                self._change_timer -= self._change_interval
                # apply small rotation and tiny speed variation
                self._apply_random_nudge()
                self._change_interval = random.randint(self._change_interval_min, self._change_interval_max)

    def _apply_random_nudge(self):
        angle = math.atan2(self.vel.y, self.vel.x)
        angle += random.uniform(-math.pi / 12, math.pi / 12)
        speed = self.vel.length() or self.speed
        speed *= random.uniform(0.9, 1.1)
        self.vel.x = math.cos(angle) * speed
        self.vel.y = math.sin(angle) * speed


class CircleEnemy(Enemy):
    """Simple, readable circular-motion enemy.

    - `angular_speed` is the base angular speed in radians/sec.
    - A behavior multiplier modifies that base speed (pause, slow, dash, reverse).
    - Position is computed directly from angle, so speed control is explicit.
    """
    def __init__(self, image, center_x, center_y, radius=160, angular_speed=2.0):
        super().__init__(image, center_x + radius, center_y)
        self.center = pygame.Vector2(center_x, center_y)
        self.radius = float(radius)
        # base angular speed (radians per second)
        self.base_angular_speed = float(angular_speed)
        # current angle around the circle
        self.angle = random.uniform(0.0, math.tau)

        # initial facing: tangent to the circle
        vx = -math.sin(self.angle) * self.base_angular_speed * self.radius
        vy = math.cos(self.angle) * self.base_angular_speed * self.radius
        self.display_angle = math.atan2(-vy, vx)

        # Physics / external push support
        self.mass = 1.0
        # push system: linear-decay push applied to position for short durations
        self._push_initial = pygame.Vector2(0, 0)
        self._push_elapsed = 0.0
        self._push_duration = 0.0

        # behavior state for simple, readable speed control
        self._behavior = 'normal'
        self._behavior_timer = 0.0
        self._behavior_duration = random.uniform(0.8, 2.5)
        # explicit multiplier applied to base_angular_speed
        self._speed_mult = 1.0

    def _choose_behavior(self):
        """Pick a simple behavior and set the speed multiplier."""
        r = random.random()
        if r < 0.10:
            self._behavior = 'pause'
            self._speed_mult = 0.0
        elif r < 0.30:
            self._behavior = 'reverse'
            self._speed_mult = -1.0
        elif r < 0.60:
            self._behavior = 'dash'
            # dash is a clear multiplicative increase
            self._speed_mult = random.uniform(0.8, 0.9)
        elif r < 0.85:
            self._behavior = 'slow'
            self._speed_mult = random.uniform(0.4, 0.8)
        else:
            self._behavior = 'normal'
            self._speed_mult = 1.0

    def update(self, dt_ms, player=None, world_rect=None):
        # keep base animation ticking
        super().update(dt_ms, player, world_rect)

        dt = dt_ms / 1000.0

        # behavior timer: pick a new behavior when time's up
        self._behavior_timer += dt
        if self._behavior_timer >= self._behavior_duration:
            self._behavior_timer = 0.0
            self._behavior_duration = random.uniform(0.6, 3.0)
            self._choose_behavior()

        # compute angular change explicitly using base speed and multiplier
        angular_speed = self.base_angular_speed * self._speed_mult
        self.angle += angular_speed * dt

        # keep angle in a reasonable range
        if self.angle > math.tau or self.angle < -math.tau:
            self.angle = self.angle % math.tau

        # update position from angle
        self.pos = pygame.Vector2(
            self.center.x + math.cos(self.angle) * self.radius,
            self.center.y + math.sin(self.angle) * self.radius,
        )
        self.rect.center = (int(self.pos.x), int(self.pos.y))

        # If an external short push is active, apply it as a position offset that decays linearly
        if self._push_duration > 0.0 and self._push_elapsed < self._push_duration:
            t = self._push_elapsed / max(1e-6, self._push_duration)
            # current push vector decays linearly from initial to zero
            current_push = self._push_initial * (1.0 - t)
            self.pos += current_push * dt
            self.rect.center = (int(self.pos.x), int(self.pos.y))
            self._push_elapsed += dt

        # update facing based on instantaneous tangent direction
        vx = -math.sin(self.angle) * angular_speed * self.radius
        vy = math.cos(self.angle) * angular_speed * self.radius
        if abs(vx) > 1e-6 or abs(vy) > 1e-6:
            target = math.atan2(-vy, vx)
            self._update_display_angle(dt_ms, target)

    def apply_push(self, impulse_vec: pygame.Vector2, duration: float = 0.5):
        """Apply a short-lived positional push to the circle enemy.

        The push decays linearly to zero over `duration` seconds. `impulse_vec` is
        interpreted as an initial velocity-like offset (px/s) applied to position.
        """
        try:
            self._push_initial = pygame.Vector2(impulse_vec)
            self._push_elapsed = 0.0
            self._push_duration = max(0.001, float(duration))
        except Exception:
            pass

    def draw(self, screen: pygame.Surface, camera_x: int, camera_y: int):
        # keep sprite visually upright (no rotation)
        r = self.image.get_rect(center=(self.rect.centerx - camera_x, self.rect.centery - camera_y))
        screen.blit(self.image, r.topleft)
