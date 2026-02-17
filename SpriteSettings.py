import os
import pygame


class SpriteSettings:
    """Load commonly used enemy sprites into lists for easy assignment to enemies.

    Defaults expect the repository structure shown in the project and will
    load assets for a single ship (default 'Ship2').
    """

    def __init__(self, base_path: str = 'enemy-sprite', ship: str = 'Ship2'):
        self.base = base_path
        self.ship = ship

        self.ship_frames: list[pygame.Surface] = []
        self.exhaust_turbo: list[pygame.Surface] = []
        self.exhaust_normal: list[pygame.Surface] = []
        self.shot_frames: list[pygame.Surface] = []

        # call load when pygame is ready (pygame.init() must be called first)
        # We do not auto-initialize pygame here to keep this module pure.

    def _load_images_from(self, path: str) -> list:
        """Return list of Surfaces from a folder or a single-file path.

        If `path` is a file, returns a single-element list. If it's a folder,
        returns all .png files inside (sorted).
        """
        if not os.path.exists(path):
            return []

        if os.path.isfile(path):
            try:
                return [pygame.image.load(path).convert_alpha()]
            except Exception:
                return []

        # directory: walk immediate descendants and collect pngs
        images = []
        for dirpath, _, files in os.walk(path):
            pngs = sorted(f for f in files if f.lower().endswith('.png'))
            for f in pngs:
                full = os.path.join(dirpath, f)
                try:
                    images.append(pygame.image.load(full).convert_alpha())
                except Exception:
                    continue
        return images

    def load_all(self):
        """Load the ship sprite(s), exhaust (turbo/normal) and shot sprites.

        Paths used (relative to `base_path`):
        - PNG_Parts&Spriter_Animation/<Ship>/<Ship>/  (ship frames)
        - PNG_Parts&Spriter_Animation/<Ship>/Exhaust/Turbo_flight/Exhaust1
        - PNG_Parts&Spriter_Animation/<Ship>/Exhaust/Normal_flight/Exhaust1
        - PNG_Animations/Shots/Shot4
        """
        ship_folder = os.path.join(self.base, 'PNG_Parts&Spriter_Animation', self.ship, self.ship)
        self.ship_frames = self._load_images_from(ship_folder)

        turbo_folder = os.path.join(self.base, 'PNG_Parts&Spriter_Animation', self.ship, 'Exhaust', 'Turbo_flight', 'Exhaust1')
        self.exhaust_turbo = self._load_images_from(turbo_folder)

        normal_folder = os.path.join(self.base, 'PNG_Parts&Spriter_Animation', self.ship, 'Exhaust', 'Normal_flight', 'Exhaust1')
        self.exhaust_normal = self._load_images_from(normal_folder)

        # check both PNG_Animations and PNG_Parts&Spriter_Animation locations for Shot4
        candidate_shot_paths = [
            os.path.join(self.base, 'PNG_Animations', 'Shots', 'Shot4'),
            os.path.join(self.base, 'PNG_Parts&Spriter_Animation', 'Shots', 'Shot4'),
            os.path.join(self.base, 'PNG_Parts&Spriter_Animation', 'Shot4'),
        ]

        # collect shot subfolders into categories: start, flight, explode
        shots = {'start': [], 'flight': [], 'explode': []}
        for shots_folder in candidate_shot_paths:
            if not os.path.isdir(shots_folder):
                continue
            for dirpath, dirnames, files in os.walk(shots_folder):
                name = os.path.basename(dirpath).lower()
                pngs = sorted(f for f in files if f.lower().endswith('.png'))
                imgs = []
                for f in pngs:
                    full = os.path.join(dirpath, f)
                    try:
                        imgs.append(pygame.image.load(full).convert_alpha())
                    except Exception:
                        continue
                if not imgs:
                    continue
                if 'start' in name or 'shotstart' in name:
                    shots['start'].extend(imgs)
                elif 'exp' in name or 'expl' in name:
                    shots['explode'].extend(imgs)
                else:
                    # default to flight/asset frames
                    shots['flight'].extend(imgs)

        self.shot_frames = shots

        # If a specific Shot4 flight asset exists in the parts folder, prefer it
        preferred = os.path.join(self.base, 'PNG_Parts&Spriter_Animation', 'Shots', 'Shot4', 'shot4', 'shot4_asset', '000_shot4_asset_0.png')
        if os.path.isfile(preferred):
            try:
                img = pygame.image.load(preferred).convert_alpha()
                shots['flight'] = [img]
                self.shot_frames = shots
            except Exception:
                pass

        return {
            'ship': self.ship_frames,
            'exhaust_turbo': self.exhaust_turbo,
            'exhaust_normal': self.exhaust_normal,
            'shots': self.shot_frames,
        }


__all__ = ['SpriteSettings']
