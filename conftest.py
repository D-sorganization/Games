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
    "get_init",
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


class MockRect:
    def __init__(self, x, y, width, height):
        """Initialize MockRect with position and dimensions."""
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.top = y
        self.left = x
        self.bottom = y + height
        self.right = x + width
        self.center = (x + width // 2, y + height // 2)
        self.topleft = (x, y)
        self.topright = (x + width, y)
        self.bottomleft = (x, y + height)
        self.bottomright = (x + width, y + height)

    def collidepoint(self, pos):
        """Return True if pos (x, y) falls within this rect's bounds."""
        px, py = pos
        return self.left <= px <= self.right and self.top <= py <= self.bottom

    def copy(self):
        """Return a copy of this MockRect with the same bounds."""
        return MockRect(self.x, self.y, self.width, self.height)

    def __repr__(self):
        """Return a human-readable string representation of this MockRect."""
        return f"<rect({self.x}, {self.y}, {self.width}, {self.height})>"


_pg.Rect = MockRect  # type: ignore[attr-defined]
_pg.Color = MagicMock  # type: ignore[attr-defined]
_pg.SRCALPHA = 65536  # type: ignore[attr-defined]

# pygame.error is the base exception class raised by pygame functions.
# It must be a real exception type so that ``except pygame.error:`` works.


class _PygameError(RuntimeError):
    """Stand-in for ``pygame.error`` in the test-fake module."""


_pg.error = _PygameError  # type: ignore[attr-defined]

# Event types
_pg.QUIT = 256  # type: ignore[attr-defined]
_pg.KEYDOWN = 768  # type: ignore[attr-defined]
_pg.KEYUP = 769  # type: ignore[attr-defined]
_pg.MOUSEBUTTONDOWN = 1025  # type: ignore[attr-defined]
_pg.MOUSEBUTTONUP = 1026  # type: ignore[attr-defined]
_pg.MOUSEMOTION = 1024  # type: ignore[attr-defined]
_pg.JOYAXISMOTION = 1536  # type: ignore[attr-defined]
_pg.JOYBUTTONDOWN = 1539  # type: ignore[attr-defined]
_pg.JOYBUTTONUP = 1540  # type: ignore[attr-defined]
_pg.VIDEORESIZE = 65281  # type: ignore[attr-defined]

# Key constants — letters
for _i, _letter in enumerate("abcdefghijklmnopqrstuvwxyz"):
    setattr(_pg, f"K_{_letter}", 97 + _i)

# Key constants — digits
for _d in range(10):
    setattr(_pg, f"K_{_d}", 48 + _d)

# Key constants — special keys
_KEY_SPECIALS = {
    "K_ESCAPE": 27,
    "K_RETURN": 13,
    "K_SPACE": 32,
    "K_TAB": 9,
    "K_BACKSPACE": 8,
    "K_DELETE": 127,
    "K_UP": 273,
    "K_DOWN": 274,
    "K_RIGHT": 275,
    "K_LEFT": 276,
    "K_INSERT": 277,
    "K_HOME": 278,
    "K_END": 279,
    "K_PAGEUP": 280,
    "K_PAGEDOWN": 281,
    "K_F1": 282,
    "K_F2": 283,
    "K_F3": 284,
    "K_F4": 285,
    "K_F5": 286,
    "K_F6": 287,
    "K_F7": 288,
    "K_F8": 289,
    "K_F9": 290,
    "K_F10": 291,
    "K_F11": 292,
    "K_F12": 293,
    "K_LSHIFT": 304,
    "K_RSHIFT": 303,
    "K_LCTRL": 306,
    "K_RCTRL": 305,
    "K_LALT": 308,
    "K_RALT": 307,
    "K_MINUS": 45,
    "K_EQUALS": 61,
    "K_PLUS": 270,
}
for _k, _v in _KEY_SPECIALS.items():
    setattr(_pg, _k, _v)

# Mouse button constants
_pg.BUTTON_LEFT = 1  # type: ignore[attr-defined]
_pg.BUTTON_MIDDLE = 2  # type: ignore[attr-defined]
_pg.BUTTON_RIGHT = 3  # type: ignore[attr-defined]

# Display flag constants (real pygame values; needed when Game.__init__ uses them)
_pg.SCALED = 512  # type: ignore[attr-defined]
_pg.RESIZABLE = 16  # type: ignore[attr-defined]
_pg.NOFRAME = 32  # type: ignore[attr-defined]
_pg.FULLSCREEN = 1  # type: ignore[attr-defined]
_pg.HWSURFACE = 2  # type: ignore[attr-defined]
_pg.DOUBLEBUF = 4  # type: ignore[attr-defined]
_pg.HIDDEN = 32768  # type: ignore[attr-defined]

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
_pg.event.set_grab = MagicMock()  # type: ignore[attr-defined]
_pg.event.get_grab = MagicMock(return_value=False)  # type: ignore[attr-defined]

# joystick helpers
_pg.joystick.init = MagicMock()  # type: ignore[attr-defined]
_pg.joystick.get_count = MagicMock(return_value=0)  # type: ignore[attr-defined]

# key helpers
_pg.key.get_pressed = MagicMock(  # type: ignore[attr-defined]
    return_value=[False] * 512,
)
_pg.key.name = MagicMock(return_value="unknown")  # type: ignore[attr-defined]

# math helpers (Vector2)
_pg.math.Vector2 = MagicMock  # type: ignore[attr-defined]

# mixer extras
_pg.mixer.pre_init = MagicMock()  # type: ignore[attr-defined]
_pg.mixer.set_num_channels = MagicMock()  # type: ignore[attr-defined]
_pg.mixer.pause = MagicMock()  # type: ignore[attr-defined]
_pg.mixer.unpause = MagicMock()  # type: ignore[attr-defined]

# mouse helpers
_pg.mouse.get_pos = MagicMock(return_value=(0, 0))  # type: ignore[attr-defined]
_pg.mouse.get_rel = MagicMock(return_value=(0, 0))  # type: ignore[attr-defined]
_pg.mouse.set_visible = MagicMock()  # type: ignore[attr-defined]
_pg.mouse.get_pressed = MagicMock(return_value=(False, False, False))  # type: ignore[attr-defined]

# image helpers
_pg.image.load = MagicMock(return_value=MagicMock())  # type: ignore[attr-defined]

# transform helpers
_pg.transform.scale = MagicMock(  # type: ignore[attr-defined]
    return_value=MagicMock(),
)
_pg.transform.rotate = MagicMock(  # type: ignore[attr-defined]
    return_value=MagicMock(),
)
_pg.transform.smoothscale = MagicMock(  # type: ignore[attr-defined]
    return_value=MagicMock(),
)

sys.modules["pygame"] = _pg
