import pygame
import math
from Ammus import Ammus


class Player(pygame.sprite.Sprite):
    """
    Player-luokka:
    - `frames`: lista pygame.Surface -objekteja animaation kehyksiksi
    - `rect` kertoo pelaajan sijainnin maailmassa (maailman koordinaatit)
    - update(dt) hoitaa animaation vaihtamisen
    - move(dx, dy, world_w, world_h) siirtää pelaajaa ja rajoittaa maailmaan
    - draw(screen, cam_x, cam_y) piirtää pelaajan ruudulle ottaen kameran offsetin huomioon
    """

    def __init__(self, scale_factor, frames, x, y, boost_frames=None):
        # Offset ampumisspriten piirtämiseen
        self.attack_offset_distance = 3  # etäisyys keulasta eteenpäin (pikseleinä)
        super().__init__()
        # tallennetaan skaalaustekijä, jotta voimme esiskaalata kehykset
        self.scale_factor = scale_factor
        # tukee erillisiä animaatioita: move ja boost
        # esiskaalataan annettu kehyslista (jos olemassa)
        liike_frames = frames if frames else [pygame.Surface((32, 32), pygame.SRCALPHA)]
        self.animaatio = {
            'move': self._scale_frames(liike_frames),
            'boost': self._scale_frames(boost_frames) if boost_frames else []
        }
        self.frame_index = 0
        self.current_anim = 'move'
        # säilytä aktiivinen kuva
        self.image = self.animaatio[self.current_anim][self.frame_index]
        self.rect = self.image.get_rect(center=(x, y))
        # rect on nyt luotu skaalatusta kuvasta, ei tarvita lisäskaalausta
        # Käytetään liikkeessä tarkempaa kelluvaa sijaintia
        self.pos = pygame.math.Vector2(x, y)
        self.vel = pygame.math.Vector2(0, 0)
        self.angle = 0.0  # asteina
        self.turn_speed = 180.0  # astetta per sekunti
        self.accel = 300.0  # pikseleitä per sekunti^2
        # Ampumisen cooldown
        self.shoot_cooldown = 300  # ms ammusten välillä
        self.shoot_timer = 0
        self.max_speed = 400.0  # pikseleitä per sekunti
        self.brake_decel = 500.0  # jarrutusvoima (px/s^2)
        self.anim_timer = 0
        self.anim_speed = 100  # ms per frame
        self.moveUp = False
        self.moveDown = False
        self.turnLeft = False
        self.turnRight = False
        self.shoot = False
        # attack_1-sprite alustetaan ampumista varten
        self.attack_frames = []
        # Ladataan kaikki attack_1 spritet animaatioksi
        attack_paths = [
            'alukset/alus/Corvette/Attack_1/000_attack_1_0.png',
            'alukset/alus/Corvette/Attack_1/001_attack_1_1.png',
            'alukset/alus/Corvette/Attack_1/002_attack_1_2.png',
            'alukset/alus/Corvette/Attack_1/003_attack_1_3.png',
        ]
        for path in attack_paths:
                img = pygame.image.load(path).convert_alpha()
                w = max(1, int(img.get_width() * self.scale_factor))
                h = max(1, int(img.get_height() * self.scale_factor))
                self.attack_frames.append(pygame.transform.scale(img, (w, h)))
        # Ammuskuva ja ammuslista
        self.bullet_img = pygame.image.load('alukset/alus/Corvette/Charge_1/000_Charge_1_0.png').convert_alpha()
        w = max(1, int(self.bullet_img.get_width() * self.scale_factor))
        h = max(1, int(self.bullet_img.get_height() * self.scale_factor))
        self.bullet_img = pygame.transform.scale(self.bullet_img, (w, h))
        self.bullets = pygame.sprite.Group()


        self.attack_frame_index = 0
        self.attack_anim_timer = 0
        self.attack_anim_speed = 80  # ms per frame


    def _scale_frames(self, frames):
        """Palauttaa listan skaalatuista pygame.Surface-kehyksistä.
        Huom: jos `frames` on None tai tyhjä lista, palautetaan tyhjä lista.
        """
        if not frames:
            return []
        scaled = []
        for f in frames:
            w = max(1, int(f.get_width() * self.scale_factor))
            h = max(1, int(f.get_height() * self.scale_factor))
            scaled.append(pygame.transform.scale(f, (w, h)))
        return scaled

    def update(self, dt):
        """Päivitä animaatioaika (dt millisekunteina)."""
        # Päivitä cooldown
        if self.shoot_timer > 0:
            self.shoot_timer -= dt
        # valitse aktiivinen animaatio (boost kun w painetaan ja boost-kehyksiä löytyy)
        keys = pygame.key.get_pressed()
        self.moveUp = keys[pygame.K_w]
        self.moveDown = keys[pygame.K_s]
        # nämä pitää olla käänteiset, left on k_d ja right on k_a
        self.turnLeft = keys[pygame.K_d]
        self.turnRight = keys[pygame.K_a]
        # Oikea Ctrl ampumista varten
        self.shoot = keys[pygame.K_RCTRL]
        if self.shoot:
            # Päivitä attack_1 animaatio
            if self.attack_frames:
                self.attack_anim_timer += dt
                if self.attack_anim_timer >= self.attack_anim_speed:
                    self.attack_anim_timer -= self.attack_anim_speed
                    self.attack_frame_index = (self.attack_frame_index + 1) % len(self.attack_frames)
        else:
            self.attack_frame_index = 0
            self.attack_anim_timer = 0
        if self.shoot and self.shoot_timer <= 0:
            self.shoot_timer = self.shoot_cooldown
            side_offset = 15 # ammusten sivu-offset 
            forward_offset = 20 # ammusten lähtöpiste-offset
            rad = math.radians(self.angle)
            perp_rad = rad + math.pi/2
            # Vasen ammus
            x1 = self.pos.x + math.cos(rad) * forward_offset + math.cos(perp_rad) * side_offset
            y1 = self.pos.y + math.sin(rad) * forward_offset + math.sin(perp_rad) * side_offset
            # Oikea ammus
            x2 = self.pos.x + math.cos(rad) * forward_offset - math.cos(perp_rad) * side_offset
            y2 = self.pos.y + math.sin(rad) * forward_offset - math.sin(perp_rad) * side_offset
            self.bullets.add(Ammus(x1, y1, self.angle, self.bullet_img))
            self.bullets.add(Ammus(x2, y2, self.angle, self.bullet_img))
        # Päivitä ammukset
        self.bullets.update(dt)


        # tähän lisätään uusia animaatioita tarpeen mukaan.
        # valitaan tarvitaanko lista,array tai dict rakenteita
        # new_anim määritellään painikkeiden perusteella
        # w = boost, muuten move
        # ctrl = attack1, Alt Gr = attack2 jne.
        # space = rockets jne.
        new_anim = 'boost' if (self.moveUp and self.animaatio.get('boost')) else 'move'
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

        # aikamuunnos
        dt_s = dt / 1000.0

        # kääntö
        if self.turnLeft:
            self.angle += self.turn_speed * dt_s
        if self.turnRight:
            self.angle -= self.turn_speed * dt_s

        # eteenpäin (thrust)
        if self.moveUp:
            rad = math.radians(self.angle)
            thrust = pygame.math.Vector2(math.cos(rad), math.sin(rad)) * self.accel * dt_s
            self.vel += thrust
            # rajoitus maksiminopeuteen
            if self.vel.length() > self.max_speed:
                self.vel.scale_to_length(self.max_speed)

        # jarru (paina s)
        if self.moveDown:
            speed = self.vel.length()
            if speed > 0:
                dec = self.brake_decel * dt_s
                new_speed = max(0.0, speed - dec)
                if new_speed == 0:
                    self.vel = pygame.math.Vector2(0, 0)
                else:
                    self.vel.scale_to_length(new_speed)

        # päivitä sijainti
        self.pos += self.vel * dt_s
        # päivitä rect-keskikohta
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        # Liike on jo laskettu self.vel/self.pos: älä muuta rect:ia suoraan täällä.

    def move(self, dx, dy, world_w, world_h):
        """Siirrä pelaajaa ja rajoita maailman reunoihin."""
        # move kutsutaan pääsilmukasta mahdollisesti rajoitusten asettamiseksi
        self.rect.x += dx
        self.rect.y += dy
        # synkronoi myös pos-muuttuja, jotta seuraavat päivitykset säilyttävät koordinaatit
        self.pos.x = self.rect.centerx
        self.pos.y = self.rect.centery
        # Rajoita olio maailmaan
        self.rect.x = max(0, min(self.rect.x, world_w - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, world_h - self.rect.height))
        # pidä pos yhteneväisenä rajauksen jälkeen
        self.pos.x = self.rect.centerx
        self.pos.y = self.rect.centery
        



    def draw(self, screen, cam_x, cam_y):
        """Piirrä pelaaja ruudulle kameran offsetilla."""
        # Kierrä aktiivista kehystä ja piirrä sen keskipisteellä
        base = self.image
        rotated = pygame.transform.rotate(base, -self.angle)
        rot_rect = rotated.get_rect(center=(self.pos.x - cam_x, self.pos.y - cam_y))
        screen.blit(rotated, rot_rect.topleft)
        # Piirrä aina kaikki ammukset
        for bullet in self.bullets:
            screen.blit(bullet.image, (bullet.rect.x - cam_x, bullet.rect.y - cam_y))
        # Jos ammutaan, piirretään attack_1-sprite
        if self.shoot and self.attack_frames:
            attack_sprite = self.attack_frames[self.attack_frame_index]
            attack_rotated = pygame.transform.rotate(attack_sprite, -self.angle)
            # Offset keulan suuntaan
            rad = math.radians(self.angle)
            offset_x = math.cos(rad) * self.attack_offset_distance
            offset_y = math.sin(rad) * self.attack_offset_distance
            attack_center = (self.pos.x - cam_x + offset_x, self.pos.y - cam_y + offset_y)
            attack_rect = attack_rotated.get_rect(center=attack_center)
            screen.blit(attack_rotated, attack_rect.topleft)