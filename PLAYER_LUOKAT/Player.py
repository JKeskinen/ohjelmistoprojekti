import pygame
import math
import os
from PLAYER_LUOKAT.PlayerAnimation import PlayerAnimation
from PLAYER_LUOKAT.PlayerWeapons import PlayerWeapons
from PLAYER_LUOKAT.PlayerInput import PlayerInput

# Collision sizing defaults for player sprite.
# Change these to tune player's collision circle relative to the sprite.
PLAYER_DEFAULT_COLLISION_FACTOR = 0.5  # fraction of max(width,height)
PLAYER_MIN_COLLISION_RADIUS = 2

class Player(pygame.sprite.Sprite):
    def __init__(self, scale_factor, frames, x, y, boost_frames=None):
        super().__init__()
        self.scale_factor = scale_factor
        self.input = PlayerInput()
        self.animation = PlayerAnimation(scale_factor)
        self.weapons = PlayerWeapons(scale_factor)
        self.attack_offset_distance = 3 # asetettu 0.5 scalefactorille RocketGame.py(scale_factor=0.5) 

        liike_frames = frames if frames else [pygame.Surface((32, 32), pygame.SRCALPHA)]
        scaled_move = self.animation.scale_frames(liike_frames)
        # idle: prefer a dedicated Idle frame set, otherwise use first frame of move
        idle_frames = [scaled_move[0]] if scaled_move else [pygame.Surface((32, 32), pygame.SRCALPHA)]
        self.animaatio = {
            'idle': idle_frames,
            'move': scaled_move,
            'boost': self.animation.scale_frames(boost_frames) if boost_frames else []
        }
        self.frame_index = 0
        self.current_anim = 'move'
        self.image = self.animaatio[self.current_anim][self.frame_index]
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = pygame.math.Vector2(x, y)
        # Default collision radius for the player (can be overridden externally)
        try:
            self.collision_radius = max(PLAYER_MIN_COLLISION_RADIUS, int(max(self.rect.width, self.rect.height) * PLAYER_DEFAULT_COLLISION_FACTOR))
        except Exception:
            self.collision_radius = PLAYER_MIN_COLLISION_RADIUS
        self.vel = pygame.math.Vector2(0, 0)
        self.angle = 0.0
        self.turn_speed = 180.0
        self.accel = 300.0
        self.max_speed = 400.0
        self.brake_decel = 500.0
        self.anim_timer = 0
        self.anim_speed = 100

        # Destroyed animation
        self.destroyed_sprites = self.animation.load_destroyed_sprites()
        self.destroyed_anim_timer = 0
        self.destroyed_anim_duration = 1200
        self.destroyed_anim_speed = 60
        self.is_destroyed = False
        self.destroyed_frame_index = 0

        # Attack animation
        self.attack_frames = []
        project_root = os.path.dirname(os.path.dirname(__file__))
        # Search for any ship folder under alukset/alus containing Attack_1
        attack_dir = None
        alukset_alus = os.path.join(project_root, 'alukset', 'alus')
        if os.path.isdir(alukset_alus):
            for candidate in sorted(os.listdir(alukset_alus)):
                cand_dir = os.path.join(alukset_alus, candidate, 'Attack_1')
                if os.path.isdir(cand_dir):
                    attack_dir = cand_dir
                    break
        if attack_dir:
            attack_paths = sorted([os.path.join(attack_dir, f) for f in os.listdir(attack_dir) if f.lower().endswith('.png')])
            for path in attack_paths:
                try:
                    img = pygame.image.load(path).convert_alpha()
                except Exception:
                    continue
                w = max(1, int(img.get_width() * self.scale_factor))
                h = max(1, int(img.get_height() * self.scale_factor))
                self.attack_frames.append(pygame.transform.scale(img, (w, h)))
        self.attack_frame_index = 0
        self.attack_anim_timer = 0
        self.attack_anim_speed = 80

        # Osuma-animaatio
        self.hit_anim_timer = 0
        self.hit_anim_duration = 200
        self.hit_flash_color = (255, 80, 80)
        # Hurt-flag: yksinkertainen boolean, joka kertoo, näytetäänkö
        # Damage/Hurt-overlay piirrossyklissä. Käytetään yhdessä
        # `hit_anim_timer`-ajastimen kanssa, jotta tila on helposti
        # tarkistettavissa muista moduuleista ja piirrosssa.
        self.hurt_flag = False
        # Hurt animation frame speed (milliseconds per hurt-frame)
        self.hurt_frame_speed = 40

        # Vahinko-animaatio
        self.damage_sprites = []
        self.damage_sprite_names = []
        # Search for any ship folder under alukset/alus containing Damage
        damage_dir = None
        alukset_alus = os.path.join(project_root, 'alukset', 'alus')
        if os.path.isdir(alukset_alus):
            for candidate in sorted(os.listdir(alukset_alus)):
                cand_dir = os.path.join(alukset_alus, candidate, 'Damage')
                if os.path.isdir(cand_dir):
                    damage_dir = cand_dir
                    break
        # Jos ei löytynyt tutkitaan myös alukset -kansion juuritasoa (esim. alukset/FIGHTER-SPRITES/Hurt)
        if not damage_dir:
            alukset_root = os.path.join(project_root, 'alukset')
            if os.path.isdir(alukset_root):
                for candidate in sorted(os.listdir(alukset_root)):
                    # etsi joko 'Damage' tai 'Hurt' alikansiosta
                    cand_dir = os.path.join(alukset_root, candidate, 'Damage')
                    cand_dir2 = os.path.join(alukset_root, candidate, 'Hurt')
                    if os.path.isdir(cand_dir):
                        damage_dir = cand_dir
                        break
                    if os.path.isdir(cand_dir2):
                        damage_dir = cand_dir2
                        break
        if damage_dir:
            damage_files = sorted([f for f in os.listdir(damage_dir) if f.lower().endswith('.png')])
            for fname in damage_files:
                path = os.path.join(damage_dir, fname)
                try:
                    img = pygame.image.load(path).convert_alpha()
                except Exception:
                    continue
                w = max(1, int(img.get_width() * self.scale_factor))
                h = max(1, int(img.get_height() * self.scale_factor))
                self.damage_sprites.append(pygame.transform.scale(img, (w, h)))
                self.damage_sprite_names.append(fname)


    def update(self, dt):
        self.input.update()
        self.update_destroyed_animation(dt)
        self.weapons.update(dt)
        self.update_hit_animation(dt)
        self.handle_attack_animation(dt)
        self.handle_animation(dt)
        self.handle_movement(dt)

    def update_destroyed_animation(self, dt):
        if self.is_destroyed:
            self.destroyed_anim_timer += dt
            frame_count = len(self.destroyed_sprites)
            if frame_count > 0:
                self.destroyed_frame_index = min(int(self.destroyed_anim_timer / self.destroyed_anim_speed), frame_count - 1)

    def update_hit_animation(self, dt):
        if self.hit_anim_timer > 0:
            self.hit_anim_timer -= dt
            if self.hit_anim_timer < 0:
                # Ajastin päättynyt -> sammuta hurt-flag myös
                self.hit_anim_timer = 0
                self.hurt_flag = False
        if self.input.hit:
            self.trigger_hit_animation()

    def handle_attack_animation(self, dt):
        if self.input.shoot:
            if self.attack_frames:
                self.attack_anim_timer += dt
                if self.attack_anim_timer >= self.attack_anim_speed:
                    self.attack_anim_timer -= self.attack_anim_speed
                    self.attack_frame_index = (self.attack_frame_index + 1) % len(self.attack_frames)
            self.weapons.shoot(self.pos, self.angle)
        else:
            self.attack_frame_index = 0
            self.attack_anim_timer = 0

    def handle_animation(self, dt):
        # Choose animation state: idle when not thrusting, move/fly when thrusting,
        # boost when thrusting and boost frames available.
        if self.input.moveUp:
            new_anim = 'boost' if self.animaatio.get('boost') else 'move'
        else:
            new_anim = 'idle'

        if new_anim != self.current_anim:
            self.current_anim = new_anim
            self.frame_index = 0
            self.anim_timer = 0
        frames = self.animaatio.get(self.current_anim, [])
        if frames:
            self.anim_timer += dt
            if self.anim_timer >= self.anim_speed:
                self.anim_timer -= self.anim_speed
                self.frame_index = (self.frame_index + 1) % len(frames)
            self.image = frames[self.frame_index]

    def handle_movement(self, dt):
        dt_s = dt / 1000.0
        if self.input.turnLeft:
            self.angle += self.turn_speed * dt_s
        if self.input.turnRight:
            self.angle -= self.turn_speed * dt_s
        if self.input.moveUp:
            # thrust direction: use same angle convention as drawing
            rad = math.radians(self.angle)
            thrust = pygame.math.Vector2(math.cos(rad), math.sin(rad)) * self.accel * dt_s
            self.vel += thrust
            if self.vel.length() > self.max_speed:
                self.vel.scale_to_length(self.max_speed)
        if self.input.moveDown:
            speed = self.vel.length()
            if speed > 0:
                dec = self.brake_decel * dt_s
                new_speed = max(0.0, speed - dec)
                if new_speed == 0:
                    self.vel = pygame.math.Vector2(0, 0)
                else:
                    self.vel.scale_to_length(new_speed)
        self.pos += self.vel * dt_s
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def move(self, dx, dy, world_w, world_h):
        self.rect.x += dx
        self.rect.y += dy
        self.pos.x = self.rect.centerx
        self.pos.y = self.rect.centery
        self.rect.x = max(0, min(self.rect.x, world_w - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, world_h - self.rect.height))
        self.pos.x = self.rect.centerx
        self.pos.y = self.rect.centery

    def draw(self, screen, cam_x, cam_y):
        if self.is_destroyed and self.destroyed_sprites:
            destroyed_sprite = self.destroyed_sprites[self.destroyed_frame_index]
            destroyed_rect = destroyed_sprite.get_rect(center=(self.rect.centerx - cam_x, self.rect.centery - cam_y))
            screen.blit(destroyed_sprite, destroyed_rect.topleft)
            return

        # Keskitetään piirto rectin mukaan (varmistaa yhdenmukaisen sijoittelun)
        base_center = (self.rect.centerx - cam_x, self.rect.centery - cam_y)

        # Piirrä vahinko/hurt -animaatio päälle, jos `hurt_flag` on asetettu.
        # Jos hurt-flag on päällä, älä piirrä alempaa (perus)spriteä.
        if self.hurt_flag and self.damage_sprites:
            frame_count = len(self.damage_sprites)
            if frame_count > 0:
                # compute elapsed time since hurt animation started
                elapsed = self.hit_anim_duration - self.hit_anim_timer
                idx = int(elapsed / max(1, self.hurt_frame_speed))
                idx = max(0, min(frame_count - 1, idx))
                damage_sprite = self.damage_sprites[idx]
                damage_rotated = pygame.transform.rotate(damage_sprite, -self.angle)
                dmg_rect = damage_rotated.get_rect(center=base_center)
                screen.blit(damage_rotated, dmg_rect.topleft)
        else:
            # Piirrä pelaajan sprite (vain jos ei hurt-overlayia)
            rotated = pygame.transform.rotate(self.image, -self.angle)
            rot_rect = rotated.get_rect(center=base_center)
            screen.blit(rotated, rot_rect.topleft)
        # Piirrä aseiden ammukset
        for bullet in self.weapons.bullets:
            screen.blit(bullet.image, (bullet.rect.x - cam_x, bullet.rect.y - cam_y))

        # Piirrä hyökkäysanimaatio
        if self.input.shoot and self.attack_frames:
            attack_sprite = self.attack_frames[self.attack_frame_index]
            attack_rotated = pygame.transform.rotate(attack_sprite, -self.angle)
            rad = math.radians(self.angle)
            offset_x = math.cos(rad) * self.attack_offset_distance
            offset_y = math.sin(rad) * self.attack_offset_distance
            attack_center = (base_center[0] + offset_x, base_center[1] + offset_y)
            attack_rect = attack_rotated.get_rect(center=attack_center)
            screen.blit(attack_rotated, attack_rect.topleft)

    def trigger_hit_animation(self):
        # Aseta ajastin ja merkkaa hurt-flag True, jolloin piirrossykli
        # näyttää Damage/Hurt-kehyksen välittömästi.
        self.hit_anim_timer = self.hit_anim_duration
        self.hurt_flag = True