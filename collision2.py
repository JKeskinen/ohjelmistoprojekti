import pygame
import pymunk
from pymunk.vec2d import Vec2d


class PymunkCollisionManager:
    """Lightweight manager to use pymunk for sprites collision handling.

    - Keeps a mapping between sprite-like objects and pymunk shapes.
    - Provides helpers to create circle shapes and register collision handlers
      that receive the original sprite objects.
    Note: this intentionally keeps coordinates identical to pygame (top-left origin).
    If you prefer to convert y-axis, adapt conversion in `add_circle`/`sync_positions`.
    """

    def __init__(self):
        self.space = pymunk.Space()
        self.space.gravity = (0.0, 0.0)
        self.shape_to_entity = {}
        self.entity_to_shape = {}

    def clear(self):
        self.space = pymunk.Space()
        self.space.gravity = (0.0, 0.0)
        self.shape_to_entity.clear()
        self.entity_to_shape.clear()

    def add_circle(self, entity, radius=None, mass=1.0, collision_type=1, body_type=pymunk.Body.DYNAMIC):
        """Create a pymunk circle body/shape and associate it with `entity`.

        `entity` must have a `.rect` attribute (pygame.Rect). We set the shape._entity
        so collision handlers can retrieve the original sprite object.
        Returns (body, shape).
        """
        if radius is None:
            radius = max(entity.rect.width, entity.rect.height) * 0.5

        moment = pymunk.moment_for_circle(mass, 0, radius)
        body = pymunk.Body(mass, moment, body_type=body_type)
        body.position = Vec2d(entity.rect.centerx, entity.rect.centery)

        shape = pymunk.Circle(body, radius)
        shape.collision_type = collision_type
        shape.elasticity = 0.0

        self.space.add(body, shape)

        # keep mappings
        shape._entity = entity
        self.shape_to_entity[shape] = entity
        self.entity_to_shape[entity] = shape
        return body, shape

    def remove_entity(self, entity):
        shape = self.entity_to_shape.pop(entity, None)
        if shape is None:
            return
        try:
            body = shape.body
            self.space.remove(shape, body)
        except Exception:
            pass
        self.shape_to_entity.pop(shape, None)

    def step(self, dt):
        """Advance physics and then sync positions back to sprites."""
        self.space.step(dt)
        self.sync_positions()

    def sync_positions(self):
        """Copy body positions to sprite `pos`/`rect.center` if present."""
        for shape, entity in list(self.shape_to_entity.items()):
            try:
                p = shape.body.position
                # Keep same top-left origin as pygame (no Y flip here)
                x, y = float(p.x), float(p.y)
                try:
                    entity.pos = pygame.Vector2(x, y)
                except Exception:
                    pass
                try:
                    entity.rect.center = (int(x), int(y))
                except Exception:
                    pass
            except Exception:
                pass

    def get_entity_shape(self, entity):
        return self.entity_to_shape.get(entity)

    def get_body(self, entity):
        s = self.get_entity_shape(entity)
        return getattr(s, 'body', None)

    def add_collision_handler(self, type_a, type_b, begin=None, pre_solve=None, post_solve=None, separate=None):
        """Register pymunk collision handlers. Callbacks receive (a_entity, b_entity, arbiter, space, data)."""
        h = self.space.add_collision_handler(type_a, type_b)

        def _wrap(cb):
            if cb is None:
                return None

            def _fn(arbiter, space, data):
                a_shape, b_shape = arbiter.shapes[:2]
                a_ent = getattr(a_shape, '_entity', None)
                b_ent = getattr(b_shape, '_entity', None)
                try:
                    return cb(a_ent, b_ent, arbiter, space, data)
                except Exception:
                    # swallow exceptions to avoid breaking the physics step
                    return True

            return _fn

        h.begin = _wrap(begin)
        h.pre_solve = _wrap(pre_solve)
        h.post_solve = _wrap(post_solve)
        h.separate = _wrap(separate)

        return h


# Example helper callback
def simple_player_enemy_begin(player_ent, enemy_ent, arbiter, space, data):
    """Default begin callback: reduce player health and remove enemy shape."""
    try:
        if hasattr(player_ent, 'health'):
            player_ent.health = max(0, int(player_ent.health) - 1)
            try:
                if hasattr(player_ent, 'trigger_hit_animation'):
                    player_ent.trigger_hit_animation()
            except Exception:
                pass
        # Optionally mark enemy for removal
        if enemy_ent is not None:
            # remove body/shape via manager stored in data
            mgr = data.get('manager')
            try:
                mgr.remove_entity(enemy_ent)
            except Exception:
                pass
    except Exception:
        pass
    return True
