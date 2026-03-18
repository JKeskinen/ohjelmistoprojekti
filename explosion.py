# explosion.py BOSS-enemyn räjähdys, mutta lisätty kaikkien räjähdykset managerin kautta
"""
Tämä moduuli huolehtii räjähdysanimaatioista pelissä.

- `Explosion` edustaa yksittäistä räjähdystä, joka käy läpi annettua
  kehyslistaa (frames) ja merkitään kuolleeksi (`dead`) kun animaatio loppuu.
- `ExplosionManager` lataa ja hallinnoi useita `Explosion`-instansseja,
  tarjoaa apumetodit kehyksien lataukseen, räjähdyksen spawnaamiseen,
  päivitykseen ja piirtämiseen.

Kommentit ja docstringit on kirjoitettu suomeksi jotta kuka tahansa kehittäjä
ymmärrä koodin tarkoituksen ja käytön helposti.
"""

import os
import re
import pygame


class Explosion:
    """Yksittäisen räjähdyksen animaatio.

    Parametrit:
    - frames: lista pygame.Surface-objekteja, jotka muodostavat animaation kehyksittäin.
    - pos: sijainti (x,y) maailmakoordinaateissa, mihin räjähdys sijoitetaan.
    - fps: animaation nopeus (framejä sekunnissa).

    Käyttö:
      ex = Explosion(frames, (100,200), fps=24)
      ex.update(dt_ms)
      ex.draw(screen, camera_x, camera_y)
    """

    def __init__(self, frames, pos, fps=20):
        # talletetaan kehykset ja muut tilamuuttujat
        self.frames = frames
        self.pos = pygame.Vector2(pos)
        self.fps = fps
        self.t = 0.0          # ajastin sekunteina, kerää dt:itä
        self.idx = 0          # nykyinen kehyksen indeksi
        self.dead = False     # True kun animaatio on päättynyt

        # Aloituskuva ja siihen liittyvä rect
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    def update(self, dt_ms):
        """Päivitä animaation tila.

        - `dt_ms` on kulunut aika millisekunneissa edellisestä päivityksestä.
        - Metodi kasvattaa sisäistä ajastinta ja vaihtaa kehyksiä kun
          frame_time on ylittynyt. Kun viimeinen kehys on näytetty,
          asetetaan `dead = True` jotta manager voi poistaa animaation.
        """

        if self.dead:
            return

        dt = dt_ms / 1000.0
        self.t += dt

        # kuinka kauan yhtä kehystä näytetään (sekunteina)
        frame_time = 1.0 / max(1, self.fps)
        while self.t >= frame_time:
            self.t -= frame_time
            self.idx += 1
            # jos indeksi ylittää kehyksien määrän, animaatio päättyy
            if self.idx >= len(self.frames):
                self.dead = True
                return
            # vaihdetaan nykyinen kuva ja päivitetään rect säilyttäen keskipiste
            self.image = self.frames[self.idx]
            self.rect = self.image.get_rect(center=self.rect.center)

    def draw(self, screen, camera_x=0, camera_y=0):
        """Piirtää nykyisen kehyksen ruudulle ottaen huomioon kameran siirrot.

        - `camera_x`, `camera_y` ovat maailmasta ruutuun käännettävän kameran
          offset-arvot (esim. jos peli rullaa, kamera liikkuu ja piirto skaalataan
          takaisin ruutun koordinaatistoon).
        """

        # maailma-koordinaatit -> ruutukoordinaatit
        screen.blit(self.image, (self.rect.x - camera_x, self.rect.y - camera_y))


class ExplosionManager:
    """Hallinnoi useita räjähdyksiä ja tarjoaa kehyksien latauksen.

    Vastuualueet:
    - ladata räjähdyksen kuvatiedostot halutusta kansiosta (oletuspolku löytyy
      projektin rakenteesta)
    - luoda (spawn) uusia `Explosion`-olioita annettuun sijaintiin
    - päivittää ja piirtää kaikki aktiiviset räjähdykset

    Yksinkertainen käyttö:
      manager = ExplosionManager(ExplosionManager.load_frames())
      manager.spawn((x,y), fps=24)
      manager.update(dt_ms)
      manager.draw(screen, camera_x, camera_y)
    """

    def __init__(self, frames=None):
        # frames: yhteinen kehyslista joka käytetään kaikissa spawnatuissa animaatioissa
        self.frames = list(frames) if frames else []
        # aktiivisten Explosion-olioiden lista
        self.explosions = []
        # tyypikohtaiset kehyslistat: 'boss', 'enemy', 'player'
        self.frames_by_type = {
            'boss': [],
            'enemy': [],
            'player': [],
            'hit': []
        }

    @staticmethod
    def load_frames(folder=None, size=(200, 200), pattern=r"000_Explosion1_(\d+)_0\.png"):
        """Lataa räjähdyskehyksiä annetusta kansiosta.

        Parametrit:
        - folder: polku kansioon; jos None, käytetään oletusrakennetta
        - size: skaalataan jokainen kuva tähän kokoon (leveys,korkeus)
        - pattern: regex-kuvio tiedostonimien tunnistukseen (numero-osan poimimiseen)

        Palauttaa listan pygame.Surface-objekteja järjestettynä nousevan numeron mukaan.
        """

        if folder is None:
            folder = os.path.join(os.path.dirname(__file__),
                                  "enemy-sprite",
                                  "PNG_Parts&Spriter_Animation",
                                  "Explosions",
                                  "Explosion1")

        pat = re.compile(pattern, re.IGNORECASE)
        items = []
        frames = []
        if not os.path.isdir(folder):
            # Jos kansiota ei ole, palautetaan tyhjä lista (turvatoimi)
            return frames

        # Kerätään tiedostot. Jos regex löytää numeron, käytetään sitä järjestykseen,
        # Kerätään kaikki .png-tiedostot ja tehdään luotettava järjestys.
        # Käytämme `re.search`-hakua niin, että pattern voi löytyä missä tahansa
        # tiedostonimessä. Järjestämme siten, että numerolliset avaimet ovat etusijalla
        # (esim. 000_Explosion1_1_0.png -> 1) ja muut tiedostot tulevat nimen mukaisesti.
        for fn in os.listdir(folder):
            if not fn.lower().endswith('.png'):
                continue
            m = pat.search(fn)
            if m:
                try:
                    k = int(m.group(1))
                    key = (0, k)  # numerollinen avain: prioriteetti 0
                except Exception:
                    key = (1, fn.lower())  # ei-numerollinen ryhmä: sorttaa nimellä
            else:
                key = (1, fn.lower())
            items.append((key, fn))

        # Lajitellaan avaimen mukaan (numerot ensin, sitten aakkosjärjestys)
        items.sort(key=lambda x: x[0])

        # Ladataan ja skaalataan kuvat järjestyksessä
        for _, fn in items:
            img = pygame.image.load(os.path.join(folder, fn)).convert_alpha()
            img = pygame.transform.scale(img, size)
            frames.append(img)

        return frames

    def set_frames(self, frames):
        """Aseta (tai vaihda) käytettävät kehykset.

        Tämä mahdollistaa eri räjähdystyylien lataamisen ja asettamisen myöhemmin.
        """

        self.frames = list(frames) if frames else []

    def set_frames_for(self, kind, frames):
        """Aseta kehykset tietylle tyypille.

        `kind` on teksti: `'boss'`, `'enemy'` tai `'player'`.
        """
        if kind not in self.frames_by_type:
            return
        self.frames_by_type[kind] = list(frames) if frames else []

    def spawn(self, pos, fps=24):
        """Luo uuden räjähdyksen annettuun maailmapaikkaan `pos`.

        Jos kehyksiä ei ole asetettu, metodi ei tee mitään (turvatoimi).
        """

        if not self.frames:
            return
        self.explosions.append(Explosion(self.frames, pos, fps=fps))

    def spawn_for(self, kind, pos, fps=24):
        """Luo räjähdyksen tietylle tyypille (`boss`,`enemy`,`player`).

        Jos tyypille ei ole asetettu kehyksiä, metodi ei tee mitään.
        """
        if kind not in self.frames_by_type:
            return
        frames = self.frames_by_type.get(kind) or []
        if not frames:
            return
        self.explosions.append(Explosion(frames, pos, fps=fps))

    # Erikoismetodit helpottamaan käyttöä
    def spawn_boss(self, pos, fps=20):
        """Spawn boss-räjähdys (käyttää boss-kehyksiä)."""
        self.spawn_for('boss', pos, fps=fps)

    def spawn_enemy(self, pos, fps=20):
        """Spawn tavallinen vihollisen räjähdys."""
        self.spawn_for('enemy', pos, fps=fps)

    def spawn_player(self, pos, fps=20):
        """Spawn pelaajan räjähdys."""
        self.spawn_for('player', pos, fps=fps)
    
    def spawn_hit(self, pos, fps=24):
        frames = self.frames_by_type.get('hit')
        if not frames:
            frames = self.frames_by_type.get('enemy') or self.frames
        if not frames:
            return
        self.explosions.append(Explosion(frames, pos, fps=fps))

    def load_frames_for(self, kind, folder=None, size=(200, 200), pattern=r"000_Explosion1_(\d+)_0\.png"):
        """Lataa ja asettaa kehykset tyypille `kind`.

        Esimerkiksi `kind='boss'`. Palauttaa ladatun listan (tai tyhjän listan).
        """
        frames = self.load_frames(folder=folder, size=size, pattern=pattern)
        if kind in self.frames_by_type:
            self.frames_by_type[kind] = frames
        return frames

    def load_all_defaults(self):
        """Yritä ladata oletuskansiot boss/enemy/player -animaatioille.

        Tämä yrittää järkeviä oletuspolkuja, mutta voit aina kutsua
        `load_frames_for` omilla kansioillasi jos haluat hallita polkuja.
        """
        boss_explosion_size = (150, 150)
        enemy_explosion_size = (60, 60)
        base = os.path.join(os.path.dirname(__file__), 'enemy-sprite', 'PNG_Parts&Spriter_Animation', 'Explosions')
        # boss: käytä Explosion1 -kansion kehyksiä oletuksena (suurikokoinen)
        boss_folder = os.path.join(base, 'Explosion1')
        self.load_frames_for('boss', folder=boss_folder, size=(boss_explosion_size))
        # enemy: sama paikka pienemmällä koossa
        enemy_folder = os.path.join(base, 'Explosion1')
        self.load_frames_for('enemy', folder=enemy_folder, size=(enemy_explosion_size))
        # player: use dedicated explosion sprites so the effect is visually separate
        # from the ship's own Destroyed animation drawn by Player/Player2.
        player_folder = os.path.join(base, 'Explosion1')
        player_frames = self.load_frames_for('player', folder=player_folder, size=(220, 220))
        if not player_frames:
            # Fallback to enemy explosion frames if a dedicated player set is missing.
            self.frames_by_type['player'] = list(self.frames_by_type.get('enemy') or [])

    def update(self, dt_ms):
        """Päivitä kaikki aktiiviset räjähdykset ja poista päättyneet.

        Käytetään listan kopion läpikäyntiä jotta poisto voi tapahtua turvallisesti
        ilman virheitä iteroinnin aikana.
        """

        for ex in list(self.explosions):
            ex.update(dt_ms)
            if ex.dead:
                self.explosions.remove(ex)

    def draw(self, screen, camera_x=0, camera_y=0):
        """Piirtää kaikki aktiiviset räjähdykset ruudulle.

        Huomioi kameran offsetit, samoin kuin `Explosion.draw`-metodi.
        """

        for ex in self.explosions:
            ex.draw(screen, camera_x, camera_y)