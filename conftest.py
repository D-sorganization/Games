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


class MockRect:
    def __init__(self, x, y, width, height):
        """Initialize MockRect with position and dimensions."""
        self._x = int(x)
        self._y = int(y)
        self.width = int(width)
        self.height = int(height)

    # -- coordinate properties (keep left/right/top/bottom in sync) --

    @property
    def x(self):
        """Left edge x coordinate."""
        return self._x

    @x.setter
    def x(self, value):
        """Set left edge x coordinate."""
        self._x = int(value)

    @property
    def y(self):
        """Top edge y coordinate."""
        return self._y

    @y.setter
    def y(self, value):
        """Set top edge y coordinate."""
        self._y = int(value)

    @property
    def left(self):
        """Left edge."""
        return self._x

    @left.setter
    def left(self, value):
        """Set left edge."""
        self._x = int(value)

    @property
    def top(self):
        """Top edge."""
        return self._y

    @top.setter
    def top(self, value):
        """Set top edge."""
        self._y = int(value)

    @property
    def right(self):
        """Right edge."""
        return self._x + self.width

    @right.setter
    def right(self, value):
        """Set right edge (moves rect)."""
        self._x = int(value) - self.width

    @property
    def bottom(self):
        """Bottom edge."""
        return self._y + self.height

    @bottom.setter
    def bottom(self, value):
        """Set bottom edge (moves rect)."""
        self._y = int(value) - self.height

    @property
    def center(self):
        """Center point."""
        return (self._x + self.width // 2, self._y + self.height // 2)

    @center.setter
    def center(self, value):
        """Set center (moves rect)."""
        cx, cy = value
        self._x = int(cx) - self.width // 2
        self._y = int(cy) - self.height // 2

    @property
    def topleft(self):
        """Top-left corner."""
        return (self._x, self._y)

    @property
    def topright(self):
        """Top-right corner."""
        return (self._x + self.width, self._y)

    @property
    def bottomleft(self):
        """Bottom-left corner."""
        return (self._x, self._y + self.height)

    @property
    def bottomright(self):
        """Bottom-right corner."""
        return (self._x + self.width, self._y + self.height)

    def collidepoint(self, pos):
        """Return True if pos (x, y) falls within this rect's bounds."""
        px, py = pos
        return self.left <= px <= self.right and self.top <= py <= self.bottom

    def colliderect(self, other):
        """Return True if this rect overlaps with *other*."""
        return (
            self.left < other.right
            and self.right > other.left
            and self.top < other.bottom
            and self.bottom > other.top
        )

    def copy(self):
        """Return a copy of this MockRect with the same bounds."""
        return MockRect(self.x, self.y, self.width, self.height)

    def inflate(self, dx, dy):
        """Return a new rect expanded by dx, dy."""
        return MockRect(
            self.x - dx // 2,
            self.y - dy // 2,
            self.width + dx,
            self.height + dy,
        )

    def move(self, dx, dy):
        """Return a new rect moved by dx, dy."""
        return MockRect(self.x + dx, self.y + dy, self.width, self.height)

    def clip(self, other):
        """Return the intersection of this rect and other."""
        x = max(self.left, other.left)
        y = max(self.top, other.top)
        w = max(0, min(self.right, other.right) - x)
        h = max(0, min(self.bottom, other.bottom) - y)
        return MockRect(x, y, w, h)

    def union(self, other):
        """Return the union bounding rect."""
        x = min(self.left, other.left)
        y = min(self.top, other.top)
        w = max(self.right, other.right) - x
        h = max(self.bottom, other.bottom) - y
        return MockRect(x, y, w, h)

    def __repr__(self):
        """Return a human-readable string representation of this MockRect."""
        return f"<rect({self.x}, {self.y}, {self.width}, {self.height})>"


_pg.Rect = MockRect  # type: ignore[attr-defined]


class _MockSurface(MagicMock):
    """MagicMock subclass that pre-wires common Surface methods."""

    def __init__(self, *args, **kwargs):
        """Initialise with pre-wired methods."""
        super().__init__(*args, **kwargs)
        self.fill = MagicMock()
        self.get_width = MagicMock(return_value=800)
        self.get_height = MagicMock(return_value=600)
        self.set_alpha = MagicMock()
        self.set_at = MagicMock()
        self.blit = MagicMock()
        self.convert_alpha = MagicMock(return_value=self)
        self.get_rect = MagicMock(return_value=MockRect(0, 0, 800, 600))


_pg.Surface = _MockSurface  # type: ignore[attr-defined]
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

# draw helpers
_pg.draw.rect = MagicMock()  # type: ignore[attr-defined]
_pg.draw.circle = MagicMock()  # type: ignore[attr-defined]
_pg.draw.line = MagicMock()  # type: ignore[attr-defined]
_pg.draw.polygon = MagicMock()  # type: ignore[attr-defined]
_pg.draw.lines = MagicMock()  # type: ignore[attr-defined]
_pg.draw.ellipse = MagicMock()  # type: ignore[attr-defined]

# display helpers
_pg.display.set_mode = MagicMock(return_value=_MockSurface())  # type: ignore[attr-defined]
_pg.display.flip = MagicMock()  # type: ignore[attr-defined]
_pg.display.update = MagicMock()  # type: ignore[attr-defined]
_pg.display.set_caption = MagicMock()  # type: ignore[attr-defined]
_pg.display.Info = MagicMock()  # type: ignore[attr-defined]
_pg.display.init = MagicMock()  # type: ignore[attr-defined]

# mixer helpers
_pg.mixer.init = MagicMock()  # type: ignore[attr-defined]
_pg.mixer.get_init = MagicMock(return_value=False)  # type: ignore[attr-defined]
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


class _MockVector2:
    """Minimal Vector2 stub for headless tests."""

    def __init__(self, *args):
        """Accept (x, y) or ((x, y),) or (scalar,)."""
        if len(args) == 2:
            self.x, self.y = float(args[0]), float(args[1])
        elif len(args) == 1:
            arg = args[0]
            if hasattr(arg, "__iter__"):
                vals = list(arg)
                self.x, self.y = float(vals[0]), float(vals[1])
            else:
                self.x = self.y = float(arg)
        else:
            self.x = self.y = 0.0

    def copy(self):
        """Return a copy of this vector."""
        return _MockVector2(self.x, self.y)

    def __iadd__(self, other):
        """In-place addition."""
        self.x += other.x
        self.y += other.y
        return self

    def __imul__(self, scalar):
        """In-place scalar multiplication."""
        self.x *= scalar
        self.y *= scalar
        return self

    def __mul__(self, scalar):
        """Scalar multiplication."""
        return _MockVector2(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar):
        """Reverse scalar multiplication."""
        return _MockVector2(self.x * scalar, self.y * scalar)

    def length(self):
        """Return vector length."""
        import math

        return math.hypot(self.x, self.y)

    def distance_to(self, other):
        """Return distance to another vector."""
        import math

        return math.hypot(self.x - other.x, self.y - other.y)

    def rotate(self, angle):
        """Return a new vector rotated by angle degrees."""
        import math

        rad = math.radians(angle)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        return _MockVector2(
            self.x * cos_a - self.y * sin_a,
            self.x * sin_a + self.y * cos_a,
        )

    def normalize(self):
        """Return a normalized copy (unit vector)."""
        import math

        mag = math.hypot(self.x, self.y)
        if mag == 0:
            return _MockVector2(0, 0)
        return _MockVector2(self.x / mag, self.y / mag)

    def angle_to(self, other):
        """Return angle in degrees to other vector."""
        import math

        return math.degrees(math.atan2(other.y - self.y, other.x - self.x))

    def __iter__(self):
        """Support tuple unpacking."""
        yield self.x
        yield self.y

    def __repr__(self):
        """String form."""
        return f"<Vector2({self.x}, {self.y})>"


_pg.math.Vector2 = _MockVector2  # type: ignore[attr-defined]

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
# sync trigger 2026-04-10
