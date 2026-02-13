# Games Repository — Quality Improvement Plan

**Created:** 2026-02-13
**Based on:** DBC/DRY/TDD Assessment (Grade: 3.7/10)
**Target Grade:** 8.5/10

---

## Strategy: "Extract, Contract, Test"

The Games repo has a **unique architectural opportunity**: three FPS games (Duum, Force_Field, Zombie_Survival) are 58-88% identical. Rather than fixing issues in each copy, we extract shared logic into `GameBase`, add contracts, and test the shared core once. This is a force multiplier — every fix applies to 3 games simultaneously.

---

## Wave 1: GameBase + Contracts Foundation (Highest Impact)

### 1.1 Create `shared/game_base.py`

Extract these functions (which are 87-93% identical across Duum/Zombie_Survival):

```
GameBase
├── __init__(screen, clock, player, ...)    # Shared initialization (~116 lines)
├── run()                                   # Main game loop
├── start_level(level_num)                  # Level setup (~170 lines)
├── update_game(dt)                         # Game update — template method (~290 lines)
│   ├── _update_projectiles(dt)             # Extracted sub-method
│   ├── _update_bots(dt)                    # Extracted sub-method
│   ├── _check_collisions()                 # Extracted sub-method
│   └── _update_game_state()                # Game-specific override point
├── handle_game_events(events)              # Event processing (~137 lines)
├── check_shot_hit(origin, direction, ...)  # Collision math (~160-228 lines)
├── respawn_player()                        # Player respawn logic
├── add_bot(bot_type, position)             # Bot spawning
├── add_projectile(weapon, origin, dir)     # Projectile creation
├── get_nearby_bots(position, radius)       # Spatial query
└── update_bots(dt)                         # Bot tick
```

**Per-game subclasses** override only what differs:

- `DuumGame(GameBase)` — portal mechanics, unique enemies
- `ForceFieldGame(GameBase)` — shield system, energy weapons
- `ZombieSurvivalGame(GameBase)` — survival waves, zombie AI

### 1.2 Create `shared/contracts.py`

```python
# Decorator-based contracts (same pattern as Tools repo)
@precondition(lambda self, dt: dt > 0, "dt must be positive")
@precondition(lambda self, dt: dt < 1.0, "dt must be < 1 second")
def update_game(self, dt: float) -> None: ...

@precondition(lambda self, level: level >= 1, "level must be >= 1")
def start_level(self, level: int) -> None: ...

@invariant(lambda self: self.player.health >= 0, "health cannot be negative")
class GameBase: ...
```

### 1.3 Merge Constants

Create `shared/constants.py` with the ~92% shared values:

```python
# shared/constants.py — Base game constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FOV = 60
RAY_COUNT = 320
# ... ~400 shared constants

# Per-game overrides in game_name/src/constants.py
from games.shared.constants import *  # noqa: F403
UNIQUE_ENEMY_HEALTH = 150  # Game-specific
```

---

## Wave 2: Function Decomposition + DbC Adoption

### 2.1 Break Down Monolith Functions

Target: Every function under 50 lines

| Function (before)     | Lines | After                                                   |
| --------------------- | ----- | ------------------------------------------------------- |
| `update_game`         | 334   | 6 sub-methods × ~55 lines each                          |
| `_draw_single_sprite` | 232   | `_prepare_sprite`, `_calculate_columns`, `_blit_sprite` |
| `check_shot_hit`      | 228   | `_cast_hit_ray`, `_check_entity_hit`, `_apply_damage`   |
| `render_hud`          | 198   | `_render_health`, `_render_ammo`, `_render_minimap`     |
| `start_level`         | 189   | `_create_map`, `_spawn_entities`, `_init_ui`            |

### 2.2 Add Preconditions to Critical APIs

Priority targets (20 APIs):

- All `GameBase` public methods
- `Raycaster.cast_rays()`, `_draw_single_sprite()`
- `PlayerBase.take_damage()`, `move()`
- `BotBase.update()`, `take_damage()`
- `MapBase.get_tile()`, `is_solid()`

### 2.3 Extract Magic Numbers

The 1,118 magic numbers should become named constants:

```python
# Before
if distance < 3.0 and enemy.health > 0:
    damage = 25 * (1.0 - distance / 3.0)

# After
if distance < MELEE_RANGE and enemy.health > MIN_HEALTH:
    damage = BASE_MELEE_DAMAGE * (1.0 - distance / MELEE_RANGE)
```

---

## Wave 3: Test Infrastructure

### 3.1 Test the Shared Module (Priority #1)

| Module                 | Lines | Test Priority | Focus Areas                     |
| ---------------------- | ----- | ------------- | ------------------------------- |
| `raycaster.py`         | 1,436 | CRITICAL      | Ray math, wall rendering        |
| `player_base.py`       | 282   | HIGH          | Movement, damage, health        |
| `map_base.py`          | ~200  | HIGH          | Tile access, collision          |
| `bot_base.py`          | ~150  | HIGH          | AI state, pathfinding           |
| `projectile_base.py`   | ~100  | MEDIUM        | Projectile lifecycle            |
| `utils.py`             | ~150  | MEDIUM        | `has_line_of_sight`, `try_move` |
| `texture_generator.py` | 200+  | LOW           | Visual correctness              |

### 3.2 Test Infrastructure

```python
# conftest.py — Shared fixtures
@pytest.fixture
def mock_screen():
    """Mock pygame screen for headless testing."""
    ...

@pytest.fixture
def sample_map():
    """A known-good map for testing."""
    ...

@pytest.fixture
def player(mock_screen, sample_map):
    """A fully initialized player for testing."""
    ...
```

### 3.3 Parametrized Tests for Math

```python
@pytest.mark.parametrize("origin,direction,expected", [
    ((5.0, 5.0), 0.0, (10.0, 5.0)),      # East
    ((5.0, 5.0), math.pi/2, (5.0, 10.0)), # North
    ((5.0, 5.0), math.pi, (0.0, 5.0)),    # West
])
def test_raycast_direction(origin, direction, expected):
    ...
```

---

## Estimated Timeline

| Wave | Duration | Grade Impact     |
| ---- | -------- | ---------------- |
| 1    | 3-5 days | 3.7 → 5.7 (+2.0) |
| 2    | 3-5 days | 5.7 → 6.8 (+1.1) |
| 3    | 3-5 days | 6.8 → 7.7 (+0.9) |
| Full | 2-3 wks  | 3.7 → 8.5 (+4.8) |

---

## Success Criteria

- [ ] `GameBase` class exists and is inherited by all 3 FPS games
- [ ] `shared/contracts.py` exists with `@precondition`, `@postcondition`, `@invariant`
- [ ] 20+ critical APIs have preconditions
- [ ] `shared/` module has >60% test coverage
- [ ] No function exceeds 100 lines
- [ ] Constants consolidated — <10% duplication between game-specific constants files
- [ ] Overall DBC/DRY/TDD grade ≥ 7.5/10
