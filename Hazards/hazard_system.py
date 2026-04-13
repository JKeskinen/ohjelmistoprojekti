import math
import random
from pathlib import Path

import pygame
from Audio import pelimusat


DEFAULT_HAZARD_CONFIG = {
    "enabled": True,
    "fuse_seconds": 3.0,
    "warning_seconds": 1.0,
    "bomb_radius": 150.0,
    "bomb_damage": 1,
    "chain_radius_scale": 0.65,
    "chain_damage_scale": 0.5,
    "meteor_spawn_rate": 1.8,
    "max_active_meteors": 9,
    "enemy_drop_chance": 0.25,
    "enemy_drop_cooldown": 0.75,
    "boss_drop_interval_min": 4.0,
    "boss_drop_interval_max": 6.0,
    "player_hit_cooldown": 0.9,
    "meteor_contact_damage": 1,
    "pickup_drop_chance": 0.33,
    "bomb_sprite_size": 76,
    "shockwave_max_radius_mult": 1.45,
    "shockwave_speed": 410.0,
    "shockwave_band": 42.0,
    "shockwave_push": 440.0,
    "bomb_family": "3",
    "boss_drop_initial_speed": 300.0,
    "boss_drop_lateral_speed": 95.0,
    "bomb_drop_phase_seconds": 0.75,
    "bomb_hover_drift": 26.0,
    "bomb_spin_speed_min": -85.0,
    "bomb_spin_speed_max": 85.0,
    "mine_trigger_radius": 180.0,
    "mine_auto_arm_seconds": 4.8,
    "mine_fuse_seconds": 1.6,
}


class HazardSpriteLibrary:
    """Loads and maps hazard sprites with safe fallbacks."""

    def __init__(self, base_dir: str, config=None):
        self.base_dir = Path(base_dir)
        self.config = config or {}
        self.mapping = {}
        self._fallback_cache = {}
        self._load_all()

    def _scale_to_square(self, image, size_px):
        size_px = max(18, int(size_px))
        return pygame.transform.smoothscale(image, (size_px, size_px))

    def _load_image(self, path: Path, fallback_size=(64, 64), fallback_color=(255, 180, 80, 220)):
        if path and path.exists():
            try:
                return pygame.image.load(str(path)).convert_alpha()
            except Exception:
                pass
        return self._fallback_surface(fallback_size, fallback_color)

    def _fallback_surface(self, size, color):
        key = (int(size[0]), int(size[1]), tuple(color))
        if key in self._fallback_cache:
            return self._fallback_cache[key]

        surface = pygame.Surface((int(size[0]), int(size[1])), pygame.SRCALPHA)
        rect = surface.get_rect()
        pygame.draw.ellipse(surface, color, rect)
        pygame.draw.ellipse(surface, (255, 255, 255, 180), rect.inflate(-rect.width * 0.35, -rect.height * 0.35))
        self._fallback_cache[key] = surface
        return surface

    def _glob_sorted(self, rel_glob: str):
        root = self.base_dir
        try:
            files = sorted(root.glob(rel_glob))
            return [p for p in files if p.suffix.lower() == ".png"]
        except Exception:
            return []

    def _pick_by_area(self, images):
        if not images:
            return {
                "small": self._fallback_surface((46, 46), (120, 170, 200, 220)),
                "medium": self._fallback_surface((64, 64), (110, 160, 180, 225)),
                "large": self._fallback_surface((92, 92), (95, 130, 150, 235)),
            }

        loaded = []
        for p in images:
            img = self._load_image(p)
            loaded.append((img.get_width() * img.get_height(), img))
        loaded.sort(key=lambda item: item[0])

        return {
            "small": loaded[0][1],
            "medium": loaded[len(loaded) // 2][1],
            "large": loaded[-1][1],
        }

    def _load_all(self):
        meteor_paths = self._glob_sorted("PNG/Meteors/*.png")
        meteors = self._pick_by_area(meteor_paths)

        # Load all available bomb families so game logic can choose different styles.
        preferred = str(self.config.get("bomb_family", "3")).strip() or "3"
        bomb_size = int(self.config.get("bomb_sprite_size", 76))
        bomb_sets = {}

        for family in ("1", "2", "3"):
            idle_paths = self._glob_sorted(f"PNG/Sprites/Bombs/Bomb_{family}_Idle_*.png")
            explosion_paths = self._glob_sorted(f"PNG/Sprites/Bombs/Bomb_{family}_Explosion_*.png")
            if not idle_paths or not explosion_paths:
                continue

            idle_frames = [self._load_image(p, (74, 74), (220, 90, 70, 230)) for p in idle_paths]
            idle_frames = [self._scale_to_square(img, bomb_size) for img in idle_frames]
            explosion_frames = [self._load_image(p, (110, 110), (255, 165, 70, 190)) for p in explosion_paths]
            bomb_sets[family] = {
                "idle": idle_frames,
                "warning": idle_frames,
                "explode": explosion_frames,
            }

        if not bomb_sets:
            fallback_idle = self._scale_to_square(
                self._fallback_surface((74, 74), (220, 90, 70, 230)),
                bomb_size,
            )
            fallback_explode = self._fallback_surface((110, 110), (255, 165, 70, 190))
            bomb_sets["fallback"] = {
                "idle": [fallback_idle],
                "warning": [fallback_idle],
                "explode": [fallback_explode],
            }

        default_family = preferred if preferred in bomb_sets else next(iter(bomb_sets.keys()))

        pickup_hp_path = self.base_dir / "PNG" / "Bonus_Items" / "HP_Bonus.png"
        pickup_barrier_path = self.base_dir / "PNG" / "Bonus_Items" / "Barrier_Bonus.png"
        pickup_hp = self._load_image(pickup_hp_path, (64, 64), (120, 255, 140, 210))
        pickup_shield = self._load_image(pickup_barrier_path, (64, 64), (120, 200, 255, 210))

        # Required explicit mapping keys.
        self.mapping = {
            "meteor_small": meteors["small"],
            "meteor_medium": meteors["medium"],
            "meteor_large": meteors["large"],
            "bomb_sets": bomb_sets,
            "bomb_idle": bomb_sets[default_family]["idle"],
            "bomb_warning": bomb_sets[default_family]["warning"],
            "bomb_explode": bomb_sets[default_family]["explode"],
            "pickup_hp": pickup_hp,
            "pickup_shield": pickup_shield,
            "bomb_family": default_family,
        }


class BombHazard:
    STATE_IDLE = "idle"
    STATE_ARMED = "armed"
    STATE_WARNING = "warning"
    STATE_EXPLODE = "explode"
    STATE_DONE = "done"

    def __init__(self, center, sprites: HazardSpriteLibrary, config, chain=False, velocity=(0, 0), drop_phase=False, family=None):
        self.pos = pygame.Vector2(center)
        self.sprites = sprites
        self.config = config
        bomb_sets = self.sprites.mapping.get("bomb_sets", {})
        requested_family = str(family).strip() if family is not None else str(self.sprites.mapping.get("bomb_family", "3"))
        if requested_family not in bomb_sets:
            requested_family = str(self.sprites.mapping.get("bomb_family", "3"))
        if requested_family not in bomb_sets and bomb_sets:
            requested_family = next(iter(bomb_sets.keys()))
        self.family = requested_family
        self._frames = bomb_sets.get(
            self.family,
            {
                "idle": self.sprites.mapping["bomb_idle"],
                "warning": self.sprites.mapping["bomb_warning"],
                "explode": self.sprites.mapping["bomb_explode"],
            },
        )
        self.is_proximity_mine = self.family == "2"
        self.state = self.STATE_IDLE
        self.timer = 0.0
        self.fuse_seconds = float(config["fuse_seconds"])
        self.warning_seconds = float(config["warning_seconds"])
        self.explode_seconds = 0.42
        self.mine_fuse_seconds = float(config.get("mine_fuse_seconds", 1.6))
        self.mine_auto_arm_seconds = float(config.get("mine_auto_arm_seconds", 4.8))
        self.mine_trigger_radius = float(config.get("mine_trigger_radius", 180.0))
        self.radius = float(config["bomb_radius"])
        self.damage = int(config["bomb_damage"])
        self._explosion_damage_pending = False
        self._player_damaged = False
        self._countdown_tick_second = None
        self.vel = pygame.Vector2(velocity)
        self.drop_phase = bool(drop_phase)
        self.drop_phase_seconds = float(config.get("bomb_drop_phase_seconds", 0.75))
        self.hover_drift = float(config.get("bomb_hover_drift", 26.0))
        self._hover_phase = random.uniform(0.0, math.tau)
        self._hover_time = 0.0
        self.angle = random.uniform(0.0, 360.0)
        self.spin = random.uniform(float(config.get("bomb_spin_speed_min", -85.0)), float(config.get("bomb_spin_speed_max", 85.0)))
        self._proximity_armed = False

        if chain:
            self.radius *= float(config["chain_radius_scale"])
            self.damage = max(1, int(round(self.damage * float(config["chain_damage_scale"]))))

        self.current_image = self._frames["idle"][0]
        self.rect = self.current_image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    @property
    def is_done(self):
        return self.state == self.STATE_DONE

    @property
    def is_exploding(self):
        return self.state == self.STATE_EXPLODE

    def early_detonate(self):
        if self.state in (self.STATE_IDLE, self.STATE_ARMED, self.STATE_WARNING):
            self.state = self.STATE_EXPLODE
            self.timer = 0.0
            self.radius *= float(self.config["chain_radius_scale"])
            self.damage = max(1, int(round(self.damage * float(self.config["chain_damage_scale"]))))
            self._explosion_damage_pending = True

    def _bomb_frame(self, dt_seconds, warning=False):
        frames = self._frames["warning" if warning else "idle"]
        speed = 20.0 if warning else 10.0
        idx = int(self.timer * speed) % max(1, len(frames))
        self.current_image = frames[idx]
        self.rect = self.current_image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def _update_motion(self, dt_seconds):
        self._hover_time += dt_seconds
        self.angle = (self.angle + self.spin * dt_seconds) % 360.0

        if self.drop_phase:
            self.pos += self.vel * dt_seconds
            self.vel *= 0.90
            self.timer += dt_seconds
            if self.timer >= self.drop_phase_seconds:
                self.drop_phase = False
                self.timer = 0.0
            return

        # Videogame-like floating drift after drop.
        wobble = math.sin(self._hover_phase + self._hover_time * 3.4)
        self.pos += self.vel * dt_seconds
        self.pos.y += wobble * (self.hover_drift * 0.06)
        self.vel *= 0.985

    def _arm_mine(self):
        if self._proximity_armed:
            return
        self._proximity_armed = True
        self.state = self.STATE_ARMED
        self.timer = 0.0
        self.fuse_seconds = min(self.fuse_seconds, self.mine_fuse_seconds)
        self.warning_seconds = min(self.warning_seconds, max(0.6, self.fuse_seconds * 0.55))

    def update(self, dt_seconds, proximity_positions=None):
        countdown_tick = None
        self._update_motion(dt_seconds)

        if self.drop_phase:
            self._bomb_frame(dt_seconds, warning=False)
            self.rect = self.current_image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
            return countdown_tick

        self.timer += dt_seconds

        if self.is_proximity_mine and self.state == self.STATE_IDLE:
            for p in proximity_positions or []:
                if (pygame.Vector2(p) - self.pos).length_squared() <= self.mine_trigger_radius * self.mine_trigger_radius:
                    self._arm_mine()
                    break

            if self.state == self.STATE_IDLE and self.timer >= self.mine_auto_arm_seconds:
                self._arm_mine()

        if (not self.is_proximity_mine) and self.state == self.STATE_IDLE and self.timer >= 0.15:
            self.state = self.STATE_ARMED
            self.timer = 0.0

        if self.state == self.STATE_IDLE:
            self._bomb_frame(dt_seconds, warning=False)

        elif self.state == self.STATE_ARMED:
            self._bomb_frame(dt_seconds, warning=False)
            remaining = self.fuse_seconds - self.timer
            if remaining <= self.warning_seconds:
                self.state = self.STATE_WARNING
                self.timer = max(0.0, self.fuse_seconds - self.warning_seconds)

        elif self.state == self.STATE_WARNING:
            self._bomb_frame(dt_seconds, warning=True)
            remaining = max(0.0, self.fuse_seconds - self.timer)
            this_second = int(math.ceil(remaining))
            if this_second > 0 and this_second != self._countdown_tick_second:
                self._countdown_tick_second = this_second
                countdown_tick = this_second
            if self.timer >= self.fuse_seconds:
                self.state = self.STATE_EXPLODE
                self.timer = 0.0
                self._explosion_damage_pending = True

        elif self.state == self.STATE_EXPLODE:
            frames = self._frames["explode"]
            idx = min(len(frames) - 1, int(self.timer * 30.0))
            self.current_image = frames[idx]
            self.rect = self.current_image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
            if self.timer >= self.explode_seconds:
                self.state = self.STATE_DONE

        self.rect = self.current_image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        return countdown_tick

    def consume_explosion_damage(self):
        if not self._explosion_damage_pending:
            return None
        self._explosion_damage_pending = False
        return {"center": self.pos, "radius": self.radius, "damage": self.damage}

    def can_damage_player(self):
        return self.is_exploding and not self._player_damaged

    def mark_player_damaged(self):
        self._player_damaged = True

    def draw(self, surface, camera_x, camera_y):
        rotated = pygame.transform.rotozoom(self.current_image, self.angle, 1.0)
        draw_rect = rotated.get_rect(center=(int(self.pos.x - camera_x), int(self.pos.y - camera_y)))
        surface.blit(rotated, draw_rect.topleft)

        center = (int(self.pos.x - camera_x), int(self.pos.y - camera_y))
        if self.is_proximity_mine and self.state == self.STATE_IDLE:
            pulse = 0.55 + 0.45 * abs(math.sin(self._hover_time * 2.8))
            trigger_preview = int(self.mine_trigger_radius * (0.15 + pulse * 0.08))
            pygame.draw.circle(surface, (90, 210, 255), center, trigger_preview, 1)
        elif self.state == self.STATE_WARNING:
            rem = max(0.0, self.fuse_seconds - self.timer)
            pulse = 0.55 + 0.45 * abs(math.sin((self.fuse_seconds - rem) * 11.0))
            preview_radius = int(self.radius * (0.5 + pulse * 0.35))
            pygame.draw.circle(surface, (255, 90, 70), center, preview_radius, 2)
            pygame.draw.circle(surface, (255, 170, 70), center, max(12, preview_radius // 2), 1)
        elif self.state == self.STATE_EXPLODE:
            ring = pygame.Surface((int(self.radius * 2 + 4), int(self.radius * 2 + 4)), pygame.SRCALPHA)
            pygame.draw.circle(
                ring,
                (255, 170, 70, 58),
                (ring.get_width() // 2, ring.get_height() // 2),
                int(self.radius),
            )
            surface.blit(ring, (int(center[0] - self.radius), int(center[1] - self.radius)))


class MeteorHazard:
    TIER_TO_KEY = {1: "meteor_small", 2: "meteor_medium", 3: "meteor_large"}

    def __init__(self, center, velocity, tier, sprites: HazardSpriteLibrary):
        self.pos = pygame.Vector2(center)
        self.vel = pygame.Vector2(velocity)
        self.tier = max(1, min(3, int(tier)))
        self.sprites = sprites
        self.image = self._scaled_image()
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        self.radius = max(14, int(max(self.rect.width, self.rect.height) * 0.38))
        self.hp = {3: 3, 2: 2, 1: 1}[self.tier]
        self.dead = False
        self.spin = random.uniform(-110.0, 110.0)
        self.angle = random.uniform(0.0, 360.0)

    def _scaled_image(self):
        base = self.sprites.mapping[self.TIER_TO_KEY[self.tier]]
        size_map = {1: 54, 2: 78, 3: 108}
        size = size_map[self.tier]
        return pygame.transform.smoothscale(base, (size, size))

    def update(self, dt_seconds, world_rect):
        self.pos += self.vel * dt_seconds
        self.angle = (self.angle + self.spin * dt_seconds) % 360.0

        # Meteors that fly beyond level bounds are removed (no edge bounce).
        margin = max(self.radius, 32)
        if (
            self.pos.x < world_rect.left - margin
            or self.pos.x > world_rect.right + margin
            or self.pos.y < world_rect.top - margin
            or self.pos.y > world_rect.bottom + margin
        ):
            self.dead = True

        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def take_hit(self, damage=1):
        self.hp -= int(damage)
        if self.hp <= 0:
            self.dead = True
            return True
        return False

    def split_children(self):
        if self.tier <= 1:
            return []
        children = []
        base_speed = max(90.0, self.vel.length() * 1.15)
        for sign in (-1, 1):
            dir_vec = pygame.Vector2(self.vel)
            if dir_vec.length_squared() <= 1e-6:
                dir_vec = pygame.Vector2(1, 0)
            dir_vec = dir_vec.normalize().rotate(40 * sign)
            child_vel = dir_vec * base_speed
            child = MeteorHazard(self.pos + dir_vec * (self.radius * 0.55), child_vel, self.tier - 1, self.sprites)
            children.append(child)
        return children

    def draw(self, surface, camera_x, camera_y):
        rotated = pygame.transform.rotozoom(self.image, self.angle, 1.0)
        r = rotated.get_rect(center=(int(self.pos.x - camera_x), int(self.pos.y - camera_y)))
        surface.blit(rotated, r.topleft)


class Pickup:
    def __init__(self, center, kind, image):
        self.pos = pygame.Vector2(center)
        self.kind = kind
        self.image = pygame.transform.smoothscale(image, (46, 46))
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        self.lifetime = 8.0
        self.dead = False

    def update(self, dt_seconds):
        self.lifetime -= dt_seconds
        if self.lifetime <= 0:
            self.dead = True

    def draw(self, surface, camera_x, camera_y):
        surface.blit(self.image, (int(self.rect.x - camera_x), int(self.rect.y - camera_y)))


class Shockwave:
    def __init__(self, center, max_radius, speed, band, strength):
        self.center = pygame.Vector2(center)
        self.max_radius = float(max_radius)
        self.speed = float(speed)
        self.band = float(band)
        self.strength = float(strength)
        self.radius = 0.0
        self.prev_radius = 0.0
        self.dead = False

    def update(self, dt_seconds):
        self.prev_radius = self.radius
        self.radius = min(self.max_radius, self.radius + self.speed * dt_seconds)
        if self.radius >= self.max_radius:
            self.dead = True

    def to_push_event(self):
        return {
            "center": (float(self.center.x), float(self.center.y)),
            "radius": float(self.radius),
            "prev_radius": float(self.prev_radius),
            "band": float(self.band),
            "strength": float(self.strength),
        }

    def draw(self, surface, camera_x, camera_y):
        if self.radius <= 1.0:
            return
        center = (int(self.center.x - camera_x), int(self.center.y - camera_y))
        alpha = max(20, int(125 * (1.0 - self.radius / max(1.0, self.max_radius))))
        ring = pygame.Surface((int(self.radius * 2 + self.band * 2 + 4), int(self.radius * 2 + self.band * 2 + 4)), pygame.SRCALPHA)
        c = (ring.get_width() // 2, ring.get_height() // 2)
        pygame.draw.circle(ring, (255, 215, 120, alpha), c, int(self.radius + self.band * 0.5), max(2, int(self.band * 0.35)))
        pygame.draw.circle(ring, (255, 130, 70, max(18, alpha - 30)), c, int(self.radius), 1)
        surface.blit(ring, (int(center[0] - ring.get_width() // 2), int(center[1] - ring.get_height() // 2)))


class HazardSystem:
    """Unified update/render/collision pipeline for meteors, bombs, and pickups."""

    def __init__(self, world_size, sprite_root, config=None):
        merged = dict(DEFAULT_HAZARD_CONFIG)
        if config:
            merged.update(config)
        self.config = merged
        self.enabled = bool(self.config.get("enabled", True))
        self.world_rect = pygame.Rect(0, 0, int(world_size[0]), int(world_size[1]))
        self.sprites = HazardSpriteLibrary(sprite_root, config=self.config)

        self.bombs = []
        self.meteors = []
        self.pickups = []
        self.shockwaves = []
        self.debug_countdown_tick = None
        self.debug_last_damage = 0

        self._meteor_spawn_timer = 0.0
        self._boss_drop_timer = random.uniform(
            float(self.config["boss_drop_interval_min"]),
            float(self.config["boss_drop_interval_max"]),
        )
        self._enemy_drop_cooldown = 0.0
        self._player_hazard_cooldown = 0.0

    def reset(self):
        self.bombs.clear()
        self.meteors.clear()
        self.pickups.clear()
        self.shockwaves.clear()
        self._meteor_spawn_timer = 0.0
        self._enemy_drop_cooldown = 0.0
        self._player_hazard_cooldown = 0.0
        self.debug_countdown_tick = None
        self.debug_last_damage = 0

    def _random_world_edge_spawn(self):
        side = random.choice(("top", "right", "bottom", "left"))
        if side == "top":
            return pygame.Vector2(random.uniform(0, self.world_rect.width), 0)
        if side == "bottom":
            return pygame.Vector2(random.uniform(0, self.world_rect.width), self.world_rect.height)
        if side == "left":
            return pygame.Vector2(0, random.uniform(0, self.world_rect.height))
        return pygame.Vector2(self.world_rect.width, random.uniform(0, self.world_rect.height))

    def spawn_meteor(self, tier=3, center=None, velocity=None):
        if center is None:
            center = self._random_world_edge_spawn()
        if velocity is None:
            toward_center = pygame.Vector2(self.world_rect.center) - pygame.Vector2(center)
            if toward_center.length_squared() < 1e-6:
                toward_center = pygame.Vector2(1, 0)
            velocity = toward_center.normalize() * random.uniform(110.0, 180.0)
            velocity.rotate_ip(random.uniform(-35.0, 35.0))
        meteor = MeteorHazard(center, velocity, tier, self.sprites)
        self.meteors.append(meteor)
        return meteor

    def spawn_bomb(self, center, chain=False):
        bomb = BombHazard(center, self.sprites, self.config, chain=chain)
        self.bombs.append(bomb)
        return bomb

    def spawn_boss_drop_bomb(self, center):
        vy = float(self.config.get("boss_drop_initial_speed", 300.0))
        vx = random.uniform(-float(self.config.get("boss_drop_lateral_speed", 95.0)), float(self.config.get("boss_drop_lateral_speed", 95.0)))
        bomb_sets = self.sprites.mapping.get("bomb_sets", {})
        boss_families = [f for f in ("2", "3") if f in bomb_sets]
        if not boss_families:
            boss_families = [f for f in bomb_sets.keys() if f != "fallback"]
        chosen_family = random.choice(boss_families) if boss_families else None
        bomb = BombHazard(
            center,
            self.sprites,
            self.config,
            chain=False,
            velocity=(vx, vy),
            drop_phase=True,
            family=chosen_family,
        )
        self.bombs.append(bomb)
        return bomb

    def on_enemy_destroyed(self, enemy, is_boss=False):
        if not self.enabled:
            return
        if self._enemy_drop_cooldown > 0.0:
            return

        chance = float(self.config["enemy_drop_chance"])
        if is_boss:
            chance = max(chance, 0.65)

        if random.random() <= chance:
            self.spawn_bomb(enemy.rect.center)
            self._enemy_drop_cooldown = float(self.config["enemy_drop_cooldown"])

    def _maybe_spawn_meteor(self, dt_seconds):
        self._meteor_spawn_timer += dt_seconds
        rate = max(0.1, float(self.config["meteor_spawn_rate"]))
        if self._meteor_spawn_timer < rate:
            return

        self._meteor_spawn_timer = 0.0
        if len(self.meteors) >= int(self.config["max_active_meteors"]):
            return

        tier = random.choices([3, 2, 1], weights=[0.45, 0.35, 0.20], k=1)[0]
        self.spawn_meteor(tier=tier)

    def _maybe_boss_drop(self, dt_seconds, boss_positions):
        if not boss_positions:
            return

        self._boss_drop_timer -= dt_seconds
        if self._boss_drop_timer > 0.0:
            return

        center = random.choice(boss_positions)
        offset = pygame.Vector2(random.uniform(-120, 120), random.uniform(75, 170))
        target = pygame.Vector2(center) + offset
        target.x = max(48, min(self.world_rect.width - 48, target.x))
        target.y = max(48, min(self.world_rect.height - 48, target.y))
        self.spawn_boss_drop_bomb(target)

        self._boss_drop_timer = random.uniform(
            float(self.config["boss_drop_interval_min"]),
            float(self.config["boss_drop_interval_max"]),
        )

    def _distance_sq_to_player(self, player, pos):
        p = pygame.Vector2(player.rect.center)
        return (p - pygame.Vector2(pos)).length_squared()

    def _coerce_positions(self, entries):
        positions = []
        for item in entries or []:
            if hasattr(item, "rect") and hasattr(item.rect, "center"):
                positions.append(item.rect.center)
                continue

            if isinstance(item, pygame.Vector2):
                positions.append((item.x, item.y))
                continue

            if isinstance(item, (tuple, list)) and len(item) >= 2:
                positions.append((item[0], item[1]))
        return positions

    def update(self, dt_ms, player, player_bullets, boss_positions=None, nearby_positions=None):
        if not self.enabled:
            return {
                "player_damage": 0,
                "pickup_hp": 0,
                "pickup_shield": 0,
                "countdown_tick": None,
                "meteor_destroyed_positions": [],
                "shockwaves": [],
            }

        dt_seconds = max(0.0, float(dt_ms) / 1000.0)
        self.debug_countdown_tick = None
        self.debug_last_damage = 0

        if self._enemy_drop_cooldown > 0.0:
            self._enemy_drop_cooldown = max(0.0, self._enemy_drop_cooldown - dt_seconds)
        if self._player_hazard_cooldown > 0.0:
            self._player_hazard_cooldown = max(0.0, self._player_hazard_cooldown - dt_seconds)

        self._maybe_spawn_meteor(dt_seconds)
        boss_pos_list = self._coerce_positions(boss_positions)
        self._maybe_boss_drop(dt_seconds, boss_pos_list)

        proximity_positions = [player.rect.center]
        proximity_positions.extend(boss_pos_list)
        proximity_positions.extend(self._coerce_positions(nearby_positions))
        proximity_positions.extend([m.rect.center for m in self.meteors])

        for bomb in self.bombs:
            tick = bomb.update(dt_seconds, proximity_positions=proximity_positions)
            if tick is not None:
                self.debug_countdown_tick = tick

        for meteor in self.meteors:
            meteor.update(dt_seconds, self.world_rect)
        self.meteors = [m for m in self.meteors if not m.dead]

        for pickup in self.pickups:
            pickup.update(dt_seconds)

        for wave in self.shockwaves:
            wave.update(dt_seconds)

        meteor_destroyed_positions = []

        # Bullet collisions with hazards.
        for bullet in list(player_bullets):
            removed = False

            for bomb in self.bombs:
                if bomb.state != BombHazard.STATE_DONE and bullet.rect.colliderect(bomb.rect):
                    try:
                        player_bullets.remove(bullet)
                    except ValueError:
                        pass
                    bomb.early_detonate()
                    removed = True
                    break
            if removed:
                continue

            for meteor in list(self.meteors):
                if bullet.rect.colliderect(meteor.rect):
                    try:
                        player_bullets.remove(bullet)
                    except ValueError:
                        pass

                    destroyed = meteor.take_hit(1)
                    if destroyed:
                        meteor_destroyed_positions.append((int(meteor.pos.x), int(meteor.pos.y)))
                        self.meteors.remove(meteor)
                        self.meteors.extend(meteor.split_children())

                        if random.random() <= float(self.config["pickup_drop_chance"]):
                            pickup_kind = random.choice(("hp", "shield"))
                            key = "pickup_hp" if pickup_kind == "hp" else "pickup_shield"
                            self.pickups.append(Pickup(meteor.pos, pickup_kind, self.sprites.mapping[key]))

                    removed = True
                    break
            if removed:
                continue

        effects = {
            "player_damage": 0,
            "pickup_hp": 0,
            "pickup_shield": 0,
            "countdown_tick": self.debug_countdown_tick,
            "meteor_destroyed_positions": meteor_destroyed_positions,
            "shockwaves": [],
        }

        # Player collisions with meteors.
        if self._player_hazard_cooldown <= 0.0:
            for meteor in list(self.meteors):
                if player.rect.colliderect(meteor.rect):
                    effects["player_damage"] += int(self.config["meteor_contact_damage"])
                    self._player_hazard_cooldown = float(self.config["player_hit_cooldown"])

                    # Collision shatters meteor into smaller chunks.
                    meteor_destroyed_positions.append((int(meteor.pos.x), int(meteor.pos.y)))
                    if meteor in self.meteors:
                        self.meteors.remove(meteor)
                    self.meteors.extend(meteor.split_children())
                    break

        # Bomb explosion damage region.
        player_radius = max(12, int(max(player.rect.width, player.rect.height) * 0.35))
        for bomb in self.bombs:
            damage_event = bomb.consume_explosion_damage()
            if damage_event is None:
                continue

            # TOISTA POMMIN RÄJÄHDYS-ÄÄNI
            if pelimusat.game_sounds:
                pelimusat.game_sounds.play_sfx("bomb_explosion")
        

            max_radius = float(damage_event["radius"]) * float(self.config["shockwave_max_radius_mult"])
            self.shockwaves.append(
                Shockwave(
                    center=damage_event["center"],
                    max_radius=max_radius,
                    speed=float(self.config["shockwave_speed"]),
                    band=float(self.config["shockwave_band"]),
                    strength=float(self.config["shockwave_push"]),
                )
            )

            if bomb.can_damage_player():
                dist_sq = self._distance_sq_to_player(player, damage_event["center"])
                max_r = damage_event["radius"] + player_radius
                if dist_sq <= max_r * max_r:
                    effects["player_damage"] += int(damage_event["damage"])
                    bomb.mark_player_damaged()

        # Pickup collect.
        for pickup in list(self.pickups):
            if pickup.rect.colliderect(player.rect):
                if pickup.kind == "hp":
                    effects["pickup_hp"] += 1
                elif pickup.kind == "shield":
                    effects["pickup_shield"] += 1
                pickup.dead = True

        self.bombs = [b for b in self.bombs if not b.is_done]
        self.pickups = [p for p in self.pickups if not p.dead]
        self.shockwaves = [w for w in self.shockwaves if not w.dead]

        effects["shockwaves"] = [w.to_push_event() for w in self.shockwaves]

        self.debug_last_damage = effects["player_damage"]
        return effects

    def draw(self, surface, camera_x, camera_y):
        for meteor in self.meteors:
            meteor.draw(surface, camera_x, camera_y)
        for bomb in self.bombs:
            bomb.draw(surface, camera_x, camera_y)
        for wave in self.shockwaves:
            wave.draw(surface, camera_x, camera_y)
        for pickup in self.pickups:
            pickup.draw(surface, camera_x, camera_y)

    def get_debug_lines(self):
        lines = [
            (
                f"Hazards bombs={len(self.bombs)} meteors={len(self.meteors)} "
                f"shockwaves={len(self.shockwaves)} pickups={len(self.pickups)}"
            ),
            (
                f"Hazard cfg fuse={self.config['fuse_seconds']:.1f}s radius={self.config['bomb_radius']:.0f} "
                f"spawn={self.config['meteor_spawn_rate']:.2f}s"
            ),
        ]
        if self.debug_countdown_tick is not None:
            lines.append(f"Bomb countdown tick: {self.debug_countdown_tick}")
        return lines
