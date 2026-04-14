"""
================================================================================
                         UI.PY - PELIRAYKAISU MODUULI
================================================================================
KUVAUS:
    TÄMÄ MODUULI HALLITSEE KAIKEN HUD-NÄYTÖNTÄ JA HEALTHBARIEN PIIRTÄMISEN
    PELIN AIKANA. SISÄLTÄÄ FUNKTIOT BOOST-MITTARILLE, ARMOR-MITTARILLE,
    DAMAGE-NÄYTÖLLE, PELAAJAN TERVEYSPALKEILLE JA VIHOLLISTEN TERVEYSPALKEILLE.
    
PÄÄFUNKTIOT:
    - draw_hud()                   : PIIRTÄÄ PÄÄASIALLISEN HUD-NÄYTÖN
    - draw_boost_bar()             : PIIRTÄÄ BOOST-ENERGIAMITTARIN
    - draw_armor_bar()             : PIIRTÄÄ PANSSARIN MITTARIN
    - draw_damage_display()        : PIIRTÄÄ DAMAGE-TASON NÄYTÖN
    - draw_enemy_health_bar()      : PIIRTÄÄ VIHOLLISEN TERVEYSPALKIN
    - draw_death_overlay()         : PIIRTÄÄ KUOLEMA-NÄYTÖN
    - load_health_bar_images()     : LATAA TERVEYSPALKKIEN KUVAT LEVYLTÄ
    
MODUULIN GLOBAALIT MUUTTUJAT:
    - ENEMY_BAR_IMGS               : VÄLIMUISTI VIHOLLISTEN PALKKIEN KUVILLE
    
================================================================================
"""

import pygame
import os


# ============================================================================
# PÄÄASIALLINEN HUD-NÄYTTÖ - PIIRTÄÄ PELAAJAN TERVEYSTILAN JA KAIKKI MITTARIT
# ============================================================================
def draw_hud(screen, X, Y, player, lives, health_imgs, HUD_POS):
    """
    PIIRTÄÄ KOKO HUD-NÄYTÖN: ELÄMÄT, BOOST-MITTARI, ARMOR-MITTARI JA DMG-TASO.
    
    PARAMETRIT:
        screen      : PYGAME SURFACE JOHON PIIRRETÄÄN
        X, Y        : NÄYTÖN LEVEYS JA KORKEUS
        player      : PELAAJA-OBJEKTI (SISÄLTÄÄ HEALTH, ARMOR, DMG_BONUS)
        lives       : ELÄMIEN MÄÄRÄ (VARALLINEN ARVO)
        health_imgs : SANAKIRJA TERVEYSPALKKIEN KUVILLE {0-5}
        HUD_POS     : SIJAINTI HUD-NÄYTTÖÖN NÄYTÖLLÄ (x, y)
    
    LOGIIKKA:
        1. TARKISTA KUINKA MONTA ELÄMÄÄ PELAAJALLA ON
        2. VALITSE OIKEA KUVA TERVEYSTILÄN MUKAAN
        3. PIIRTÄÄ KAIKKI MITTARIT: BOOST, ARMOR, DMG
    """
    
    # ALUSTA FONTTI HUD-TEKSTILLE
    font = pygame.font.SysFont('Arial', 24)
    
    # HAKE PELAAJAN NYKYINEN TERVEYSTILA
    cur_health = lives
    max_h = 5
    
    if hasattr(player, 'health'):
        cur_health = int(max(0, min(player.health, getattr(player, 'max_health', 5))))
        max_h = int(getattr(player, 'max_health', 5))
    
    # VALITSE OIKEA HUD-KUVA TERVEYSTILAN PERUSTEELLA
    hud_img = None
    if isinstance(health_imgs, dict):
        if max_h > 0 and max_h != 5:
            slot = int(round((cur_health / max_h) * 5))
        else:
            slot = int(max(0, min(cur_health, 5)))
        hud_img = health_imgs.get(slot)
    
    # PIIRTÄÄ KUVAN TAI TEKSTIN (JOS KUVA EI SAATAVILLA)
    if hud_img is not None:
        screen.blit(hud_img, HUD_POS)
    else:
        # PIIRTÄÄ TEKSTILLÄ JOS KUVAA EI OLE
        lives_text = font.render(f"Elämät: {cur_health}", True, (255, 255, 255))
        screen.blit(lives_text, (X - 200, 10))
    
    # PIIRTÄÄ BOOST-MITTARI
    draw_boost_bar(screen, player, X, Y)
    
    # PIIRTÄÄ ARMOR-MITTARI
    draw_armor_bar(screen, player, X, Y)
    
    # PIIRTÄÄ DMG-NÄYTTÖ
    draw_damage_display(screen, player, X, Y)


# ============================================================================
# BOOST-ENERGIAMITTARI - NÄYTTÄÄ BOOST-TILAN JA LATAUSPROSENTTI
# ============================================================================
def draw_boost_bar(screen, player, X, Y):
    """
    PIIRTÄÄ BOOST-ENERGIAN MITTARIN NÄYTÖLLE. NÄYTTÄÄ KUINKA PALJON
    ENERGIAA ON JÄLJELLÄ JA ONKO BOOST KÄYTÖSSÄ VAI LADATESSA.
    
    PARAMETRIT:
        screen : PYGAME SURFACE JOHON PIIRRETÄÄN
        player : PELAAJA-OBJEKTI (SISÄLTÄÄ BOOST_ENERGY, BOOST_ACTIVE)
        X, Y   : NÄYTÖN LEVEYS JA KORKEUS
    
    VÄRIKOODI:
        KELTAINEN  : BOOST ON KÄYTÖSSÄ (AKTIIVINEN)
        SININEN    : BOOST LADATAAN (VARAUKSESSA)
        PUNAINEN   : BOOST ON LOPPUNUT (LATAA UUDESTAAN)
        VIHREÄ     : BOOST ON TÄYNNÄ JA VALMIS
    """
    
    # TARKISTA ONKO PELAAJALLA BOOST-ENERGIAA
    if not hasattr(player, 'boost_energy'):
        return
    
    # MITTARIN PARAMETRIT JA VÄRIT
    bar_width = 200
    bar_height = 20
    bar_x = 20
    bar_y = Y - 40
    border_thickness = 2
    
    color_bg = (50, 50, 50)
    color_charging = (100, 150, 255)
    color_active = (255, 200, 0)
    color_border = (255, 255, 255)
    
    # HAKE BOOST-PARAMETRIT
    boost_energy = getattr(player, 'boost_energy', 0.0)
    boost_max_energy = getattr(player, 'boost_max_energy', 3.0)
    boost_active = getattr(player, 'boost_active', False)
    
    # LASKE ENERGIA-PROSENTTI
    if boost_max_energy > 0:
        progress = boost_energy / boost_max_energy
    else:
        progress = 0.0
    
    # RAJOITA 0-1 VÄLILLE
    progress = max(0.0, min(1.0, progress))
    
    # VALITSE TÄYTTÖ-VÄRI TILAN MUKAAN
    if boost_active:
        fill_color = color_active
    else:
        fill_color = color_charging
    
    # PIIRTÄÄ TAUSTA
    pygame.draw.rect(screen, color_bg, (bar_x, bar_y, bar_width, bar_height))
    
    # PIIRTÄÄ TÄYTTÖ (PROSENTTI-MUKAAN)
    fill_width = int(bar_width * progress)
    if fill_width > 0:
        pygame.draw.rect(screen, fill_color, (bar_x, bar_y, fill_width, bar_height))
    
    # PIIRTÄÄ KEHYS
    pygame.draw.rect(screen, color_border, (bar_x, bar_y, bar_width, bar_height), border_thickness)
    
    # PIIRTÄÄ TEKSTI JA TILA
    font = pygame.font.SysFont('Arial', 14)
    boost_is_full = (abs(boost_energy - boost_max_energy) < 0.01)
    boost_depleted = getattr(player, 'boost_depleted', False)
    
    # VALITSE TEKSTI TILAN MUKAAN
    if boost_active:
        text = f"BOOST: {boost_energy:.1f}s"
        text_color = (255, 200, 0)
    elif boost_depleted:
        text = f"RECHARGING: {boost_energy:.1f}s"
        text_color = (255, 100, 100)
    elif boost_is_full:
        text = "BOOST READY! (Shift)"
        text_color = (100, 255, 100)
    else:
        text = f"CHARGING: {boost_energy:.1f}s"
        text_color = (100, 150, 255)
    
    text_surf = font.render(text, True, text_color)
    screen.blit(text_surf, (bar_x + 5, bar_y - 25))


# ============================================================================
# PANSSARIN MITTARI - NÄYTTÄÄ ARMOR-TILAN JA VAURIOITUMISEN
# ============================================================================
def draw_armor_bar(screen, player, X, Y):
    """
    PIIRTÄÄ PELAAJAN PANSSARIN (ARMOR) MITTARIN. NÄYTTÄÄ KUINKA PALJON
    SUOJAUSTA ON JÄLJELLÄ (0-10).
    
    PARAMETRIT:
        screen : PYGAME SURFACE JOHON PIIRRETÄÄN
        player : PELAAJA-OBJEKTI (SISÄLTÄÄ ARMOR-ARVON)
        X, Y   : NÄYTÖN LEVEYS JA KORKEUS
    
    VÄRIKOODI:
        SININEN  : ARMOR ON EHJÄ JA SUOJAA PELAAJAA
        PUNAINEN : ARMOR ON RIKKI (0 PISTETTÄ)
    """
    
    # TARKISTA ONKO PELAAJALLA ARMOR-OMINAISUUTTA
    if not hasattr(player, 'armor'):
        return
    
    # MITTARIN PARAMETRIT
    bar_width = 200
    bar_height = 20
    bar_x = 20
    bar_y = Y - 70
    max_armor = 10
    border_thickness = 2
    
    color_bg = (50, 50, 50)
    color_border = (255, 255, 255)
    
    # HAKE ARMOR-ARVO
    armor = getattr(player, 'armor', 0)
    
    # LASKE ARMOR-PROSENTTI
    if max_armor > 0:
        progress = min(armor / max_armor, 1.0)
    else:
        progress = 0.0
    
    # PIIRTÄÄ TAUSTA
    pygame.draw.rect(screen, color_bg, (bar_x, bar_y, bar_width, bar_height))
    
    # VALITSE TÄYTTÖ-VÄRI: SININEN (EHÄ) TAI PUNAINEN (RIKKI)
    if armor > 0:
        fill_color = (100, 150, 200)
    else:
        fill_color = (255, 0, 0)
    
    # PIIRTÄÄ TÄYTTÖ
    fill_width = int(bar_width * progress)
    if fill_width > 0:
        pygame.draw.rect(screen, fill_color, (bar_x, bar_y, fill_width, bar_height))
    
    # PIIRTÄÄ KEHYS
    pygame.draw.rect(screen, color_border, (bar_x, bar_y, bar_width, bar_height), border_thickness)
    
    # PIIRTÄÄ TEKSTI JA ARMOR-TILA
    font = pygame.font.SysFont('Arial', 14)
    
    if armor <= 0 and max_armor > 0:
        text = "ARMOR BROKEN!"
        text_color = (255, 50, 50)
    else:
        text = f"ARMOR: {armor:.0f}/{max_armor}"
        if armor > 0:
            text_color = (100, 150, 200)
        else:
            text_color = (255, 100, 100)
    
    text_surf = font.render(text, True, text_color)
    screen.blit(text_surf, (bar_x + 5, bar_y - 25))


# ============================================================================
# DAMAGE-TASON NÄYTTÖ - NÄYTTÄÄ PELAAJAN DAMAGE-TASON (1-3)
# ============================================================================
def draw_damage_display(screen, player, X, Y):
    """
    NÄYTTÄÄ PELAAJAN DAMAGE-TASON TASOLLA 1-3. MUKAAN LUKIEN VÄRIN MUUTOKSET
    PERUSTEELLA TASONUMERO.
    
    PARAMETRIT:
        screen : PYGAME SURFACE JOHON PIIRRETÄÄN
        player : PELAAJA-OBJEKTI (SISÄLTÄÄ DAMAGE_BONUS)
        X, Y   : NÄYTÖN LEVEYS JA KORKEUS
    
    DAMAGE-LASKENTA:
        BASE_DMG: 1.0
        PER_BONUS: 0.5
        MAKSIMI: 3.0 DMG
        
    TASOT:
        TASO 1 (VIHREÄ)   : DMG <= 1.0
        TASO 2 (ORANSSI)  : DMG <= 2.0
        TASO 3 (PUNAINEN) : DMG >= 2.0
    """
    
    # TARKISTA ONKO PELAAJA OLEMASSA
    if not player:
        return
    
    # HAKE DAMAGE_BONUS
    damage_bonus = getattr(player, 'damage_bonus', 0)
    
    # LASKE NYKYINEN DAMAGE
    base_dmg = 1.0
    current_dmg = min(3.0, base_dmg + (damage_bonus * 0.5))
    
    # MÄÄRITÄ TIER JA VÄRI PERUSTEELLA DAMAGE
    if current_dmg <= 1.0:
        dmg_level = 1
        dmg_color = (100, 255, 100)
    elif current_dmg <= 2.0:
        dmg_level = 2
        dmg_color = (255, 200, 100)
    else:
        dmg_level = 3
        dmg_color = (255, 100, 100)
    
    # PIIRTÄÄ DAMAGE-TEKSTI
    font = pygame.font.SysFont('Arial', 16, bold=True)
    dmg_text = f"DMG: {current_dmg:.1f} (Tier {dmg_level})"
    text_surf = font.render(dmg_text, True, dmg_color)
    
    # SIJAINTI OIKEASSA YLÄKULMASSA
    display_x = X - 300
    display_y = Y - 100
    screen.blit(text_surf, (display_x, display_y))


# ============================================================================
# TERVEYSPALKKIEN KUVAN LATAUS - LATAA PNG-KUVAT LEVYLTÄ
# ============================================================================
def load_health_bar_images(base_dir):
    """
    LATAA TERVEYSPALKKIEN TAUSTA- JA ETUALAN KUVAT ANNETUSTA KANSIOSTA.
    ETSII TIEDOSTOJA, JOISSA ON "BACKGROUND" JA "FOREGROUND" NIMESSÄ.
    
    PARAMETRIT:
        base_dir : KANSIO JOSTA LADATAAN KUVAT
    
    PALAUTTAA:
        dict: {'bg': Surface tai None, 'fg': Surface tai None}
    """
    
    imgs = {'bg': None, 'fg': None}
    
    # TARKISTA ONKO KANSIO OLEMASSA
    if not os.path.isdir(base_dir):
        return imgs
    
    # ETSI JA LADAA TAUSTA JA ETUALAN KUVAT
    for name in os.listdir(base_dir):
        ln = name.lower()
        path = os.path.join(base_dir, name)
        
        # LATAA BACKGROUND-KUVA
        if 'background' in ln and imgs['bg'] is None:
            if os.path.isfile(path):
                try:
                    imgs['bg'] = pygame.image.load(path).convert_alpha()
                except Exception:
                    pass
        
        # LATAA FOREGROUND-KUVA
        if 'foreground' in ln and imgs['fg'] is None:
            if os.path.isfile(path):
                try:
                    imgs['fg'] = pygame.image.load(path).convert_alpha()
                except Exception:
                    pass
    
    return imgs


# ============================================================================
# MODUULIN GLOBAALI VÄLIMUISTI VIHOLLISTEN TERVEYSPALKKIEN KUVILLE
# ============================================================================
ENEMY_BAR_IMGS = None


# ============================================================================
# VIHOLLISTEN TERVEYSPALKKIEN ALUSTAMINEN
# ============================================================================
def init_enemy_health_bars(project_root=None):
    """
    ALUSTAA VIHOLLISTEN TERVEYSPALKKIEN KUVAT MODUULIN GLOBAALIIN VÄLIMUISTIIN.
    TÄMÄ KUTSUTAAN KERRAN PELIN START-VAIHEESSA.
    
    PARAMETRIT:
        project_root : PROJEKTIN JUURI-KANSIO (JOS None, KÄYTETÄÄN SKRIPTIN KANSIOTA)
    
    PALAUTTAA:
        dict: LADATUT KUVAT JA NIIDEN SIJAINNIT
    """
    
    global ENEMY_BAR_IMGS
    
    if project_root is None:
        project_root = os.path.dirname(__file__)
    
    base = os.path.join(project_root, 'images', 'enemy_health_bars_2.0', 'enemy_health_bars_2.0')
    ENEMY_BAR_IMGS = load_health_bar_images(base)
    
    return ENEMY_BAR_IMGS


# ============================================================================
# HAKE VIHOLLISTEN TERVEYSPALKKIEN KUVAT VÄLIMUISTISTA
# ============================================================================
def get_enemy_bar_images():
    """
    PALAUTTAA GLOBAALIN VÄLIMUISTIN VIHOLLISTEN TERVEYSPALKKIEN KUVILLE.
    
    PALAUTTAA:
        dict: {'bg': Surface tai None, 'fg': Surface tai None}
    """
    
    global ENEMY_BAR_IMGS
    return ENEMY_BAR_IMGS


# ============================================================================
# VIHOLLISEN TERVEYSPALKIN PIIRTÄMINEN
# ============================================================================
def draw_enemy_health_bar(screen, x, y, width, height, cur_hp, max_hp, imgs, tint=(255, 0, 0)):
    """
    PIIRTÄÄ VIHOLLISEN TERVEYSPALKIN ANNETTUUN SIJAINTIIN.
    KÄYTTÄÄ LADATTUJA KUVIA (JOS SAATAVILLA) TAI YKSINKERTAISTA TÄYTTÖÄ.
    
    PARAMETRIT:
        screen    : PYGAME SURFACE JOHON PIIRRETÄÄN
        x, y      : PALKIN SIJAINTI NÄYTÖLLÄ
        width     : PALKIN LEVEYS PIKSELEINÄ
        height    : PALKIN KORKEUS PIKSELEINÄ
        cur_hp    : NYKYINEN TERVEYSTILA
        max_hp    : MAKSIMI TERVEYSTILA
        imgs      : SANAKIRJA PALKKIEN KUVILLE {'bg', 'fg'}
        tint      : RGB-VÄRI TÄYTTÖÖN (OLETUKSENA PUNAINEN)
    
    LOGIIKKA:
        1. LASKE TERVEYSPROSENTTI
        2. PIIRTÄÄ TAUSTA (KUVA TAI VÄRI)
        3. PIIRTÄÄ TÄYTTÖ PROSENTTI-MUKAAN
        4. PIIRTÄÄ ETUALAN KUVA (JOS SAATAVILLA)
    """
    
    # LASKE TERVEYSPROSENTTI
    ratio = 0.0
    if max_hp is not None and max_hp > 0:
        ratio = max(0.0, min(float(cur_hp) / float(max_hp), 1.0))
    
    # PADDING PALKKIEN YMPÄRILLE
    pad = max(6, int(min(width, height) * 0.12))
    total_w = width + pad * 2
    total_h = height + pad * 2
    bx = x - pad
    by = y - pad
    
    # PIIRTÄÄ TAUSTA (KUVA TAI VÄRI)
    if imgs is not None and imgs.get('bg') is not None:
        bg = pygame.transform.smoothscale(imgs['bg'], (total_w, total_h))
        screen.blit(bg, (bx, by))
    else:
        bg_s = pygame.Surface((total_w, total_h), pygame.SRCALPHA)
        bg_s.fill((20, 20, 20, 220))
        screen.blit(bg_s, (bx, by))
    
    # PIIRTÄÄ TERVEYSTÄYTTÖ (KIINTEÄ VÄRI, EI LÄPINÄKYVÄ)
    fill_w = max(0, int(width * ratio))
    if fill_w > 0:
        s = pygame.Surface((fill_w, height))
        s.fill((tint[0], tint[1], tint[2]))
        screen.blit(s, (x, y))
    
    # PIIRTÄÄ ETUALAN KUVA (JOS SAATAVILLA)
    if imgs is not None and imgs.get('fg') is not None:
        frame = imgs['fg']
        frame_s = pygame.transform.smoothscale(frame, (total_w, total_h))
        screen.blit(frame_s, (bx, by))


# ============================================================================
# KUOLEMA-NÄYTÖN PIIRTÄMINEN - NÄYTTÄÄ GAME OVER -NÄYTÖN
# ============================================================================
def draw_death_overlay(screen, X, Y, health_imgs, player, lives):
    """
    PIIRTÄÄ KUOLEMA-NÄYTÖN: PIMEA TAUSTA, "YOU DIED" -TEKSTI JA
    RESTART/QUIT-NAPIT.
    
    PARAMETRIT:
        screen      : PYGAME SURFACE JOHON PIIRRETÄÄN
        X, Y        : NÄYTÖN LEVEYS JA KORKEUS
        health_imgs : SANAKIRJA TERVEYSPALKKIEN KUVILLE
        player      : PELAAJA-OBJEKTI
        lives       : ELÄMIEN MÄÄRÄ
    
    PALAUTTAA:
        tuple: (RESTART_BUTTON_RECT, QUIT_BUTTON_RECT)
    """
    
    # PIIRTÄÄ PIMEÄ TAUSTA (LÄPINÄKYVÄ OVERLAY)
    overlay = pygame.Surface((X, Y))
    overlay.set_alpha(220)
    overlay.fill((10, 10, 10))
    screen.blit(overlay, (0, 0))
    
    screen_rect = screen.get_rect()
    cx, cy = screen_rect.center
    
    # YRITÄ PIIRTÄÄ SUURI EMPTY-HEALTH KUVA
    large_rect = None
    cur_health = 0
    max_h = 5
    
    if hasattr(player, 'health'):
        cur_health = player.health
    else:
        cur_health = lives
    
    if hasattr(player, 'max_health'):
        max_h = int(getattr(player, 'max_health', 5))
    
    # LASKE SLOT TERVEYSPALKIN KUVALLE
    if max_h > 0 and max_h != 5:
        slot = int(round((cur_health / max_h) * 5))
    else:
        slot = int(max(0, min(int(cur_health), 5)))
    
    # TARKISTA ONKO TYHJÄ TERVEYSPALKIN KUVA OLEMASSA
    if slot == 0 and isinstance(health_imgs, dict) and health_imgs.get(0) is not None:
        hud_img = health_imgs.get(0)
        sw, sh = hud_img.get_size()
        max_w = int(X * 0.8)
        max_h = int(Y * 0.6)
        scale = min(max_w / sw, max_h / sh, 1.0)
        large_w = max(1, int(sw * scale))
        large_h = max(1, int(sh * scale))
        large_img = pygame.transform.scale(hud_img, (large_w, large_h))
        large_rect = large_img.get_rect(center=(cx, cy - 40))
        screen.blit(large_img, large_rect.topleft)
    
    # PIIRTÄÄ "YOU DIED" -OTSIKKO
    font_large = pygame.font.SysFont('Arial', 48)
    font_small = pygame.font.SysFont('Arial', 28)
    title = font_large.render("YOU DIED", True, (220, 80, 80))
    
    if large_rect is not None:
        title_rect = title.get_rect(center=(cx, large_rect.top - 40))
    else:
        title_rect = title.get_rect(center=(cx, cy - 140))
    
    screen.blit(title, title_rect.topleft)
    
    # LUO RESTART JA QUIT -NAPIT
    btn_w, btn_h = 320, 64
    restart_btn = pygame.Rect(0, 0, btn_w, btn_h)
    quit_btn = pygame.Rect(0, 0, btn_w, btn_h)
    
    if large_rect is not None:
        restart_btn.center = (cx, large_rect.bottom + btn_h // 2 + 24)
        quit_btn.center = (cx, large_rect.bottom + btn_h // 2 + 24 + btn_h + 12)
    else:
        restart_btn.center = (cx, cy)
        quit_btn.center = (cx, cy + btn_h + 16)
    
    # PIIRTÄÄ NAPIT
    pygame.draw.rect(screen, (70, 150, 70), restart_btn)
    pygame.draw.rect(screen, (150, 70, 70), quit_btn)
    
    # PIIRTÄÄ NAPPI-TEKSTIT
    restart_label = font_small.render("Restart", True, (255, 255, 255))
    quit_label = font_small.render("Quit", True, (255, 255, 255))
    screen.blit(restart_label, restart_label.get_rect(center=restart_btn.center).topleft)
    screen.blit(quit_label, quit_label.get_rect(center=quit_btn.center).topleft)
    
    pygame.display.update()
    return restart_btn, quit_btn


# ============================================================================
# MUKAUTETTU TERVEYSPALKIN PIIRTÄMINEN - YKSINKERTAINEN JA JOUSTAVA
# ============================================================================
def draw_healthbar_custom(screen,
                          fill_size_x, fill_size_y,
                          fill_x, fill_y,
                          frame_size_x, frame_size_y,
                          frame_x, frame_y,
                          cur_hp, max_hp,
                          imgs=None,
                          tint=(255, 0, 0)):
    """
    PIIRTÄÄ MUKAUTETUN TERVEYSPALKIN ANNETTUIHIN PARAMETREIHIN.
    
    PARAMETRIT:
        screen       : PYGAME SURFACE JOHON PIIRRETÄÄN
        fill_size_x  : TÄYTTÖ-OSA LEVEYS
        fill_size_y  : TÄYTTÖ-OSA KORKEUS
        fill_x       : TÄYTTÖ-OSA X-SIJAINTI
        fill_y       : TÄYTTÖ-OSA Y-SIJAINTI
        frame_size_x : KEHYS LEVEYS
        frame_size_y : KEHYS KORKEUS
        frame_x      : KEHYS X-SIJAINTI
        frame_y      : KEHYS Y-SIJAINTI
        cur_hp       : NYKYINEN TERVEYSTILA
        max_hp       : MAKSIMI TERVEYSTILA
        imgs         : SANAKIRJA PALKKIEN KUVILLE (VALINNAINEN)
        tint         : RGB-VÄRI TÄYTTÖÖN
    
    PIIRTÄÄ JÄRJESTYKSESSÄ:
        1. TAUSTA/KEHYS-TAUSTA (KUVA TAI VÄRI)
        2. KIINTEÄ VÄRITÄYTTÖ (PROSENTTI-MUKAAN)
        3. ETUALAN KEHYS-KUVA (KORISTEELLINEN)
    """
    
    # LASKE TERVEYSPROSENTTI
    ratio = 0.0
    if max_hp is not None and max_hp > 0:
        ratio = max(0.0, min(float(cur_hp) / float(max_hp), 1.0))
    
    # PIIRTÄÄ TAUSTA/KEHYS-TAUSTA
    if imgs is not None and imgs.get('bg') is not None:
        bg = pygame.transform.smoothscale(imgs['bg'], (frame_size_x, frame_size_y))
        screen.blit(bg, (frame_x, frame_y))
    else:
        bg_s = pygame.Surface((frame_size_x, frame_size_y), pygame.SRCALPHA)
        bg_s.fill((20, 20, 20, 255))
        screen.blit(bg_s, (frame_x, frame_y))
    
    # PIIRTÄÄ KIINTEÄ TERVEYSTÄYTTÖ (PROSENTTI-MUKAAN)
    fill_w = max(0, int(fill_size_x * ratio))
    if fill_w > 0:
        s = pygame.Surface((fill_w, fill_size_y))
        s.fill((tint[0], tint[1], tint[2]))
        screen.blit(s, (fill_x, fill_y))
    
    # PIIRTÄÄ ETUALAN KEHYS-KUVA (KORISTEELLINEN)
    if imgs is not None and imgs.get('fg') is not None:
        frame = imgs['fg']
        frame_s = pygame.transform.smoothscale(frame, (frame_size_x, frame_size_y))
        screen.blit(frame_s, (frame_x, frame_y))
"""
================================================================================
                         UI.PY - PELIRAYKAISU MODUULI
================================================================================
KUVAUS:
    TÄMÄ MODUULI HALLITSEE KAIKEN HUD-NÄYTÖNTÄ JA TERVEYSPALKKIEN PIIRTÄMISEN
    PELIN AIKANA. SISÄLTÄÄ FUNKTIOT BOOST-MITTARILLE, ARMOR-MITTARILLE,
    DAMAGE-NÄYTÖLLE, PELAAJAN TERVEYSPALKEILLE JA VIHOLLISTEN TERVEYSPALKEILLE.
    
PÄÄFUNKTIOT:
    - draw_hud()                   : PIIRTÄÄ PÄÄASIALLISEN HUD-NÄYTÖN
    - draw_boost_bar()             : PIIRTÄÄ BOOST-ENERGIAMITTARIN
    - draw_armor_bar()             : PIIRTÄÄ PANSSARIN MITTARIN
    - draw_damage_display()        : PIIRTÄÄ DAMAGE-TASON NÄYTÖN
    - draw_enemy_health_bar()      : PIIRTÄÄ VIHOLLISEN TERVEYSPALKIN
    - draw_death_overlay()         : PIIRTÄÄ KUOLEMA-NÄYTÖN
    - load_health_bar_images()     : LATAA TERVEYSPALKKIEN KUVAT LEVYLTÄ
    
MODUULIN GLOBAALIT MUUTTUJAT:
    - ENEMY_BAR_IMGS               : VÄLIMUISTI VIHOLLISTEN PALKKIEN KUVILLE
    
================================================================================
"""

import pygame
import os


# ============================================================================
# PÄÄASIALLINEN HUD-NÄYTTÖ - PIIRTÄÄ PELAAJAN TERVEYSTILAN JA KAIKKI MITTARIT
# ============================================================================
def draw_hud(screen, X, Y, player, lives, health_imgs, HUD_POS):
    """
    PIIRTÄÄ KOKO HUD-NÄYTÖN: ELÄMÄT, BOOST-MITTARI, ARMOR-MITTARI JA DMG-TASO.
    
    PARAMETRIT:
        screen      : PYGAME SURFACE JOHON PIIRRETÄÄN
        X, Y        : NÄYTÖN LEVEYS JA KORKEUS
        player      : PELAAJA-OBJEKTI (SISÄLTÄÄ HEALTH, ARMOR, DMG_BONUS)
        lives       : ELÄMIEN MÄÄRÄ (VARALLINEN ARVO)
        health_imgs : SANAKIRJA TERVEYSPALKKIEN KUVILLE {0-5}
        HUD_POS     : SIJAINTI HUD-NÄYTTÖÖN NÄYTÖLLÄ (x, y)
    
    LOGIIKKA:
        1. TARKISTA KUINKA MONTA ELÄMÄÄ PELAAJALLA ON
        2. VALITSE OIKEA KUVA TERVEYSTILÄN MUKAAN
        3. PIIRTÄÄ KAIKKI MITTARIT: BOOST, ARMOR, DMG
    """
    
    # ALUSTA FONTTI HUD-TEKSTILLE
    font = pygame.font.SysFont('Arial', 24)
    
    # HAKE PELAAJAN NYKYINEN TERVEYSTILA
    cur_health = lives
    max_h = 5
    
    if hasattr(player, 'health'):
        cur_health = int(max(0, min(player.health, getattr(player, 'max_health', 5))))
        max_h = int(getattr(player, 'max_health', 5))
    
    # VALITSE OIKEA HUD-KUVA TERVEYSTILAN PERUSTEELLA
    hud_img = None
    if isinstance(health_imgs, dict):
        if max_h > 0 and max_h != 5:
            slot = int(round((cur_health / max_h) * 5))
        else:
            slot = int(max(0, min(cur_health, 5)))
        hud_img = health_imgs.get(slot)
    
    # PIIRTÄÄ KUVAN TAI TEKSTIN (JOS KUVA EI SAATAVILLA)
    if hud_img is not None:
        screen.blit(hud_img, HUD_POS)
    else:
        # PIIRTÄÄ TEKSTILLÄ JOS KUVAA EI OLE
        lives_text = font.render(f"Elämät: {cur_health}", True, (255, 255, 255))
        screen.blit(lives_text, (X - 200, 10))
    
    # PIIRTÄÄ BOOST-MITTARI
    draw_boost_bar(screen, player, X, Y)
    
    # PIIRTÄÄ ARMOR-MITTARI
    draw_armor_bar(screen, player, X, Y)
    
    # PIIRTÄÄ DMG-NÄYTTÖ
    draw_damage_display(screen, player, X, Y)


# ============================================================================
# BOOST-ENERGIAMITTARI - NÄYTTÄÄ BOOST-TILAN JA LATAUSPROSENTTI
# ============================================================================
    if not hasattr(player, 'boost_energy'):
        return
    
    # Mittarin parametrit
    bar_width = 200
    bar_height = 20
    bar_x = 20
    bar_y = Y - 40
    border_thickness = 2
    
    # Värit
    color_bg = (50, 50, 50)  # Harmaa tausta
    color_charging = (100, 150, 255)  # Sininen ladatessa
    color_active = (255, 200, 0)  # Keltainen aktiivinen
    color_border = (255, 255, 255)  # Valkoinen kehys
    
    # Hae boost-energia parametrit
    boost_energy = getattr(player, 'boost_energy', 0.0)
    boost_max_energy = getattr(player, 'boost_max_energy', 3.0)
    boost_active = getattr(player, 'boost_active', False)
    
    # Laske energia-prosentti
    if boost_max_energy > 0:
        progress = boost_energy / boost_max_energy
    else:
        progress = 0.0
    
    # Valitse väri riippuen boost-tilasta
    if boost_active:
        fill_color = color_active  # Keltainen kun käytössä
    else:
        fill_color = color_charging  # Sininen kun ladataan
    
    # Rajoita progress 0-1 välille
    progress = max(0.0, min(1.0, progress))
    
    # Piirrä tausta
    pygame.draw.rect(screen, color_bg, (bar_x, bar_y, bar_width, bar_height))
    
    # Piirrä täyttö
    fill_width = int(bar_width * progress)
    if fill_width > 0:
        pygame.draw.rect(screen, fill_color, (bar_x, bar_y, fill_width, bar_height))
    
    # Piirrä kehys
    pygame.draw.rect(screen, color_border, (bar_x, bar_y, bar_width, bar_height), border_thickness)
    
    # Piirrä teksti
    font = pygame.font.SysFont('Arial', 14)
    boost_is_full = (abs(boost_energy - boost_max_energy) < 0.01)
    boost_depleted = getattr(player, 'boost_depleted', False)
    
    if boost_active:
        text = f"BOOST: {boost_energy:.1f}s"
        text_color = (255, 200, 0)
    elif boost_depleted:
        # Boost on loppunut kokonaan - näytä latausprosentti
        text = f"RECHARGING: {boost_energy:.1f}s"
        text_color = (255, 100, 100)  # Punainen lataustilanteessa
    elif boost_is_full:
        text = "BOOST READY! (Shift)"
        text_color = (100, 255, 100)  # Vihreä valmiina
    else:
        text = f"CHARGING: {boost_energy:.1f}s"
        text_color = (100, 150, 255)  # Sininen lataus
    
    text_surf = font.render(text, True, text_color)
    screen.blit(text_surf, (bar_x + 5, bar_y - 25))


def draw_armor_bar(screen, player, X, Y):
    """Piirtää armor-mittarin näytölle"""
    if not hasattr(player, 'armor'):
        return
    
    # Mittarin parametrit
    bar_width = 200
    bar_height = 20
    bar_x = 20
    bar_y = Y - 70  # Boost-mittarin alle
    max_armor = 10
    border_thickness = 2
    
    # Värit
    color_bg = (50, 50, 50)  # Harmaa tausta
    color_armor = (100, 150, 200)  # Sininen
    color_border = (255, 255, 255)  # Valkoinen kehys
    
    armor = getattr(player, 'armor', 0)
    
    # Laske armor-prosentti
    if max_armor > 0:
        progress = min(armor / max_armor, 1.0)
    else:
        progress = 0.0
    
    # Piirrä tausta
    pygame.draw.rect(screen, color_bg, (bar_x, bar_y, bar_width, bar_height))
    
    # Piirrä täyttö - punainen kun broken, sininen muutoin
    fill_color = (100, 150, 200) if armor > 0 else (255, 0, 0)  # Punainen kun nolla
    fill_width = int(bar_width * progress)
    if fill_width > 0:
        pygame.draw.rect(screen, fill_color, (bar_x, bar_y, fill_width, bar_height))
    
    # Piirrä kehys
    pygame.draw.rect(screen, color_border, (bar_x, bar_y, bar_width, bar_height), border_thickness)
    
    # Piirrä teksti
    font = pygame.font.SysFont('Arial', 14)
    if armor <= 0 and max_armor > 0:
        text = "ARMOR BROKEN!"
        text_color = (255, 50, 50)  # Punainen varoitus
    else:
        text = f"ARMOR: {armor:.0f}/{max_armor}"
        text_color = (100, 150, 200) if armor > 0 else (255, 100, 100)
    text_surf = font.render(text, True, text_color)
    screen.blit(text_surf, (bar_x + 5, bar_y - 25))


def draw_damage_display(screen, player, X, Y):
    """Näyttää pelaajan DMG tason (tasot 1-3)"""
    if not player:
        return
    
    # Hae damage_bonus
    damage_bonus = getattr(player, 'damage_bonus', 0)
    
    # Laske nykyinen DMG (Base 1 + 0.5 per bonus, max 3)
    base_dmg = 1.0
    current_dmg = min(3.0, base_dmg + (damage_bonus * 0.5))
    
    # Määritä taso (1-3)
    if current_dmg <= 1.0:
        dmg_level = 1
        dmg_color = (100, 255, 100)  # Vihreä - heikko
    elif current_dmg <= 2.0:
        dmg_level = 2
        dmg_color = (255, 200, 100)  # Oranssi - normaali
    else:
        dmg_level = 3
        dmg_color = (255, 100, 100)  # Punainen - vahva
    
    # Piirrä teksti
    font = pygame.font.SysFont('Arial', 16, bold=True)
    dmg_text = f"DMG: {current_dmg:.1f} (Tier {dmg_level})"
    text_surf = font.render(dmg_text, True, dmg_color)
    
    # Paikka oikeassa yläkulmassa (vierekkäin muiden mittareiden kanssa)
    display_x = X - 300
    display_y = Y - 100
    screen.blit(text_surf, (display_x, display_y))


def load_health_bar_images(base_dir):
    """Load health bar images from a folder. Returns dict with 'bg' and 'fg' Surfaces.
    Expects files like *background*.png and *foreground*.png in `base_dir`.
    """
    import os
    imgs = {'bg': None, 'fg': None}
    try:
        # prefer explicit names if present
        for name in os.listdir(base_dir):
            ln = name.lower()
            path = os.path.join(base_dir, name)
            if 'background' in ln and imgs['bg'] is None:
                imgs['bg'] = pygame.image.load(path).convert_alpha()
            if 'foreground' in ln and imgs['fg'] is None:
                imgs['fg'] = pygame.image.load(path).convert_alpha()
    except Exception:
        return imgs
    return imgs


# Module-level cache for enemy bar images
ENEMY_BAR_IMGS = None


def init_enemy_health_bars(project_root=None):
    """Initialize module-level enemy health bar images.
    If project_root is None, use the current file's directory as base.
    """
    global ENEMY_BAR_IMGS
    import os
    if project_root is None:
        project_root = os.path.dirname(__file__)
    base = os.path.join(project_root, 'images', 'enemy_health_bars_2.0', 'enemy_health_bars_2.0')
    ENEMY_BAR_IMGS = load_health_bar_images(base)
    return ENEMY_BAR_IMGS


def get_enemy_bar_images():
    global ENEMY_BAR_IMGS
    return ENEMY_BAR_IMGS


def draw_enemy_health_bar(screen, x, y, width, height, cur_hp, max_hp, imgs, tint=(255,0,0)):
    """Draw a health bar at (x,y) with given size using loaded imgs dict.
    `imgs` should have 'bg' and 'fg' Surfaces (either or both optional).
    The foreground will be tinted to `tint` color and cropped according to hp ratio.
    """
    ratio = 0.0
    try:
        ratio = max(0.0, min(float(cur_hp) / float(max_hp), 1.0)) if max_hp > 0 else 0.0
    except Exception:
        ratio = 0.0

    # Draw background (stretched) with a small outer padding so the
    # decorative foreground/frame can sit outside the fill area.
    pad = max(6, int(min(width, height) * 0.12))
    total_w = width + pad * 2
    total_h = height + pad * 2
    bx = x - pad
    by = y - pad
    if imgs and imgs.get('bg'):
        try:
            bg = pygame.transform.smoothscale(imgs['bg'], (total_w, total_h))
            screen.blit(bg, (bx, by))
        except Exception:
            pass
    else:
        # simple dark background bar with padding
        bg_s = pygame.Surface((total_w, total_h), pygame.SRCALPHA)
        bg_s.fill((20, 20, 20, 220))
        screen.blit(bg_s, (bx, by))

    # Prepare foreground: tint and crop according to ratio
    # Draw a solid (opaque) foreground fill for current HP.
    # Using a plain filled rect ensures the bar appears solid (no transparency).
    try:
        fill_w = max(0, int(width * ratio))
        if fill_w > 0:
            s = pygame.Surface((fill_w, height))
            s.fill((tint[0], tint[1], tint[2]))
            screen.blit(s, (x, y))
    except Exception:
        # Fallback: plain opaque fill
        fill_w = max(0, int(width * ratio))
        if fill_w > 0:
            s = pygame.Surface((fill_w, height))
            s.fill((tint[0], tint[1], tint[2]))
            screen.blit(s, (x, y))
    else:
        # draw plain opaque colored fill
        fill_w = max(0, int(width * ratio))
        if fill_w > 0:
            s = pygame.Surface((fill_w, height))
            s.fill((tint[0], tint[1], tint[2]))
            screen.blit(s, (x, y))

    # Draw decorative foreground/frame on top if provided (scaled to padded size).
    try:
        if imgs and imgs.get('fg'):
            frame = imgs['fg']
            frame_s = pygame.transform.smoothscale(frame, (total_w, total_h))
            screen.blit(frame_s, (bx, by))
    except Exception:
        pass



def draw_death_overlay(screen, X, Y, health_imgs, player, lives):
    """Draw a semi-opaque death overlay, a large centered empty-health graphic (if available)
    and return the Restart/Quit button rects for the caller to use in an event loop.
    """
    overlay = pygame.Surface((X, Y))
    overlay.set_alpha(220)
    overlay.fill((10, 10, 10))
    screen.blit(overlay, (0, 0))

    screen_rect = screen.get_rect()
    cx, cy = screen_rect.center

    # Try to draw large empty-health graphic if player's slot is empty
    large_rect = None
    try:
        cur_health = player.health if hasattr(player, 'health') else lives
        max_h = int(getattr(player, 'max_health', 5)) if hasattr(player, 'health') else 5
        if max_h > 0 and max_h != 5:
            slot = int(round((cur_health / max_h) * 5))
        else:
            slot = int(max(0, min(int(cur_health), 5)))

        if slot == 0 and isinstance(health_imgs, dict) and health_imgs.get(0):
            hud_img = health_imgs.get(0)
            sw, sh = hud_img.get_size()
            max_w = int(X * 0.8)
            max_h = int(Y * 0.6)
            scale = min(max_w / sw, max_h / sh, 1.0)
            large_w = max(1, int(sw * scale))
            large_h = max(1, int(sh * scale))
            large_img = pygame.transform.scale(hud_img, (large_w, large_h))
            large_rect = large_img.get_rect(center=(cx, cy - 40))
            screen.blit(large_img, large_rect.topleft)
    except Exception:
        large_rect = None

    font_large = pygame.font.SysFont('Arial', 48)
    font_small = pygame.font.SysFont('Arial', 28)
    title = font_large.render("YOU DIED", True, (220, 80, 80))
    if large_rect:
        title_rect = title.get_rect(center=(cx, large_rect.top - 40))
    else:
        title_rect = title.get_rect(center=(cx, cy - 140))
    screen.blit(title, title_rect.topleft)

    btn_w, btn_h = 320, 64
    restart_btn = pygame.Rect(0, 0, btn_w, btn_h)
    quit_btn = pygame.Rect(0, 0, btn_w, btn_h)
    if large_rect:
        restart_btn.center = (cx, large_rect.bottom + btn_h // 2 + 24)
        quit_btn.center = (cx, large_rect.bottom + btn_h // 2 + 24 + btn_h + 12)
    else:
        restart_btn.center = (cx, cy)
        quit_btn.center = (cx, cy + btn_h + 16)

    pygame.draw.rect(screen, (70, 150, 70), restart_btn)
    pygame.draw.rect(screen, (150, 70, 70), quit_btn)

    restart_label = font_small.render("Restart", True, (255, 255, 255))
    quit_label = font_small.render("Quit", True, (255, 255, 255))
    screen.blit(restart_label, restart_label.get_rect(center=restart_btn.center).topleft)
    screen.blit(quit_label, quit_label.get_rect(center=quit_btn.center).topleft)

    pygame.display.update()
    return restart_btn, quit_btn


def draw_healthbar_custom(screen,
                          fill_size_x, fill_size_y,
                          fill_x, fill_y,
                          frame_size_x, frame_size_y,
                          frame_x, frame_y,
                          cur_hp, max_hp,
                          imgs=None,
                          tint=(255, 0, 0)):
    """Simple single-call healthbar.

    Parameters correspond to the simple names you requested:
    - HealthFILL size x, size y   -> fill_size_x, fill_size_y
    - HealthFILL place x, place y  -> fill_x, fill_y
    - HealthFRAME size x, size y   -> frame_size_x, frame_size_y
    - HealthFRAME place x, place y -> frame_x, frame_y

    This draws, in order: background/frame-bg (if available),
    a solid opaque fill (cropped by HP ratio) at the fill rect,
    then the decorative frame image on top (if available).
    """
    try:
        ratio = 0.0
        if max_hp and max_hp > 0:
            ratio = max(0.0, min(float(cur_hp) / float(max_hp), 1.0))
    except Exception:
        ratio = 0.0

    # Draw background/frame background (scaled to frame size) if available
    try:
        if imgs and imgs.get('bg'):
            bg = pygame.transform.smoothscale(imgs['bg'], (frame_size_x, frame_size_y))
            screen.blit(bg, (frame_x, frame_y))
        else:
            bg_s = pygame.Surface((frame_size_x, frame_size_y), pygame.SRCALPHA)
            bg_s.fill((20, 20, 20, 255))
            screen.blit(bg_s, (frame_x, frame_y))
    except Exception:
        pass

    # Draw solid fill (opaque) cropped by ratio at provided fill rect
    try:
        fill_w = max(0, int(fill_size_x * ratio))
        if fill_w > 0:
            s = pygame.Surface((fill_w, fill_size_y))
            s.fill((tint[0], tint[1], tint[2]))
            screen.blit(s, (fill_x, fill_y))
    except Exception:
        pass

    # Draw decorative frame overlay (scaled to frame size) if available
    try:
        if imgs and imgs.get('fg'):
            frame = imgs['fg']
            frame_s = pygame.transform.smoothscale(frame, (frame_size_x, frame_size_y))
            screen.blit(frame_s, (frame_x, frame_y))
    except Exception:
        pass
