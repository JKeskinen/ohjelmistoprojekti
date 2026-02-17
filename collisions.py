import random
import pygame

SPATIAL_GRID_SIZE = 64

class SpatialHash:
    def __init__(self, cell_size=SPATIAL_GRID_SIZE):
        self.cell_size = int(cell_size)
        self.grid = {}
        self.items = set()

    def rebuild(self):
        self.grid = {}
        for item in self.items:
            self.insert(item)

    def insert(self, entity):
        self.items.add(entity)
        for cell in self._rect_cells(entity.rect):
            items = self.grid.get(cell)
            if items is None:
                self.grid[cell] = [entity]
            else:
                items.append(entity)

    def _rect_cells(self, rect):
        x1, y1 = rect.topleft
        x1 //= self.cell_size
        y1 //= self.cell_size
        x2, y2 = rect.bottomright
        x2 = x2 // self.cell_size + 1
        y2 = y2 // self.cell_size + 1
        from itertools import product
        return product(range(x1, x2), range(y1, y2))

    def query(self, rect):
        items = set()
        for cell in self._rect_cells(rect):
            items.update(self.grid.get(cell, ()))
        return items


def _get_pos(entity):
    try:
        return pygame.Vector2(entity.pos)
    except Exception:
        return pygame.Vector2(entity.rect.center)


def _set_pos(entity, v):
    try:
        entity.pos = pygame.Vector2(v)
        entity.rect.center = (int(entity.pos.x), int(entity.pos.y))
    except Exception:
        try:
            entity.rect.center = (int(v.x), int(v.y))
        except Exception:
            pass


def _get_vel(entity):
    try:
        return pygame.Vector2(entity.vel)
    except Exception:
        try:
            return pygame.Vector2(entity.velocity)
        except Exception:
            return pygame.Vector2(0, 0)


def _set_vel(entity, v):
    try:
        entity.vel = pygame.Vector2(v)
    except Exception:
        try:
            entity.velocity = pygame.Vector2(v)
        except Exception:
            pass


def apply_impact(a, b, elasticity=0.8):
    pa = _get_pos(a)
    pb = _get_pos(b)
    normal = pb - pa
    dist = normal.length()
    if dist < 1e-6:
        normal = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
        dist = normal.length() or 1.0
    normal /= dist

    va = _get_vel(a)
    vb = _get_vel(b)

    ma = float(getattr(a, 'mass', 1.0))
    mb = float(getattr(b, 'mass', 1.0))

    rel = normal.dot(va) * ma - normal.dot(vb) * mb
    rel *= elasticity

    if ma > 0:
        va -= normal * (rel / ma)
    if mb > 0:
        vb += normal * (rel / mb)

    _set_vel(a, va)
    _set_vel(b, vb)


def separate(a, b, frac=0.66):
    pa = _get_pos(a)
    pb = _get_pos(b)
    ab = pa - pb
    sep = ab.length()
    minsep = (getattr(a, 'radius', max(a.rect.width, a.rect.height) * 0.5) +
             getattr(b, 'radius', max(b.rect.width, b.rect.height) * 0.5))
    overlap = minsep - sep
    if overlap <= 0:
        return True
    if sep < 1e-6:
        ab = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
        sep = ab.length() or 1.0
    ab /= sep
    ma = float(getattr(a, 'mass', 1.0))
    mb = float(getattr(b, 'mass', 1.0))
    masses = max(1e-6, ma + mb)

    ov = overlap * frac
    a_new = pa + ab * (ov * (mb / masses))
    b_new = pb - ab * (ov * (ma / masses))

    _set_pos(a, a_new)
    _set_pos(b, b_new)
    return False
