# Games Repository — DBC / DRY / TDD Quality Assessment

**Assessment Date:** 2026-02-13
**Repository:** Games
**Total Source Files:** 117 Python files (src/)
**Total Functions:** 770
**Overall Grade: 3.7/10**

---

## Executive Summary

The Games repository has **massive cross-game code duplication** as its defining quality issue. Three FPS games (Duum, Force_Field, Zombie_Survival) share 58–88% identical code across their core modules (`game.py`, `ui_renderer.py`, `bot.py`, `constants.py`), yet each maintains its own copy. A `shared/` module with 27 files and 15+ base classes exists but the `Game` class — the largest and most duplicated component — has **no base class at all**. There is **zero DbC infrastructure** (no contracts, no preconditions, no postconditions). Test coverage is minimal with 107 tests across 22 test files for 117 source modules, and **no test isolation practices** (0 fixtures, 0 mocks, 0 parametrization). The codebase has 1,118 magic number instances and 31 functions exceeding 100 lines.

---

## 1. Design by Contract (DbC) — Grade: 1.5/10

### 1.1 Infrastructure (0/10)

**No contract infrastructure exists.** There is:

- No `contracts.py` module
- No `@precondition` / `@postcondition` / `@invariant` decorators
- No validation utility library

### 1.2 Adoption Metrics

| Metric                              | Count | Assessment                |
| ----------------------------------- | ----- | ------------------------- |
| `@precondition` decorators in src/  | 0     | Non-existent              |
| `@postcondition` decorators in src/ | 0     | Non-existent              |
| `@invariant` decorators in src/     | 0     | Non-existent              |
| `raise` statements (non-test)       | 3     | Virtually no error guards |
| `assert` statements (non-test)      | 168   | Over-reliance on asserts  |
| `validate_*` functions              | 0     | Non-existent              |
| `isinstance` checks                 | 7     | Minimal type checking     |

### 1.3 Critical Gaps

**High-Risk APIs Without Any Defensive Coding:**

- `Game.__init__()` — Accepts screen/clock/player params with no validation (121–116 lines across 3 games)
- `update_game()` — Largest functions in codebase (285–334 lines) with zero preconditions
- `start_level()` — 167–189 lines, no validation on level data structures
- `check_shot_hit()` — 160–228 lines, geometry calculations with no bounds checking
- `Raycaster._draw_single_sprite()` — 232 lines with unguarded trigonometric operations

**168 assert statements are used instead of proper contracts.** Asserts are stripped in production (`python -O`), providing false safety.

### 1.4 Scoring Breakdown

| Component                 | Score      | Notes                               |
| ------------------------- | ---------- | ----------------------------------- |
| Infrastructure            | 0/10       | No contract library exists          |
| Adoption (preconditions)  | 0/10       | Zero uses                           |
| Adoption (postconditions) | 0/10       | Zero uses                           |
| Adoption (invariants)     | 0/10       | Zero uses                           |
| Validation utilities      | 0/10       | No validate\_\* functions           |
| Defensive coding (raise)  | 1/10       | Only 3 raise statements in 770 fns  |
| Type hints                | 4/10       | 279 of 639 function defs have hints |
| Docstrings                | 8/10       | 88% coverage — a bright spot        |
| **Average**               | **1.5/10** |                                     |

---

## 2. Don't Repeat Yourself (DRY) — Grade: 3.0/10

### 2.1 Cross-Game Code Cloning (CRITICAL — The #1 Issue)

The three FPS games are near-clones of each other:

| Comparison                             | Similarity | Lines Duplicated (~) |
| -------------------------------------- | ---------- | -------------------- |
| Duum `game.py` vs Zombie_Survival      | **87.6%**  | ~1,460 lines         |
| Duum `ui_renderer.py` vs Zombie_Surv.  | **93.5%**  | ~725 lines           |
| Duum `bot.py` vs Zombie_Survival       | **90.1%**  | ~321 lines           |
| Duum `constants.py` vs Zombie_Survival | **92.4%**  | ~422 lines           |
| Duum `game.py` vs Force_Field          | **58.0%**  | ~860 lines           |
| Duum `ui_renderer.py` vs Force_Field   | **67.1%**  | ~555 lines           |

**Estimated duplicated code: ~4,300+ lines that should be shared utilities or base class methods.**

### 2.2 Missing Game Base Class

The `shared/` module provides base classes for `Player`, `Bot`, `Map`, `Projectile`, `UIRenderer`, `InputManager`, and `SoundManager` — but **NOT for the `Game` class itself**, which is the single largest duplicated component:

| Game            | `Game` class lines | `update_game()` lines |
| --------------- | ------------------ | --------------------- |
| Duum            | 1,669              | 291                   |
| Force_Field     | 1,302              | 334                   |
| Zombie_Survival | 1,661              | 285                   |

16 function names appear in 3+ games identically: `update_game`, `start_level`, `check_shot_hit`, `handle_game_events`, `respawn_player`, `add_bot`, `add_projectile`, `get_nearby_bots`, `take_damage`, `explode_laser`, `explode_plasma`, `explode_rocket`, `has_line_of_sight`, `update_bots`, `reset`, `run`.

### 2.3 Monolith Functions

| Function                    | Lines | File           | Issue                          |
| --------------------------- | ----- | -------------- | ------------------------------ |
| `update_game` (Force_Field) | 334   | game.py        | God function — game loop logic |
| `update_game` (Duum)        | 291   | game.py        | Near-copy                      |
| `update_game` (Zombie_S)    | 285   | game.py        | Near-copy                      |
| `update` (ZS bot)           | 243   | bot.py         | AI state machine in one func   |
| `_draw_single_sprite`       | 232   | raycaster.py   | Rendering monolith             |
| `check_shot_hit` (Duum)     | 228   | game.py        | Collision detection monolith   |
| `render_hud` (Duum)         | 198   | ui_renderer.py | UI rendering monolith          |
| `_render_walls_vectorized`  | 188   | raycaster.py   | Raycasting monolith            |
| `start_level` (FF)          | 189   | game.py        | Level initialization monolith  |

**Total functions >50 lines: 100 | Total functions >100 lines: 31**

### 2.4 Other DRY Violations

| Metric                          | Count | Target          |
| ------------------------------- | ----- | --------------- |
| Magic number instances          | 1,118 | < 50            |
| `sys.path` manipulations        | 13    | 0               |
| `print()` in production code    | 4     | 0 (use logging) |
| Duplicate `import pygame` lines | 54    | Centralize      |
| `_render_intro_slide` copies    | 3     | 1 (in base)     |
| `render_hud` copies             | 3     | 1 (in base)     |

### 2.5 Scoring Breakdown

| Component                   | Score      | Notes                             |
| --------------------------- | ---------- | --------------------------------- |
| Cross-game deduplication    | 1/10       | 4,300+ lines duplicated across 3  |
| Game base class             | 0/10       | Missing entirely                  |
| Module decomposition        | 3/10       | 3 files >1,300 lines each         |
| Function granularity        | 3/10       | 31 functions >100 lines           |
| Magic number hygiene        | 2/10       | 1,118 bare numeric literals       |
| Shared infrastructure reuse | 6/10       | Good shared/ + base classes exist |
| Constants organization      | 4/10       | 92% duplicate across games        |
| **Average**                 | **3.0/10** |                                   |

---

## 3. Test-Driven Development (TDD) — Grade: 2.5/10

### 3.1 Coverage Metrics

| Metric                    | Count                         | Assessment             |
| ------------------------- | ----------------------------- | ---------------------- |
| Test files                | 22                            | Low density            |
| Test functions            | 107                           | Very low               |
| Source modules (non-init) | 117                           | Large surface area     |
| Test-to-source ratio      | 0.19 files, 0.91 tests/module | Far below target (3:1) |
| Mock/Patch usage          | 2                             | Virtually zero         |
| Fixture usage             | 0                             | Zero                   |
| Parametrize usage         | 0                             | Zero                   |

### 3.2 Test Coverage by Game

| Game             | Source Files | Test Files | Test Functions | Coverage |
| ---------------- | ------------ | ---------- | -------------- | -------- |
| Duum             | 20           | 5          | ~20            | Poor     |
| Force_Field      | 23           | 5          | ~20            | Poor     |
| Zombie_Survival  | 20           | 5          | ~20            | Poor     |
| Wizard_of_Wor    | 15           | 5          | ~20            | Moderate |
| Tetris           | 8            | 1          | ~10            | Poor     |
| Peanut_Butter_P. | 3            | 1          | ~5             | Moderate |
| **shared/**      | **27**       | **0**      | **0**          | **ZERO** |

**The most critical module (`shared/`) with 27 files has ZERO tests.** This includes the raycaster (1,436 lines), player_base (282 lines), and texture_generator (200+ lines).

### 3.3 Test Quality Issues

1. **No fixtures** — Every test likely recreates objects from scratch
2. **No mocking** (2 instances) — Tests may require pygame initialization, making them fragile
3. **No parametrized tests** — Suggests copy-paste test patterns
4. **No property-based testing** — No Hypothesis for math-heavy code (raycasting, collision)
5. **No coverage CI enforcement** — No minimum coverage gates
6. **`sys.path` hacks in 5 test files** — Tests use fragile path manipulation
7. **Duplicate test patterns** — `test_entity_manager.py`, `test_fps.py`, `test_utils.py` appear in multiple games (likely near-identical)

### 3.4 Scoring Breakdown

| Component             | Score      | Notes                               |
| --------------------- | ---------- | ----------------------------------- |
| Coverage breadth      | 2/10       | shared/ module entirely untested    |
| Coverage depth        | 2/10       | 107 tests for 770 functions         |
| Test isolation        | 1/10       | 0 fixtures, 2 mocks                 |
| Test reuse (fixtures) | 0/10       | Zero fixtures                       |
| Test efficiency       | 1/10       | No parametrize, no property testing |
| CI enforcement        | 3/10       | Tests run but no coverage gate      |
| Test DRY              | 3/10       | Duplicate test files across games   |
| **Average**           | **2.5/10** |                                     |

---

## 4. Remediation Priority

### Phase 1: Foundation — Create GameBase & Contract Infrastructure (3-5 days)

| #   | Action                                                                                                                       | Impact | Effort |
| --- | ---------------------------------------------------------------------------------------------------------------------------- | ------ | ------ |
| 1   | **Create `shared/game_base.py`** with `GameBase` class                                                                       | DRY +3 | High   |
|     | Extract common: `update_game`, `start_level`, `check_shot_hit`, `handle_game_events`, `respawn_player` into template methods |        |        |
| 2   | **Create `shared/contracts.py`** with `@precondition`, `@postcondition`, `@invariant`                                        | DbC +2 | Low    |
| 3   | **Extract shared constants** — merge 92% identical constants into `shared/constants.py` with per-game overrides              | DRY +1 | Medium |
| 4   | **Add tests for `shared/` module** — raycaster, player_base, map_base, utils                                                 | TDD +2 | Medium |

### Phase 2: Decomposition — Break Monoliths (3-5 days)

| #   | Action                                                    | Impact   | Effort |
| --- | --------------------------------------------------------- | -------- | ------ |
| 5   | Decompose `update_game` (334→<50 lines) into sub-methods  | DRY +1   | Medium |
| 6   | Decompose `_draw_single_sprite` (232 lines) in raycaster  | DRY +0.5 | Medium |
| 7   | Add `@precondition` to 20 critical game APIs              | DbC +2   | Medium |
| 8   | Extract 1,118 magic numbers into named constants          | DRY +1   | Medium |
| 9   | Remove 13 `sys.path` hacks — use proper package structure | DRY +0.5 | Low    |

### Phase 3: Test Maturity (3-5 days)

| #   | Action                                                        | Impact   | Effort |
| --- | ------------------------------------------------------------- | -------- | ------ |
| 10  | Add pytest fixtures for pygame initialization                 | TDD +1   | Low    |
| 11  | Add parametrized tests for collision/raycasting math          | TDD +1   | Medium |
| 12  | Introduce pytest-cov with 60% minimum gate                    | TDD +1   | Low    |
| 13  | Deduplicate test files — share test base across FPS games     | TDD +0.5 | Medium |
| 14  | Add `@invariant` to 5+ core classes (Player, Bot, Game state) | DbC +1   | Medium |

### Phase 4: Strategic (1-2 weeks)

| #   | Action                                                       | Impact   | Effort |
| --- | ------------------------------------------------------------ | -------- | ------ |
| 15  | Refactor FPS games to use `GameBase` inheritance             | DRY +2   | High   |
| 16  | Merge duplicate `ui_renderer.py` logic into `UIRendererBase` | DRY +1   | High   |
| 17  | Add property-based tests (Hypothesis) for math modules       | TDD +1   | Medium |
| 18  | Replace 168 assert statements with proper contracts          | DbC +1.5 | Medium |

---

## 5. Target Grades After Remediation

| Dimension   | Current | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
| ----------- | ------- | ------- | ------- | ------- | ------- |
| DbC         | 1.5     | 3.5     | 5.5     | 6.5     | 8.0     |
| DRY         | 3.0     | 7.0     | 8.0     | 8.5     | 9.0     |
| TDD         | 2.5     | 4.5     | 5.0     | 7.0     | 8.0     |
| **Overall** | **3.7** | **5.7** | **6.8** | **7.7** | **8.5** |

---

## 6. Top 5 Highest-Impact Actions (Recommended Starting Point)

1. **Create `GameBase` class** — Eliminates ~4,300 lines of duplication across 3 FPS games
2. **Add `shared/contracts.py`** — Establishes contract infrastructure for the entire repo
3. **Test the `shared/` module** — 27 files with 0 tests; this is the shared foundation everything depends on
4. **Merge constants** — 92% identical constants.py files across 3 games
5. **Decompose `update_game`** — 3 copies of a 285-334 line function; each should be <50 lines

---

_Assessment conducted 2026-02-13 using AST analysis, difflib similarity scoring, grep heuristics, and manual code review._
