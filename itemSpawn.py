"""
================================================================================
                    ITEMSPAWN - ITEMIEN SPAWNAUS-JÄRJESTELMÄ
================================================================================
KUVAUS:
    HALLITSEE KAIKKIEN ITEMIEN SPAWNAAMISTA VIHOLLISTEN JA BOSSIEN KUOLEMASTA.
    HEALTH, ARMOR, DAMAGE, SPEED BOOST JA NUKE.

PÄÄLUOKAT:
    - ItemSpawner : ITEMIEN HALLINTA JA SPAWNAUS
    - Item        : YKSITTÄINEN ITEM-SPRITE ANIMAATIOLLA

================================================================================
"""

import os
import random
import pygame
import math


class ItemSpawner:
    """
    ITEMSPAWNER - HALLITSEE KAIKKIEN ITEMIEN SPAWNAAMISEN PELISSA.
    VASTAA ITEMIEN LUOMISESTA, KERÄÄMISESTÄ JA ANIMAATIOISTA.
    """

    # ========================================================================
    # ITEMIEN TYYPIT - MITKÄ BONUKSET PELAAJA VOI SAADA
    # ========================================================================
    # Item types
    ITEM_HEALTH = "health"                  # +2 health (single health item type)
    ITEM_ARMOR = "armor_bonus"              # +1 armor
    ITEM_DAMAGE = "damage_bonus"            # +1 damage
    ITEM_SPEED_DEBUFF = "enemy_speed_debuff"  # Enemy slow (10 sec)
    ITEM_SHIELD = "shield_bonus"            # +1 shield
    ITEM_SPEED_BOOST = "speed_boost"        # +25% movement speed (10 sec)
    ITEM_ENEMY_DESTROY = "enemy_destroy"    # Destroy all enemies (nuke)

    # ========================================================================
    # SPRITE-POLUT - MISTÄ LÖYTYVÄT ITEMIEN KUVAT
    # ========================================================================
    # Sprite paths (relative to game folder)
    SPRITE_PATHS = {
        ITEM_ARMOR: "images/Space-Shooter_objects/PNG/Bonus_Items/Armor_Bonus.png",
        ITEM_DAMAGE: "images/Space-Shooter_objects/PNG/Bonus_Items/Damage_Bonus.png",
        ITEM_SPEED_DEBUFF: "images/Space-Shooter_objects/PNG/Bonus_Items/Enemy_Speed_Debuff.png",
        ITEM_HEALTH: "images/Space-Shooter_objects/PNG/Bonus_Items/HP_Bonus.png",
        ITEM_SHIELD: "images/Space-Shooter_objects/PNG/Bonus_Items/Barrier_Bonus.png",
        ITEM_SPEED_BOOST: "images/Space-Shooter_objects/PNG/Bonus_Items/Rockets_Bonus.png",
        ITEM_ENEMY_DESTROY: "images/Space-Shooter_objects/PNG/Bonus_Items/Enemy_Destroy_Bonus.png",
    }

    # ========================================================================
    # OLETUSKONFIGURAATIO - ITEM-SPAWN ASETUKSET
    # ========================================================================
    # Default spawn configuration
    DEFAULT_CONFIG = {
        "enemy_drop_chance": 0.70,           # 70% DROPRATE
        "enemy_drop_cooldown": 0.8,          # DROP COODOWN
        "boss_drop_interval_min": 3.0,       # BOSS DROP
        "boss_drop_interval_max": 5.0,
        "item_fall_speed": 150.0,            # PUTOAMISNOPEUS PIKSELIÄ/SEKUNTI
        "item_spin_speed": 180.0,            # SPIN NOPEUS ASTEITA/SEKUNTI
        "item_collection_radius": 50.0,      # POIMINTARADIUS
    }

    # ========================================================================
    # DROP-TODENNÄKÖISYYDET - MINKÄ TODENNÄKÖISYYDELLÄ MITÄKIN ITEMIÄ PUTOAA
    # ========================================================================
    # Drop type probabilities (when item drops, which type)
    DROP_PROBABILITIES = {
        ITEM_ARMOR: 0.55,              # 55% - Armor bonus (common)
        ITEM_HEALTH: 0.20,             # 20% - Health (+2)
        ITEM_DAMAGE: 0.15,             # 15% - Damage bonus (strong attacks)
        ITEM_SHIELD: 0.03,             # 3% - Shield bonus
        ITEM_SPEED_BOOST: 0.03,        # 3% - Speed boost
        ITEM_SPEED_DEBUFF: 0.02,       # 2% - Enemy speed debuff
        ITEM_ENEMY_DESTROY: 0.02,      # 2% - Destroy all enemies (nuke)
    }

    # ========================================================================
    # ITEM-ARVOT - KUINKA PALJON BONUSTA KUKIN ITEM ANTAA
    # ========================================================================
    # Item values/effects
    ITEM_VALUES = {
        ITEM_HEALTH: 2,             # +2 HEALTH POINTS
        ITEM_ARMOR: 1,              # +1 ARMOR POINTS
        ITEM_DAMAGE: 1,             # +1 DMG
        ITEM_SPEED_DEBUFF: 10.0,    # 10 SEKUNTIA DEBUFF ENEMYLLE
        ITEM_SHIELD: 2,             # +2 ARMOR PISTEET
        ITEM_SPEED_BOOST: 10.0,     # 10 SEKUNTIA NOPEUSBOOSTIA
        ITEM_ENEMY_DESTROY: 1,      # 1 = TRIGGERÖI NUKEN. TUHOAA VIHOLLISET, MUTTA EI BOSSIA
    }

    # ========================================================================
    # ITEMIEN VÄRIT - MIKÄ VÄRI JOKAISELLE ITEMILLE (JOS SPRIITEJA EI LÖYDY)
    # ========================================================================
    # Item colors and sizes (fallback for items without sprites)
    ITEM_COLORS = {
        ITEM_HEALTH: (255, 0, 0),           # Bright red
        ITEM_ARMOR: (100, 150, 200),        # Blue-gray
        ITEM_DAMAGE: (255, 150, 0),         # Orange
        ITEM_SPEED_DEBUFF: (150, 100, 255), # Purple
        ITEM_SHIELD: (100, 200, 255),       # Cyan
        ITEM_SPEED_BOOST: (0, 255, 150),    # Turquoise
        ITEM_ENEMY_DESTROY: (255, 0, 0),    # Red nuke
    }

    # ========================================================================
    # ITEMIEN KOOT - KUINKA ISOJA ITEMIEN SPRIITIT NÄYTTÄVÄT
    # ========================================================================
    ITEM_SIZES = {
        ITEM_HEALTH: 28,
        ITEM_ARMOR: 28,
        ITEM_DAMAGE: 28,
        ITEM_SPEED_DEBUFF: 24,
        ITEM_SHIELD: 28,
        ITEM_SPEED_BOOST: 32,
        ITEM_ENEMY_DESTROY: 36,
    }

    def __init__(self, config=None, sprite_root=None):
        """
        ALUSTAA ITEMSPAWNERIN KONFIGURAATIOLLA.
        
        PARAMETRIT:
            config      : SANAKIRJA KONFIKURAATIOIDEN YLIKIRJOITUS
            sprite_root : SPRITE-POLKU (VALINNAINEN)
        """
        self.config = {**self.DEFAULT_CONFIG}
        if config:
            self.config.update(config)

        self.sprite_root = sprite_root
        self.item_sprites = {}  # Cache for loaded item sprites
        self.items = []         # Active items on screen (Item instances)

        # Drop timers per item type
        self.last_enemy_drop_time = {}  # Tracks cooldown per drop opportunity
        self.boss_drop_timers = {}      # Tracks boss drop interval

        # Lataa bonus item spritit
        self._load_bonus_sprites()

    def _load_sprites(self):
        """LATAA ITEMIEN SPRITEET LEVYLTÄ (VALINNAINEN)."""
        if not self.sprite_root or not os.path.isdir(self.sprite_root):
            return  # Skip if no sprite root

        for item_type in self.ITEM_COLORS.keys():
            item_dir = os.path.join(self.sprite_root, item_type)
            if os.path.isdir(item_dir):
                pngs = sorted([f for f in os.listdir(item_dir) if f.lower().endswith('.png')])
                if pngs:
                    frames = []
                    for png in pngs:
                        try:
                            img = pygame.image.load(os.path.join(item_dir, png)).convert_alpha()
                            frames.append(img)
                        except Exception:
                            pass
                    if frames:
                        self.item_sprites[item_type] = frames

    def _load_bonus_sprites(self):
        """LATAA BONUS-ITEMIEN SPRITEET PNG-TIEDOSTOISTA."""
        loaded_count = 0
        for item_type, sprite_path in self.SPRITE_PATHS.items():
            if os.path.isfile(sprite_path):
                try:
                    img = pygame.image.load(sprite_path)
                    # Try to convert_alpha if display is initialized, otherwise use as-is
                    try:
                        img = img.convert_alpha()
                    except Exception:
                        pass  # Display not initialized yet, will use raw image
                    
                    # Scale to reasonable size (max 64px)
                    if img.get_width() > 64 or img.get_height() > 64:
                        scale = min(64 / img.get_width(), 64 / img.get_height())
                        new_size = (int(img.get_width() * scale), int(img.get_height() * scale))
                        img = pygame.transform.scale(img, new_size)
                    self.item_sprites[item_type] = [img]  # Wrap in list for consistency
                    loaded_count += 1
                except Exception as e:
                    print(f"[itemSpawn] Failed to load sprite {sprite_path}: {e}")
        print(f"[itemSpawn] Loaded {loaded_count} item sprites")
    
    def optimize_sprites_for_display(self):
        """OPTIMOI SPRITEET NÄYTÖLLE CONVERT_ALPHA:LLA SUORITUSKYVYN VUOKSI."""
        for item_type, frames in self.item_sprites.items():
            try:
                self.item_sprites[item_type] = [f.convert_alpha() if not hasattr(f, '_has_converted_alpha') else f for f in frames]
                for frame in self.item_sprites[item_type]:
                    frame._has_converted_alpha = True
            except Exception:
                pass  # Already converted or display issue

    def spawn_item_from_enemy(self, enemy_pos, item_type=None):
        """
        SPAWNAAA ITEMIN VIHOLLISEN KUOLEMISTAPAHTUMASTA.
        
        PARAMETRIT:
            enemy_pos : VIHOLLISEN (X, Y) SIJAINTI
            item_type : PAKOTETTU ITEM-TYYPPI TAI None SATUNNAISELLE
        
        PALAUTTAA:
            Item-objekti tai None
        """
        if item_type is None:
            # Random based on probabilities
            rand = random.random()
            cumulative = 0.0
            for itype, prob in self.DROP_PROBABILITIES.items():
                cumulative += prob
                if rand <= cumulative:
                    item_type = itype
                    break
            else:
                item_type = self.ITEM_HEALTH

        item = Item(
            pos=enemy_pos,
            item_type=item_type,
            sprites=self.item_sprites.get(item_type),
            color=self.ITEM_COLORS[item_type],
            size=self.ITEM_SIZES[item_type],
        )
        self.items.append(item)
        return item

    def spawn_item_from_boss(self, boss_pos, item_type=None):
        """
        SPAWNAAA ITEMIN BOSSIN KUOLEMISTAPAHTUMASTA (YLEENSÄ KORKEAMMAN TASON).
        
        PARAMETRIT:
            boss_pos  : BOSSIN (X, Y) SIJAINTI
            item_type : PAKOTETTU TYYPPI TAI None BOSSIN SATUNNAISELLE
        
        PALAUTTAA:
            Item-objekti tai None
        """
        if item_type is None:
            # Boss prefers larger health items
            rand = random.random()
            if rand < 0.60:
                item_type = self.ITEM_HEALTH_LARGE
            elif rand < 0.85:
                item_type = self.ITEM_HEALTH_MEDIUM
            elif rand < 0.95:
                item_type = self.ITEM_WEAPON_BOOST
            else:
                item_type = self.ITEM_SCORE_MULT

        return self.spawn_item_from_enemy(boss_pos, item_type)

    def should_enemy_drop(self, drop_chance=None):
        """
        TARKISTAA PITÄISIKÖ VIHOLLINEN DROPATA ITEMIÄ TODENNÄKÖISYYDEN MUKAAN.
        
        PARAMETRIT:
            drop_chance : YLIKIRJOITUS TODENNÄKÖISYYDELLE (0.0-1.0) TAI None
        
        PALAUTTAA:
            bool : True JOS PITÄISI DROPATA
        """
        if drop_chance is None:
            drop_chance = self.config["enemy_drop_chance"]
        return random.random() < drop_chance

    def should_boss_drop(self, boss_id, current_time):
        """
        TARKISTAA PITÄISIKÖ BOSSI DROPATA ITEMIÄ AJASTIMEN MUKAAN.
        
        PARAMETRIT:
            boss_id      : BOSSIN YKSITTÄINEN TUNNISTE
            current_time : NYKYINEN PELIAIKA (SEKUNNIT)
        
        PALAUTTAA:
            bool : True JOS PITÄISI DROPATA NYT
        """
        if boss_id not in self.boss_drop_timers:
            # Initialize new boss timer
            interval = random.uniform(
                self.config["boss_drop_interval_min"],
                self.config["boss_drop_interval_max"],
            )
            self.boss_drop_timers[boss_id] = current_time + interval
            return False

        if current_time >= self.boss_drop_timers[boss_id]:
            # Time to drop! Reset timer
            interval = random.uniform(
                self.config["boss_drop_interval_min"],
                self.config["boss_drop_interval_max"],
            )
            self.boss_drop_timers[boss_id] = current_time + interval
            return True

        return False

    def remove_boss_timer(self, boss_id):
        """POISTA BOSSIN AJASTIN KUN BOSSI ON KUKISTETTU."""
        if boss_id in self.boss_drop_timers:
            del self.boss_drop_timers[boss_id]

    def update(self, dt, player_rect=None, apply_collection=True):
        """
        PÄIVITTÄÄ KAIKKI AKTIIVISET ITEMIT JA TARKISTAA KERÄÄMISEN.
        
        PARAMETRIT:
            dt               : DELTA-AIKA (MILLISEKUNNIT)
            player_rect      : PYGAME.RECT PELAAJALLE
            apply_collection : JOS True, KERÄÄ ITEMIT LÄHELLÄ PELAAJAA
            
        PALAUTTAA:
            Lista kerityistä itemeista muodossa (item_type, value)
        """
        dt_s = dt / 1000.0
        collected_items = []

        # Update items
        for item in self.items[:]:
            item.update(dt_s)

            # Check collection
            if apply_collection and player_rect:
                if self._should_collect(item, player_rect):
                    item_value = self.get_item_value(item.item_type)
                    collected_items.append((item.item_type, item_value))
                    self.items.remove(item)
                    continue

            # Remove if out of bounds or too old
            if item.lifetime > 30.0:  # 30 second lifetime max
                self.items.remove(item)
        
        return collected_items

    def _should_collect(self, item, player_rect):
        """TARKISTAA PITÄISIKÖ TÄMÄ ITEM KERÄTÄ PELAAJALLA ETÄISYYDEN MUKAAN."""
        collect_radius = self.config["item_collection_radius"]
        dist = math.sqrt(
            (item.pos[0] - player_rect.centerx) ** 2 +
            (item.pos[1] - player_rect.centery) ** 2
        )
        return dist < collect_radius

    def get_item_value(self, item_type):
        """PALAUTTAA ITEMIN NUMEERISEN ARVON TAI EFEKTIN MÄÄRÄN."""
        return self.ITEM_VALUES.get(item_type, 1)

    def draw(self, screen, cam_x=0, cam_y=0):
        """PIIRTÄÄ KAIKKI AKTIIVISET ITEMIT NÄYTÖLLE."""
        for item in self.items:
            item.draw(screen, cam_x, cam_y)

    def clear(self):
        """POISTAA KAIKKI AKTIIVISET ITEMIT."""
        self.items.clear()

    def get_all_items(self):
        """PALAUTTAA LISTAN KAIKISTA AKTIIVISISTA ITEMEISTA."""
        return list(self.items)


class Item(pygame.sprite.Sprite):
    """
    ITEM - YKSITTÄINEN KERITYVÄI ITEMISPRITE.
    
    OMINAISUUDET:
    - AALTOLIIKE YLÖS-ALAS (UPEILEVIA LIIKKEIT)
    - GRADUELINEN PUTOAMINEN JOS SPAWNATTU KORKEALLE
    - HÄIPYMINEN ELINIÄN LOPPUPUOLELLA (5 SEKUNTIA)
    - AUTO-KERÄÄMINEN PELAAJALLA
    - KATOAA AUTOMAATTISESTI 5 SEKUNNIN JÄLKEEN
    """

    def __init__(self, pos, item_type, sprites=None, color=(255, 255, 255), size=24, falling=False):
        """
        ALUSTAA ITEMIN ANNETULLA SIJAINNILLA JA TYYPILLÄ.
        
        PARAMETRIT:
            pos       : (X, Y) SPAWN-SIJAINTI
            item_type : ITEMIN TYYPPI (ItemSpawner.ITEM_*)
            sprites   : ANIMAATION KEHYSTEN LISTA (VALINNAINEN)
            color     : RGB-VÄRI KIERROKSELLE ITEMILLE
            size      : HALKAISIJA PIKSELEINÄ
            falling   : JOS True, ITEM PUTOAA; JOS False, PYSYY PAIKALLA
        """
        super().__init__()

        self.pos = pygame.math.Vector2(pos)
        self.item_type = item_type
        self.sprites = sprites or []
        self.color = color
        self.size = size
        self.lifetime = 0.0
        self.max_lifetime = 5.0  # Seconds - items disappear after 5 seconds if not collected

        # Animation
        self.frame_index = 0
        self.anim_timer = 0.0

        # Physics: items float in place by default (falling=False)
        # Set velocity.y = 0 to stay in place, or 100 to fall down
        if falling:
            self.velocity = pygame.math.Vector2(0, 100)  # Fall speed
        else:
            self.velocity = pygame.math.Vector2(0, 0)  # Float in place
        self.base_pos_y = self.pos.y  # Store initial Y for wave motion
        self.wobble_offset = 0.0
        self.wobble_speed = 0.5  # Hz (wave motion frequency)

        # Create initial image
        if self.sprites:
            self.image = self.sprites[0]
        else:
            self._create_circle_image()
        self.rect = self.image.get_rect(center=self.pos)

    def _create_circle_image(self):
        """LUO YKSINKERTAISEN SINISEN YMPYRÄN SPRITTEEN JOS MUITA EI SAATAVILLA."""
        surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.circle(surf, self.color, (self.size // 2, self.size // 2), self.size // 2)
        self.image = surf

    def update(self, dt_s):
        """
        PÄIVITTÄÄ ITEMIN TILAN JA KOORDINAATIT.
        
        TOIMINNOT:
        - LASKE AALTOLIIIKKEEN (YLÖS-ALAS) LIIKE-OFFSET
        - SOVELLA PUTOAMINEN JOS KÄYTÖSSÄ
        - PÄIVITÄ ANIMAATION KEHYSINDEKSI
        - PÄIVITÄ RECT-SIJAINNIT
        """
        self.lifetime += dt_s

        # Gentle wave motion (vertical wobble - up and down like on a wave)
        self.wobble_offset = math.sin(self.lifetime * self.wobble_speed * 2 * math.pi) * 20

        # Apply vertical wave motion and falling
        self.pos.y = self.base_pos_y + self.wobble_offset + (self.velocity.y * self.lifetime)

        # Animation frame update (if using sprite animation)
        if self.sprites:
            self.anim_timer += dt_s
            if self.anim_timer > 0.05:  # 50ms per frame
                self.anim_timer = 0.0
                self.frame_index = (self.frame_index + 1) % len(self.sprites)
                self.image = self.sprites[self.frame_index]

        # Update rect position
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def draw(self, screen, cam_x=0, cam_y=0):
        """
        PIIRTÄÄ ITEMIN NÄYTÖLLE HÄIPYMIS-EFEKTILLÄ.
        
        OMINAISUUDET:
        - KAMERAN SIIRTYMÄN HUOMIOINTI
        - HÄIPYMIS-EFEKTI ELINIÄN LOPPUPUOLELLA (80% JO KADONNUT)
        - ALFA-KANAVAN SOVELTAMINEN GRAFIIKKAAN
        """
        # Screen position with camera offset
        screen_pos = (int(self.pos.x - cam_x), int(self.pos.y - cam_y))

        # Fade effect near end of life
        alpha = 255
        if self.lifetime > self.max_lifetime * 0.8:
            fade_factor = (self.lifetime - self.max_lifetime * 0.8) / (self.max_lifetime * 0.2)
            alpha = int(255 * (1.0 - fade_factor))

        # Draw image without rotation
        img_to_draw = self.image

        # Apply alpha
        img_to_draw.set_alpha(alpha)

        # Draw
        rect = img_to_draw.get_rect(center=screen_pos)
        screen.blit(img_to_draw, rect.topleft)
