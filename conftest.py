"""Root conftest: inject fake pygame to prevent SDL hangs in CI/headless."""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock

# Build a completely fake pygame module tree so that the real C extension
# (which requires an SDL display) never loads.  This file is automatically
# picked up by pytest before any test is collected.

_pg = types.ModuleType("pygame")
_pg.__path__ = []  # type: ignore[attr-defined]  # make it look like a package

for _attr in (
    "init",
    "quit",
    "get_error",
    "get_sdl_version",
    "get_sdl_byteorder",
    "register_quit",
    "encode_string",
    "encode_file_path",
):
    setattr(_pg, _attr, MagicMock())

_SUB_NAMES = [
    "base",
    "constants",
    "rect",
    "rwobject",
    "surflock",
    "color",
    "bufferproxy",
    "math",
    "pixelcopy",
    "surface",
    "display",
    "draw",
    "event",
    "font",
    "image",
    "joystick",
    "key",
    "mixer",
    "mouse",
    "sprite",
    "time",
    "transform",
    "cursors",
    "mask",
    "pixelarray",
    "sndarray",
    "surfarray",
    "freetype",
    "gfxdraw",
    "locals",
    "mixer.music",
]

for _name in _SUB_NAMES:
    _mod = types.ModuleType(f"pygame.{_name}")
    sys.modules[f"pygame.{_name}"] = _mod

# Wire convenience attributes on the top-level fake module
_pg.display = sys.modules["pygame.display"]
_pg.draw = sys.modules["pygame.draw"]
_pg.event = sys.modules["pygame.event"]
_pg.font = sys.modules["pygame.font"]
_pg.image = sys.modules["pygame.image"]
_pg.joystick = sys.modules["pygame.joystick"]
_pg.key = sys.modules["pygame.key"]
_pg.math = sys.modules["pygame.math"]
_pg.mixer = sys.modules["pygame.mixer"]
_pg.mouse = sys.modules["pygame.mouse"]
_pg.sprite = sys.modules["pygame.sprite"]
_pg.time = sys.modules["pygame.time"]
_pg.transform = sys.modules["pygame.transform"]
_pg.locals = sys.modules["pygame.locals"]

# Common pygame top-level classes/constants
_pg.Surface = MagicMock  # type: ignore[attr-defined]
_pg.Rect = MagicMock  # type: ignore[attr-defined]
_pg.Color = MagicMock  # type: ignore[attr-defined]
_pg.QUIT = 256  # type: ignore[attr-defined]
_pg.KEYDOWN = 768  # type: ignore[attr-defined]
_pg.KEYUP = 769  # type: ignore[attr-defined]
_pg.K_ESCAPE = 27  # type: ignore[attr-defined]
_pg.MOUSEBUTTONDOWN = 1025  # type: ignore[attr-defined]
_pg.MOUSEMOTION = 1024  # type: ignore[attr-defined]
_pg.JOYAXISMOTION = 1536  # type: ignore[attr-defined]

# display helpers
_pg.display.set_mode = MagicMock(return_value=MagicMock())  # type: ignore[attr-defined]
_pg.display.flip = MagicMock()  # type: ignore[attr-defined]
_pg.display.update = MagicMock()  # type: ignore[attr-defined]
_pg.display.set_caption = MagicMock()  # type: ignore[attr-defined]
_pg.display.Info = MagicMock()  # type: ignore[attr-defined]
_pg.display.init = MagicMock()  # type: ignore[attr-defined]

# mixer helpers
_pg.mixer.init = MagicMock()  # type: ignore[attr-defined]
_pg.mixer.music = sys.modules["pygame.mixer.music"]  # type: ignore[attr-defined]
_pg.mixer.Sound = MagicMock()  # type: ignore[attr-defined]
_pg.mixer.quit = MagicMock()  # type: ignore[attr-defined]

# font helpers
_pg.font.init = MagicMock()  # type: ignore[attr-defined]
_pg.font.SysFont = MagicMock(  # type: ignore[attr-defined]
    return_value=MagicMock(render=MagicMock(return_value=MagicMock())),
)
_pg.font.Font = MagicMock(  # type: ignore[attr-defined]
    return_value=MagicMock(render=MagicMock(return_value=MagicMock())),
)

# time helpers
_pg.time.get_ticks = MagicMock(return_value=0)  # type: ignore[attr-defined]
_pg.time.Clock = MagicMock(  # type: ignore[attr-defined]
    return_value=MagicMock(),
)

# event helpers
_pg.event.get = MagicMock(return_value=[])  # type: ignore[attr-defined]

# joystick helpers
_pg.joystick.init = MagicMock()  # type: ignore[attr-defined]
_pg.joystick.get_count = MagicMock(return_value=0)  # type: ignore[attr-defined]

sys.modules["pygame"] = _pg
