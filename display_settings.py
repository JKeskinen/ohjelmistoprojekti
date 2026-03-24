import json
import os
from copy import deepcopy


SETTINGS_FILE = "display_settings.json"

DEFAULT_DISPLAY_SETTINGS = {
    "width": 1280,
    "height": 720,
    "fullscreen": False,
}

SUPPORTED_RESOLUTIONS = [
    (1024, 576),
    (1280, 720),
    (1366, 768),
    (1600, 900),
    (1920, 1080),
]


def _settings_path():
    return os.path.join(os.path.dirname(__file__), SETTINGS_FILE)


def _closest_resolution(width, height):
    best = SUPPORTED_RESOLUTIONS[0]
    best_score = abs(best[0] - width) + abs(best[1] - height)
    for resolution in SUPPORTED_RESOLUTIONS[1:]:
        score = abs(resolution[0] - width) + abs(resolution[1] - height)
        if score < best_score:
            best = resolution
            best_score = score
    return best


def normalize_display_settings(settings):
    data = deepcopy(DEFAULT_DISPLAY_SETTINGS)
    if isinstance(settings, dict):
        data.update(settings)

    try:
        width = int(data.get("width", DEFAULT_DISPLAY_SETTINGS["width"]))
    except Exception:
        width = DEFAULT_DISPLAY_SETTINGS["width"]

    try:
        height = int(data.get("height", DEFAULT_DISPLAY_SETTINGS["height"]))
    except Exception:
        height = DEFAULT_DISPLAY_SETTINGS["height"]

    width, height = _closest_resolution(width, height)
    fullscreen = bool(data.get("fullscreen", False))

    return {
        "width": width,
        "height": height,
        "fullscreen": fullscreen,
    }


def load_display_settings():
    path = _settings_path()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            loaded = json.load(fh)
    except FileNotFoundError:
        return deepcopy(DEFAULT_DISPLAY_SETTINGS)
    except Exception:
        return deepcopy(DEFAULT_DISPLAY_SETTINGS)

    return normalize_display_settings(loaded)


def save_display_settings(settings):
    path = _settings_path()
    normalized = normalize_display_settings(settings)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(normalized, fh, indent=2)


def resolution_to_label(width, height):
    return f"{int(width)}x{int(height)}"


def resolution_items():
    return [
        (resolution_to_label(width, height), resolution_to_label(width, height))
        for width, height in SUPPORTED_RESOLUTIONS
    ]


def parse_resolution_label(value):
    raw = str(value).strip().lower().replace(" ", "")
    if "x" not in raw:
        return DEFAULT_DISPLAY_SETTINGS["width"], DEFAULT_DISPLAY_SETTINGS["height"]

    parts = raw.split("x", 1)
    try:
        width = int(parts[0])
        height = int(parts[1])
    except Exception:
        return DEFAULT_DISPLAY_SETTINGS["width"], DEFAULT_DISPLAY_SETTINGS["height"]

    return _closest_resolution(width, height)
