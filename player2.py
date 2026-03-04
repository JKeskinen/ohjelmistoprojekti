import os
import pygame
import math
from PLAYER_LUOKAT.PlayerInput import PlayerInput
from PLAYER_LUOKAT.PlayerWeapons import PlayerWeapons

# Collision sizing defaults for player sprite.
# Tweak these to change how big the player's circular collision area is.
PLAYER2_DEFAULT_COLLISION_FACTOR = 0.2
PLAYER2_MIN_COLLISION_RADIUS = 8


class Player2(pygame.sprite.Sprite):
    """Pelaajaluokka, joka lataa spritet dynaamisesti aluksen nimen perusteella.

        Kansiorakenne tuettuna (esimerkkejä):
            - alukset/alus/<SHIP>/Move/*.png
            - alukset/alus/<SHIP>/Boost/*.png
            - alukset/alus/<SHIP>/Destroyed/*.png
            - images/<SHIP>_sprites/Fly1_*.png, Destroyed_*.png, Boost_*.png, Hurt_*.png, Shot1_*.png

        Parametrit:
            - ship_name: esim. 'Bomber' tai 'FIGHTER' (kansion nimi)
      - scale_factor: skaalauksen kerroin (kuten aiemmassa `Player`)
      - x,y: aloitussijainti
    """

    def __init__(self, ship_name, scale_factor, x, y, max_health: int = 5):
        super().__init__()
        self.ship_name = ship_name
        self.scale_factor = scale_factor
        self.input = PlayerInput()
        self.weapons = PlayerWeapons(scale_factor)

        self.attack_offset_distance = 3







        # löydä projektin juuri
        def find_project_root(start_path):
            d = os.path.dirname(os.path.abspath(start_path))
            while True:
                if os.path.isdir(os.path.join(d, 'alukset')):
                    return d
                parent = os.path.dirname(d)
                if parent == d:
                    return os.path.dirname(os.path.abspath(start_path))
                d = parent

        project_root = find_project_root(__file__)






        # helper: etsi ensimmäinen olemassa oleva kansio
        def first_exist(*paths):
            for p in paths:
                if p and os.path.isdir(p):
                    return p
            return None

        # Etsi laajemmin mahdollisia sprite-kansioita. Käytetään ensin
        # tyypillisiä polkuja, sitten etsitään `alukset`-kansiosta hakusanalla
        # löytyvää kansiota (esim. 'FIGHTER-SPRITES').
        candidates = [
            os.path.join(project_root, 'alukset', 'alus', ship_name),
            os.path.join(project_root, 'alukset', ship_name),
            os.path.join(project_root, 'alukset', f"{ship_name}-SPRITES"),
            os.path.join(project_root, 'alukset', f"{ship_name}_SPRITES"),
            os.path.join(os.path.dirname(__file__), 'images', f"{ship_name}_sprites"),
            os.path.join(os.path.dirname(__file__), 'images', ship_name),
        ]

        # etsi alukset-kansion alikansioita, jotka sisältävät ship_name-merkkijonon
        alukset_root = os.path.join(project_root, 'alukset')
        if os.path.isdir(alukset_root):
            for cand in sorted(os.listdir(alukset_root)):
                if ship_name.lower() in cand.lower():
                    candidates.append(os.path.join(alukset_root, cand))

        base_folder = first_exist(*candidates)







        # Latausapufunktio: etsii ensin alakansion (base_folder/subpath), jos sitä
        # ei ole, yrittää löytää tiedostoja base_folderista prefiksillä
        # (esim. 'Shot1_*.png' tai 'Destroyed_*.png'). Palauttaa listan
        # skaalatuista pygame.Surface-olioista.
        def load_frames_from(subpath, pattern_prefix=None, size_scale=1.0):
            frames = []
            if not base_folder:
                return frames

            # 1) tarkista alikansio (esim. base/Move)
            folder = os.path.join(base_folder, subpath)
            if os.path.isdir(folder):
                names = sorted([f for f in os.listdir(folder) if f.lower().endswith('.png')])
                for fname in names:
                    full = os.path.join(folder, fname)
                    img = pygame.image.load(full).convert_alpha()
                    w = max(1, int(img.get_width() * self.scale_factor * size_scale))
                    h = max(1, int(img.get_height() * self.scale_factor * size_scale))
                    frames.append(pygame.transform.scale(img, (w, h)))
                return frames

            # 2) jos alikansiota ei ole, etsi base_folderista tiedostoja, joiden
            # nimi alkaa subpath + '_' (esim. 'Destroyed_1.png' tai 'Shot1_1.png')
            candidates = []
            for fname in sorted(os.listdir(base_folder)):
                if not fname.lower().endswith('.png'):
                    continue
                low = fname.lower()
                prefix = subpath.lower()
                # salli vain muodot: 'prefix_number.png' ja 'prefix.png'
                if low.startswith(prefix + '_') or low == prefix + '.png':
                    candidates.append(fname)

            # jos löytyi tiedostoja, ladataan ne järjestyksessä
            if candidates:
                # yritä järjestää numeerisen indeksin mukaan jos mahdollista
                def sort_key(fn):
                    import re
                    mm = re.search(r"(\d+)", fn)
                    if mm:
                        return int(mm.group(1))
                    return fn

                for fname in sorted(candidates, key=sort_key):
                    full = os.path.join(base_folder, fname)
                    img = pygame.image.load(full).convert_alpha()
                    w = max(1, int(img.get_width() * self.scale_factor * size_scale))
                    h = max(1, int(img.get_height() * self.scale_factor * size_scale))
                    frames.append(pygame.transform.scale(img, (w, h)))

            return frames

        # Lataa liike/boost/fly/hurt/destroyed/shot-kehykset
        self.move_frames = load_frames_from('Move') or load_frames_from('Fly1') or []
        self.boost_frames = load_frames_from('Boost') or load_frames_from('Boost_1') or []
        # Fly1 (liike) voi olla erikseen nimetty
        if not self.move_frames:
            self.move_frames = load_frames_from('Fly1')

        # Idle frames: try 'Idle' folder first, otherwise use first move frame as idle
        self.idle_frames = load_frames_from('Idle') or []
        if not self.idle_frames and self.move_frames:
            # use single-frame idle from first move frame
            self.idle_frames = [self.move_frames[0]]

        self.hurt_frames = load_frames_from('Damage') or load_frames_from('Hurt')
        # Hurt animation frame speed (ms per frame). Increased default to slow it down.
        self.hurt_frame_speed = 120
        self.destroyed_frames = load_frames_from('Destroyed')

        # Shot - kehykset ja ammo-kuvat
        self.shot1_frames = load_frames_from('Shot1')

        # Yksinkertainen, deterministinen ammuskuvan lataus:
        # Tukee joko yksittäistä tiedostoa `Shot1_ammo.png` tai kansiota
        # `Shot1_ammo/` jonka sisällä voi olla useita PNG-kehyksiä.
        shot_folder = os.path.join(project_root, 'alukset', f"{ship_name}-SPRITES")

        # Shot1: ensin tarkista yksittäinen tiedosto, sitten kansio
        shot1_file = os.path.join(shot_folder, 'Shot1_ammo.png')
        shot1_dir = os.path.join(shot_folder, 'Shot1_ammo')
        chosen_img = None
        if os.path.isfile(shot1_file):
            chosen_img = shot1_file
        elif os.path.isdir(shot1_dir):
            # etsi ensimmäinen PNG kansiosta
            pngs = sorted([f for f in os.listdir(shot1_dir) if f.lower().endswith('.png')])
            if pngs:
                chosen_img = os.path.join(shot1_dir, pngs[0])

        if chosen_img:
            img = pygame.image.load(chosen_img).convert_alpha()
            w = max(1, int(img.get_width() * self.scale_factor))
            h = max(1, int(img.get_height() * self.scale_factor))
            self.shot1_ammo = pygame.transform.scale(img, (w, h))
        else:
            self.shot1_ammo = self.weapons.bullet_img

        # Shot2: vastaava logiikka
        self.shot2_frames = load_frames_from('Shot2')
        shot2_file = os.path.join(shot_folder, 'Shot2_ammo.png')
        shot2_dir = os.path.join(shot_folder, 'Shot2_ammo')
        chosen_img = None
        if os.path.isfile(shot2_file):
            chosen_img = shot2_file
        elif os.path.isdir(shot2_dir):
            pngs = sorted([f for f in os.listdir(shot2_dir) if f.lower().endswith('.png')])
            if pngs:
                chosen_img = os.path.join(shot2_dir, pngs[0])

        if chosen_img:
            img = pygame.image.load(chosen_img).convert_alpha()
            w = max(1, int(img.get_width() * self.scale_factor))
            h = max(1, int(img.get_height() * self.scale_factor))
            self.shot2_ammo = pygame.transform.scale(img, (w, h))
        else:
            self.shot2_ammo = self.weapons.bullet_img

        # Attack animations: disabled — käytetään suoraan Shot1/Shot2 -kehystä
        self.attack_frames = []

        # Debug helper: track last shot type used to reduce logging spam
        self._last_shot_type = None

        # Aseta alustuskuva ja anim-tila
        self.animaatio = {
            'idle': self.idle_frames or [pygame.Surface((32,32), pygame.SRCALPHA)],
            'move': self.move_frames or [pygame.Surface((32,32), pygame.SRCALPHA)],
            'boost': self.boost_frames or []
        }
        self.frame_index = 0
        self.current_anim = 'move'
        self.image = self.animaatio[self.current_anim][self.frame_index]
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(0, 0)
        self.angle = 0.0

        # Default collision radius (can be adjusted externally)
        try:
            self.collision_radius = max(PLAYER2_MIN_COLLISION_RADIUS, int(max(self.rect.width, self.rect.height) * PLAYER2_DEFAULT_COLLISION_FACTOR))
        except Exception:
            self.collision_radius = PLAYER2_MIN_COLLISION_RADIUS

        # animaatioajastimet
        self.anim_timer = 0
        self.anim_speed = 100

        # destroy/hurt tilat
        self.is_destroyed = False
        self.destroyed_anim_timer = 0
        self.destroyed_anim_speed = 60
        self.destroyed_frame_index = 0

        self.hit_anim_timer = 0
        self.hit_anim_duration = 200
        # Hurt-flag: näyttää Damage/Hurt-overlay kun True
        self.hurt_flag = False


        # Debug: näytä spriten ja rectin keskikohdat + offset (aseta False poistaaksesi)
        self.show_center_debug = False

        # attack frames (jos niitä ei löytynyt aiemmin, varmistetaan kentät)
        self.attack_frames = getattr(self, 'attack_frames', [])
        self.attack_frame_index = 0
        self.attack_anim_timer = 0
        self.attack_anim_speed = 80
        # Nykyinen valittu attack-kehysjoukko (päivittyy napin mukaan)
        self.current_attack_frames = list(self.attack_frames)

        # Älä ylikirjoita aseen oletuskuvaa globaalisti täällä.
        # Käytämme sen sijaan `shoot_with`-metodia valitsemaan oikean ammutyypin
        # napin painalluksen mukaan.

        # health
        self.max_health = int(max(1, max_health))
        self.health = int(self.max_health)

        # (No debug output) initialization complete





    def update(self, dt):
        self.input.update()
        self.update_destroyed_animation(dt)
        self.weapons.update(dt)
        self.update_hit_animation(dt)
        self.handle_attack_animation(dt)
        self.handle_animation(dt)
        self.handle_movement(dt)





    def update_destroyed_animation(self, dt):
        if self.is_destroyed and self.destroyed_frames:
            self.destroyed_anim_timer += dt
            frame_count = len(self.destroyed_frames)
            if frame_count > 0:
                self.destroyed_frame_index = min(int(self.destroyed_anim_timer / self.destroyed_anim_speed), frame_count - 1)





    def update_hit_animation(self, dt):
        # Decrease hit timer; ensure hurt_flag is cleared and animation
        # state is restored when the hit animation completes.
        if self.hit_anim_timer > 0:
            self.hit_anim_timer -= dt
            if self.hit_anim_timer <= 0:
                # timer expired: clear flag and restore appropriate anim
                self.hit_anim_timer = 0
                self.hurt_flag = False
                # Restore to idle/move/boost depending on current input
                if self.input.moveUp:
                    new_anim = 'boost' if self.animaatio.get('boost') else 'move'
                else:
                    new_anim = 'idle'
                self.current_anim = new_anim
                self.frame_index = 0
                self.anim_timer = 0
        else:
            # Safety: if timer is zero but flag somehow stayed True, clear it
            if getattr(self, 'hurt_flag', False):
                self.hurt_flag = False

        # Allow input-triggered hit animation to restart the timer/flag
        if self.input.hit:
            self.trigger_hit_animation()









    def handle_attack_animation(self, dt):
        # Tukee kahta ampumiskomentoa: P => normaali (Shot2), L => teho (Shot1)
        # Note: `PlayerInput`: shoot2 == P, shoot1 == L
        if self.input.shoot1 or self.input.shoot2:
            # Determine which preset would be used for this input (mapping):
            # input.shoot2 (P) -> preset 'Shot2'
            # input.shoot1 (L) -> preset 'Shot1'
            preset_used = None
            if self.input.shoot2:
                preset_used = 'Shot2'
            elif self.input.shoot1:
                preset_used = 'Shot1'

            # If the preset is on cooldown, suppress its attack frames and
            # do not call the shooting method; fall back to default.
            preset_on_cooldown = False
            try:
                preset_on_cooldown = (self.weapons.preset_timers.get(preset_used, 0) > 0)
            except Exception:
                preset_on_cooldown = False

            # Select appropriate attack frames for the pressed key (if not on cooldown)
            if self.input.shoot2 and (not preset_on_cooldown) and self.shot2_frames:
                self.current_attack_frames = list(self.shot2_frames)
            elif self.input.shoot1 and (not preset_on_cooldown) and self.shot1_frames:
                self.current_attack_frames = list(self.shot1_frames)
            else:
                self.current_attack_frames = list(self.attack_frames)

            if self.current_attack_frames:
                self.attack_anim_timer += dt
                if self.attack_anim_timer >= self.attack_anim_speed:
                    self.attack_anim_timer -= self.attack_anim_speed
                    self.attack_frame_index = (self.attack_frame_index + 1) % len(self.current_attack_frames)

                # track last shot type quietly
                self._last_shot_type = 'shot2' if self.input.shoot2 else ('shot1' if self.input.shoot1 else 'attack')

            # Choose ammo type by key and shoot if preset not on cooldown
            if self.input.shoot2:
                img = self.shot2_ammo
                if not self.weapons.preset_timers.get('Shot2', 0):
                    # P -> Shot2 (normi)
                    self.weapons.shoot_with(self.pos, self.angle, img, preset_kind='Shot2')
            elif self.input.shoot1:
                img = self.shot1_ammo
                if not self.weapons.preset_timers.get('Shot1', 0):
                    # L -> Shot1 (teho)
                    self.weapons.shoot_with(self.pos, self.angle, img, preset_kind='Shot1')
        else:
            # Palauta oletus attack-kehykset ja nollaa animaatio
            self.current_attack_frames = list(self.attack_frames)
            self.attack_frame_index = 0
            self.attack_anim_timer = 0
            self._last_shot_type = None

    def handle_animation(self, dt):
        # Jos ammutaan, käytä attack-kehyksiä (Shot1/Shot2) pääanimaationa
        if (self.input.shoot1 or self.input.shoot2) and self.current_attack_frames:
            frames = self.current_attack_frames
            frame_count = len(frames)
            if frame_count == 0:
                return
            self.anim_timer += dt
            if self.anim_timer >= self.anim_speed:
                self.anim_timer -= self.anim_speed
                # keep frame_index within valid range
                self.frame_index = (self.frame_index + 1) % frame_count
            # safe access
            idx = max(0, min(self.frame_index, frame_count - 1))
            try:
                self.image = frames[idx]
            except Exception:
                # fallback to first frame
                self.image = frames[0]
            return

        # choose idle vs move vs boost
        if self.input.moveUp:
            new_anim = 'boost' if self.animaatio.get('boost') else 'move'
        else:
            new_anim = 'idle'
        if new_anim != self.current_anim:
            self.current_anim = new_anim
            self.frame_index = 0
            self.anim_timer = 0
        frames = self.animaatio.get(self.current_anim, [])
        frame_count = len(frames)
        if frame_count:
            self.anim_timer += dt
            if self.anim_timer >= self.anim_speed:
                self.anim_timer -= self.anim_speed
                # ensure frame_index always valid even if frames list changes
                self.frame_index = (self.frame_index + 1) % frame_count
            # clamp and set image safely
            if 0 <= self.frame_index < frame_count:
                self.image = frames[self.frame_index]
            else:
                self.frame_index = 0
                self.image = frames[0]







    def handle_movement(self, dt):
        dt_s = dt / 1000.0
        if self.input.turnLeft:
            self.angle += 180.0 * dt_s
        if self.input.turnRight:
            self.angle -= 180.0 * dt_s
        if self.input.moveUp:
            rad = math.radians(self.angle)
            thrust = pygame.math.Vector2(math.cos(rad), math.sin(rad)) * 300.0 * dt_s
            self.vel += thrust
            if self.vel.length() > 400.0:
                self.vel.scale_to_length(400.0)
        if self.input.moveDown:
            speed = self.vel.length()
            if speed > 0:
                dec = 500.0 * dt_s
                new_speed = max(0.0, speed - dec)
                if new_speed == 0:
                    self.vel = pygame.math.Vector2(0, 0)
                else:
                    self.vel.scale_to_length(new_speed)
        self.pos += self.vel * dt_s
        self.rect.center = (int(self.pos.x), int(self.pos.y))










    def move(self, dx, dy, world_w, world_h):
        """Siirtometodi, yhteensopiva vanhan `Player.move`-metodin kanssa.

        Joissain pelin osissa kutsutaan suoraan `player.move(dx,dy,world_w,world_h)`
        (esim. kamera- tai testioperaatioissa). Tämän metodin lisäys varmistaa,
        että `Player2` on täysin korvattavissa vanhan `Player`-luokan paikalla.

        - dx, dy: siirto pikseleinä
        - world_w, world_h: maailman leveys ja korkeus, joilla estetään siirtymä
                           pelialueen ulkopuolelle.
        """

        # siirretään rect-koordinaatteja
        self.rect.x += dx
        self.rect.y += dy
        # synkataan pos-vektori rectin keskipisteeseen
        self.pos.x = self.rect.centerx
        self.pos.y = self.rect.centery
        # rajoitetaan rectia niin, ettei se ylitä annettua maailmaa
        self.rect.x = max(0, min(self.rect.x, world_w - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, world_h - self.rect.height))
        # synkataan pos uudelleen rajoituksen jälkeen
        self.pos.x = self.rect.centerx
        self.pos.y = self.rect.centery

    def draw(self, screen, cam_x, cam_y):
        if self.is_destroyed and self.destroyed_frames:
            destroyed_sprite = self.destroyed_frames[self.destroyed_frame_index]
            destroyed_rect = destroyed_sprite.get_rect(center=(self.pos.x - cam_x, self.pos.y - cam_y))
            screen.blit(destroyed_sprite, destroyed_rect.topleft)
            return

        # Keskitys rectin mukaan
        base_center = (self.rect.centerx - cam_x, self.rect.centery - cam_y)

        # Debug: tulosta rectin top-left ja keskikohta sekä idle/fly sprite-keskikohdat
        if getattr(self, 'show_center_debug', False):
            # Raw rect coordinates relative to origin (0,0)
            rect_topleft = (self.rect.x, self.rect.y)
            rect_center = (self.rect.centerx, self.rect.centery)

            # Idle first-frame center when placed at rect_center
            idle_center = None
            if self.animaatio.get('idle'):
                idle_img = self.animaatio['idle'][0]
                idle_rect = idle_img.get_rect(center=rect_center)
                idle_center = idle_rect.center

            # Fly/move first-frame center when placed at rect_center
            fly_center = None
            move_frames = self.animaatio.get('move') or self.move_frames
            if move_frames:
                fly_img = move_frames[0]
                fly_rect = fly_img.get_rect(center=rect_center)
                fly_center = fly_rect.center

            # Offsets: sprite_center - rect_center
            def offset(a, b):
                if a is None or b is None:
                    return None
                return (a[0] - b[0], a[1] - b[1])

            idle_offset = offset(idle_center, rect_center)
            fly_offset = offset(fly_center, rect_center)

            print(f"[SPRITE DEBUG] rect={rect_topleft} rect_center={rect_center} | idle_center={idle_center} idle_offset={idle_offset} | fly_center={fly_center} fly_offset={fly_offset}")

        # Jos hurt-flag on päällä, piirretään vain hurt-frame overlay
        if getattr(self, 'hurt_flag', False) and getattr(self, 'hurt_frames', None):
            frames = self.hurt_frames
            if frames:
                frame_count = len(frames)
                if frame_count > 0:
                    elapsed = self.hit_anim_duration - self.hit_anim_timer
                    idx = int(elapsed / max(1, getattr(self, 'hurt_frame_speed', 40)))
                    idx = max(0, min(frame_count - 1, idx))
                    dmg = frames[idx]
                    dmg_rot = pygame.transform.rotate(dmg, -self.angle)
                    dmg_rect = dmg_rot.get_rect(center=base_center)
                    screen.blit(dmg_rot, dmg_rect.topleft)
        else:
            rotated = pygame.transform.rotate(self.image, -self.angle)
            rot_rect = rotated.get_rect(center=base_center)
            screen.blit(rotated, rot_rect.topleft)

        for bullet in self.weapons.bullets:
            screen.blit(bullet.image, (bullet.rect.x - cam_x, bullet.rect.y - cam_y))

        # attack overlay removed — attack frames are now applied to `self.image`
    def trigger_hit_animation(self):
        # Start/restart hit animation and remember current anim state.
        # Compute duration from hurt frames if available so the animation
        # timing scales with number of frames and the configured frame speed.
        total_duration = getattr(self, 'hit_anim_duration', 200)
        if getattr(self, 'hurt_frames', None):
            try:
                total_duration = len(self.hurt_frames) * int(self.hurt_frame_speed)
            except Exception:
                total_duration = getattr(self, 'hit_anim_duration', 200)
        self.hit_anim_duration = total_duration
        self.hit_anim_timer = total_duration
        self.hurt_flag = True
        # Save the current animation state so it can be restored if needed
        self._saved_anim = getattr(self, 'current_anim', 'move')
        self._saved_frame_index = getattr(self, 'frame_index', 0)
        self._saved_anim_timer = getattr(self, 'anim_timer', 0)
