import pygame
from Enemies.enemy import Enemy
from ui import get_enemy_bar_images, draw_healthbar_custom

# MODIFICATION NOTES:
# 2026-03-04 - Added optional `hitbox_size` and `hitbox_offset` parameters
# to `BossEnemy.__init__` so the collision rectangle can be tuned
# independently of the visual sprite. This fixes cases where the visual
# artwork is asymmetric or the sprite's pivot doesn't match the logical
# collision center. Passing `hitbox_size=(w,h)` will resize the boss's
# `rect` while preserving its center; `hitbox_offset=(dx,dy)` shifts the
# rect relative to the sprite center. The code also defensively re-centers
# the `rect` at spawn to ensure predictable placement.

class BossEnemy(Enemy):
    def __init__(self, image: pygame.Surface, world_rect: pygame.Rect,
                 hp: int = 10, enter_speed: float = 250, move_speed: float = 300,
                 hitbox_size: tuple | None = None, hitbox_offset: tuple = (0, 0)):
        
        # Spawn ylävasemmalta, hieman ruudun ulkopuolelta
        start_x = world_rect.left + image.get_width() // 2
        start_y = world_rect.top - image.get_height() // 2
        
        super().__init__(image, start_x, start_y)

        # Ensure rect is centred where we expect (defensive in case parent
        # behaviour changes). Also allow overriding the hitbox size/offset so
        # collision rect and visual sprite can be independently tuned.
        try:
            self.rect.center = (int(start_x), int(start_y))
        except Exception:
            pass

        # Optional hitbox override: size=(w,h) will resize the collision rect
        # while preserving centre; offset=(dx,dy) will shift the rect relative
        # to the sprite centre (useful when the visible sprite's artwork is
        # not symmetric).
        if hitbox_size is not None:
            try:
                c = self.rect.center
                w, h = int(hitbox_size[0]), int(hitbox_size[1])
                self.rect.size = (w, h)
                # apply offset after resizing
                dx, dy = int(hitbox_offset[0]), int(hitbox_offset[1])
                self.rect.center = (c[0] + dx, c[1] + dy)
            except Exception:
                pass

        self.world_rect = world_rect
        self.hp = hp
        self.max_hp = hp

        self.enter_speed = enter_speed
        self.move_speed = move_speed

        self.state = "entering"   # entering -> active
        self.vx = move_speed

        # Mihin kohtaan boss pysähtyy pystysuunnassa
        self.target_y = world_rect.top + 180

    def take_hit(self, amount=1):
        self.hp -= amount
        return self.hp <= 0

    def update(self, dt_ms, player=None, world_rect=None):
        dt = dt_ms / 1000.0

        if self.state == "entering":
            # Liikkuu alaspäin
            self.rect.y += int(self.enter_speed * dt)

            if self.rect.centery >= self.target_y:
                self.rect.centery = self.target_y
                self.state = "active"

        elif self.state == "active":
            # Liikkuu vasen-oikea
            self.rect.x += int(self.vx * dt)

            if self.rect.left <= self.world_rect.left:
                self.rect.left = self.world_rect.left
                self.vx *= -1

            if self.rect.right >= self.world_rect.right:
                self.rect.right = self.world_rect.right
                self.vx *= -1

    def draw_health_bar(self, screen: pygame.Surface, index: int = 0, margin: int = 16):
        """Draw this boss's stacked health bar in the left margin.

        - `index` selects vertical stack order (0 = top).
        - uses `get_enemy_bar_images()` and `draw_healthbar_custom()` from `ui`.
        """
        try:
            # frame size + padding
            frame_w, frame_h = 340, 56
            frame_x = margin
            frame_y = margin + index * (frame_h + 8)

            # derive an inner padding so the decorative frame can surround the fill
            pad = max(20, int(min(frame_w, frame_h) * 0.12))

            # mframe_w - pad * 2 = kehysleveys minus padding molemmilta puolilta, eli täytön "sisäleveys".
            # max(4, ...) varmistaa, että fill_w ei koskaan ole pienempi kuin 4 (turvaksi ettei leveys olisi nolla tai negatiivinen).
            # Sama logiikka fill_h varten korkeudelle.
            # Esimerkki: jos frame_w = 340 ja pad = 6, niin frame_w - pad*2 = 340 - 12 = 328, jolloin fill_w = max(4, 328) = 328.
            # Jos taas padding olisi liian suuri (esim. 200), lasku antaisi negatiivisen arvon ja max palauttaisi 4 niin ettei täyttö katoa.
            fill_w = max(4, frame_w - pad * 2)
            fill_h = max(4, frame_h - pad * 2)

            # center fill inside frame
            fill_x = frame_x + (frame_w - fill_w) // 2
            fill_y = frame_y + (frame_h - fill_h) // 2

            cur_hp = getattr(self, 'hp', getattr(self, 'health', getattr(self, 'HP', 0)))
            max_hp = getattr(self, 'max_hp', getattr(self, 'max_health', getattr(self, 'HP_MAX', cur_hp)))

            imgs = get_enemy_bar_images()
            draw_healthbar_custom(screen,
                                  fill_w, fill_h,
                                  fill_x, fill_y,
                                  frame_w, frame_h,
                                  frame_x, frame_y,
                                  cur_hp, max_hp,
                                  imgs=imgs,
                                  tint=(255, 40, 40))
        except Exception:
            pass