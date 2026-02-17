import pygame


def draw_hud(screen, X, Y, player, lives, health_imgs, HUD_POS):
    font = pygame.font.SysFont('Arial', 24)
    try:
        cur_health = lives
        max_h = 5
        if hasattr(player, 'health'):
            cur_health = int(max(0, min(player.health, getattr(player, 'max_health', 5))))
            max_h = int(getattr(player, 'max_health', 5))

        hud_img = None
        if isinstance(health_imgs, dict):
            if max_h > 0 and max_h != 5:
                slot = int(round((cur_health / max_h) * 5))
            else:
                slot = int(max(0, min(cur_health, 5)))
            hud_img = health_imgs.get(slot)

        if hud_img:
            try:
                pos = HUD_POS
                screen.blit(hud_img, pos)
            except Exception:
                screen.blit(hud_img, HUD_POS)
        else:
            lives_text = font.render(f"Elämät: {cur_health}", True, (255, 255, 255))
            screen.blit(lives_text, (X - 200, 10))
    except Exception:
        lives_text = font.render(f"Elämät: {lives}", True, (255, 255, 255))
        screen.blit(lives_text, (X - 200, 10))


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
