import os
import pygame

# Simple planets helper: load a decorative planet sprite, handle rotation and drawing.
# Public API:
#   init_planet(project_root=None, filename=None, height=96, rot_speed_deg=36.0)
#   update_planet(dt_ms)
#   draw_planet_above_frame(screen, frame_x, frame_y, frame_w, frame_h, gap=6)

_sprite_orig = None
_sprite_base = None
_angle = 0.0
_rot_speed = 36.0


def init_planet(project_root=None, filename=None, height=96, rot_speed_deg=36.0):
    global _sprite_base, _sprite_orig, _rot_speed, _angle
    _angle = 0.0
    _rot_speed = float(rot_speed_deg)
    if project_root is None:
        project_root = os.path.dirname(__file__)

    # default folder for terrestrial sprites
    planet_dir = os.path.join(project_root, 'images', 'SBS - 2D Planet Pack 2 - Shaded 512x512',
                              'Large Planets 512x512', 'Solid', 'Terrestrial')
    try:
        if filename:
            path = os.path.join(planet_dir, filename)
        else:
            preferred = os.path.join(planet_dir, 'Terrestrial_03-512x512.png')
            if os.path.exists(preferred):
                path = preferred
            else:
                names = [n for n in os.listdir(planet_dir) if n.lower().endswith('.png')]
                if not names:
                    _sprite_base = None
                    return
                path = os.path.join(planet_dir, names[0])

        surf = pygame.image.load(path).convert_alpha()
        _sprite_orig = surf.copy()
        # scale to requested height preserving aspect
        if surf.get_height() != height:
            pw = max(1, int(surf.get_width() * (height / surf.get_height())))
            surf = pygame.transform.smoothscale(surf, (pw, height))
        _sprite_base = surf
    except Exception:
        _sprite_base = None
        _sprite_orig = None


def update_planet(dt_ms):
    global _angle
    dt = max(0.0, dt_ms) / 1000.0
    _angle = (_angle + _rot_speed * dt) % 360.0


def draw_planet_above_frame(screen, frame_x, frame_y, frame_w, frame_h, gap=6):
    """Draw rotating planet centered horizontally above the given frame rect.
    If no sprite is loaded this does nothing.
    """
    if _sprite_base is None:
        return
    try:
        # rotate the base sprite by current angle (negate for pygame coordinates)
        surf = pygame.transform.rotozoom(_sprite_base, -_angle, 1.0)
        px = frame_x + (frame_w - surf.get_width()) // 2
        py = frame_y - surf.get_height() - gap
        screen.blit(surf, (px, py))
    except Exception:
        pass


def draw_planet_screen(screen, screen_x, screen_y, height=320, gap=0):
    """Draw a large rotating planet at screen coordinates (screen_x, screen_y) as center.
    - `height` controls the display height in pixels (scales original image).
    - `screen_x, screen_y` are the center position in screen pixels.
    """
    if _sprite_orig is None:
        return
    try:
        # scale original to requested height preserving aspect
        base = _sprite_orig
        if base.get_height() != height:
            pw = max(1, int(base.get_width() * (height / base.get_height())))
            base = pygame.transform.smoothscale(base, (pw, height))
        surf = pygame.transform.rotozoom(base, -_angle, 1.0)
        r = surf.get_rect(center=(screen_x, screen_y - gap))
        screen.blit(surf, r.topleft)
    except Exception:
        pass


def draw_planet_world(screen, camera_x, camera_y, world_x, world_y, height=320):
    """Draw planet at world coordinates (world_x, world_y). Converts to screen coords using camera.
    Centers the planet at the given world position.
    """
    if _sprite_orig is None:
        return
    try:
        base = _sprite_orig
        if base.get_height() != height:
            pw = max(1, int(base.get_width() * (height / base.get_height())))
            base = pygame.transform.smoothscale(base, (pw, height))
        surf = pygame.transform.rotozoom(base, -_angle, 1.0)
        screen_x = int(world_x - camera_x)
        screen_y = int(world_y - camera_y)
        r = surf.get_rect(center=(screen_x, screen_y))
        screen.blit(surf, r.topleft)
    except Exception:
        pass
