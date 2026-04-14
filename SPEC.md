# SPEC.md — Repository Specification Document

## 1. Identity

| Field                   | Value                                                |
| ----------------------- | ---------------------------------------------------- |
| **Repository Name**     | `Games`                                              |
| **GitHub URL**          | `https://github.com/D-sorganization/Games`           |
| **Owner**               | D-sorganization                                      |
| **Primary Language(s)** | Python 3.10+ (Pygame), JavaScript (Three.js for web) |
| **License**             | MIT                                                  |
| **Current Version**     | N/A                                                  |
| **Spec Version**        | 1.1.26                                               |
| **Last Spec Update**    | 2026-04-12                                           |

## 2. Purpose & Mission

Games is Jules' unified gaming platform providing a collection of complete, playable games written in Python/Pygame and web-based technologies. It delivers a central launcher interface that orchestrates multiple game implementations (Force Field, Duum, Tetris, Wizard of Wor, Peanut Butter Panic, Zombie Survival, QuatGolf) with shared rendering infrastructure, consistent input handling, and comprehensive test coverage for both game-specific logic and cross-game rendering systems.

## 3. Goals & Non-Goals

### Goals

- Implement multiple complete, playable games spanning different genres (FPS, roguelike, puzzle, arcade, 3D)
- Provide unified launcher with game discovery, selection, and execution management
- Build shared rendering infrastructure supporting 2D rasterization and 3D geometric algorithms
- Achieve per-game test coverage with integration tests for central launcher
- Deliver consistent user experience across platform-native (Pygame) and web-based (Three.js) implementations
- Enable C++ performance optimization via ctypes bindings for compute-intensive algorithms
- Support headless testing on Linux via xvfb (X11 virtual framebuffer)

### Non-Goals

- Not a general-purpose game engine framework (single-purpose gaming platform)
- Not designed for game distribution, publishing, or monetization
- Not a game asset pipeline or art tool
- Not intended for commercial game development workflows

## 4. Architecture Overview

### System Context

Games is a standalone entertainment application within the D-sorganization fleet with no dependencies on other fleet repositories. It depends on Pygame 2.6.1 for core rendering and input, OpenCV for image processing, and optionally provides Three.js-based web game implementations. Three.js is not vendored in the source tree; any future browser-side usage should resolve the dependency externally. The system is self-contained with all game logic, shared utilities, and test infrastructure included.

### Module Map

```
Games/
├── src/games/                      # Main game implementations
│   ├── Force_Field/               # FPS with raycasting engine
│   │   ├── engine/                # Raycasting renderer and physics
│   │   ├── src/                   # Orchestration, loop dispatch, and runtime modules
│   │   ├── maps/                  # Level data
│   │   └── entities/              # Player, enemies, projectiles
│   ├── Duum/                       # Doom-inspired roguelike
│   │   ├── levels/                # Procedural level generation
│   │   ├── monsters/              # Enemy AI and behavior
│   │   └── weapons/               # Weapon systems
│   ├── Tetris/                    # Enhanced Tetris implementation
│   │   ├── pieces/                # Tetromino definitions and rotations
│   │   ├── board/                 # Game board state and logic
│   │   └── scoring/               # Scoring and level progression
│   ├── Wizard_of_Wor/             # Arcade game remake
│   │   ├── wizard_of_wor/         # Game package
│   │   │   ├── game.py            # WizardOfWorGame (thin orchestrator, SRP)
│   │   │   ├── render_mixin.py    # RenderMixin – all draw_* methods (SRP)
│   │   │   ├── audio_mixin.py     # AudioMixin + SoundBoard – audio wiring (SRP)
│   │   │   ├── collision_manager.py # CollisionManager – spatial-grid collision (SRP)
│   │   │   ├── dungeon.py         # Procedural maze generation
│   │   │   ├── enemy.py           # Enemy AI and patterns
│   │   │   ├── player.py          # Player entity
│   │   │   ├── bullet.py          # Projectile system
│   │   │   ├── radar.py           # HUD radar
│   │   │   └── effects.py         # Visual effect system
│   │   └── tests/                 # Per-component unit tests
│   ├── Peanut_Butter_Panic/       # Platformer game
│   │   ├── levels/                # Level design and tiling
│   │   ├── physics/               # Platform collision and gravity
│   │   └── enemies/               # Enemy types and patterns
│   ├── Zombie_Survival/           # Web-based 3D game
│   │   ├── client/                # Three.js client code (JavaScript)
│   │   ├── server/                # Python backend for multiplayer
│   │   └── models/                # 3D model definitions
│   ├── QuatGolf/                  # Quaternion-based golf game (in progress)
│   │   ├── physics/               # Quaternion rotation mechanics
│   │   ├── courses/               # Golf course definitions
│   │   └── ai/                    # AI player logic
│   └── shared/                    # Shared infrastructure
│       ├── renderers/             # Base rendering interfaces, color management
│       ├── cpp_bindings/          # ctypes bindings to C++ libraries
│       ├── geometry/              # Shared geometric algorithms
│       ├── input/                 # Input handling abstractions
│       └── config/                # Global game configuration
├── tests/                         # Comprehensive test suite
│   ├── unit/                      # Unit tests per game
│   ├── integration/               # Launcher and cross-game integration
│   ├── shared/                    # Shared infrastructure tests
│   └── e2e/                       # End-to-end playability tests
├── web/                           # Web game implementations
│   ├── zombie-survival/           # Three.js Zombie Survival
│   └── shared/                    # Web-specific shared utilities
├── .github/workflows/             # CI/CD pipelines
│   ├── ci-standard.yml            # Python quality gate, tests, security scan, Rust gate
│   └── cpp-ci.yml                 # C++ format check (clang-format) + cmake/ctest pipeline
├── .clang-format                  # C++ style config (Google-based, 100 cols)
└── docs/                          # Documentation and design docs
```

### Key Components

| Component             | Location                             | Purpose                                                                                                                                                                                |
| --------------------- | ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| FPS Shared Base       | `src/games/shared/fps_game_base.py`  | Shared constructor and gameplay utilities for FPS titles (Duum, Force Field, Zombie Survival), including common initialization flow and common event handlers                          |
| Game Launcher         | `src/games/`                         | Central entry point, game discovery, selection UI, execution orchestration                                                                                                             |
| Force Field Engine    | `src/games/Force_Field/engine/`      | Raycasting renderer, 3D-to-2D projection, collision detection                                                                                                                          |
| Force Field Runtime   | `src/games/Force_Field/src/`         | Thin game facade plus extracted loop, session, combat, gameplay, screen-flow, and HUD view helper subsystems                                                                           |
| Duum Screen Flow      | `src/games/Duum/src/`                | Thin Duum game facade with delegated per-screen event handling, extracted loop dispatch, gameplay updates, ambient-state management, HUD view helpers, and weapon-system orchestration |
| Zombie Gameplay Flow  | `src/games/Zombie_Survival/src/`     | Thin Zombie Survival game facade with delegated screen handling, extracted gameplay updates, loop dispatch, ambient-state management, and HUD view helpers                             |
| Duum Level Generation | `src/games/Duum/levels/`             | Procedural dungeon generation, room connectivity                                                                                                                                       |
| Tetris Logic          | `src/games/Tetris/`                  | Piece mechanics, board state, gravity, line clearing                                                                                                                                   |
| Shared Renderers      | `src/games/shared/renderers/`        | Common rendering abstractions, 2D drawing, sprite management                                                                                                                           |
| Shared Combat Manager | `src/games/shared/combat_manager.py` | Shared hitscan and explosion logic with a request-based shot-resolution contract                                                                                                       |
| C++ Bindings          | `src/games/shared/cpp_bindings/`     | ctypes interface to compiled performance-critical code                                                                                                                                 |
| QuatEngine C++        | `src/games/shared/cpp/`              | Header-only C++17 engine modules: math, core, game, AI, renderer, input, loader                                                                                                        |
| C++ CI Pipeline       | `.github/workflows/cpp-ci.yml`       | clang-format style gate + cmake/ctest build matrix (GCC 12, Clang 17)                                                                                                                  |
| Input Handler         | `src/games/shared/input/`            | Unified keyboard/controller input abstraction                                                                                                                                          |
| Three.js Client       | `web/zombie-survival/`               | Browser-based 3D rendering for Zombie Survival                                                                                                                                         |

## 5. Desired Functionality

### Core Features

| #   | Feature                         | Status | Description                                                                                                                             |
| --- | ------------------------------- | ------ | --------------------------------------------------------------------------------------------------------------------------------------- |
| F1  | Force Field FPS with Raycasting | ✅     | First-person shooter with 2D raycasting engine, texture mapping, enemy spawning, collision detection                                    |
| F2  | Duum (Doom Reimagining)         | ✅     | Roguelike dungeon crawler with procedural levels, monster AI, weapon variety, scoring system                                            |
| F3  | Enhanced Tetris                 | ✅     | Classic Tetris with pieces, gravity, line clearing, increasing difficulty, score tracking, hold piece                                   |
| F4  | Wizard of Wor Remake            | ✅     | Arcade-style maze game with procedural mazes, enemy patterns, collectible items, lives system                                           |
| F5  | Peanut Butter Panic             | ✅     | Side-scrolling platformer with physics, platforms, enemies, collectibles, level progression                                             |
| F6  | Zombie Survival (Web 3D)        | ✅     | Web-based 3D game using Three.js, multiplayer-ready backend, spawn waves, survival mechanics                                            |
| F7  | QuatGolf (Quaternion Golf)      | 🔄     | Golf game with quaternion-based ball rotation physics, procedural courses, AI opponents                                                 |
| F8  | Unified Launcher                | ✅     | Central game selection interface, launch management, window handling, game exit/resume                                                  |
| F9  | Shared Rendering Infrastructure | ✅     | Common rendering abstractions supporting 2D drawing, sprite management, color/texture handling, and immutable raycaster render contexts |

### API / Interface Contract

**Game Launcher (Main Entry Point):**

```python
from src.games import GameLauncher

launcher = GameLauncher()
launcher.run()  # Opens launcher window, game selection UI
```

**Individual Game API (for testing/programmatic use):**

```python
from src.games.Tetris import TetrisGame
from src.games.shared.config import GameConfig

config = GameConfig()
game = TetrisGame(config)
game.initialize()
game.run()  # Blocking call until game exits
result = game.get_result()  # Score, completion status, etc.
```

**Shared Renderer Interface:**

```python
from src.games.shared.renderers import Renderer

renderer = Renderer(width=1024, height=768)
renderer.draw_sprite(sprite, x, y)
renderer.draw_rect(x, y, w, h, color)
renderer.present()
```

**Input Handler:**

```python
from src.games.shared.input import InputHandler

input_handler = InputHandler()
if input_handler.is_key_pressed("UP"):
    # Move player up
```

**Shared Combat Resolution:**

```python
from games.shared.combat_manager import ShotResolutionRequest

request = ShotResolutionRequest(
    player=player,
    raycaster=raycaster,
    bots=bots,
    damage_texts=damage_texts,
    show_damage=show_damage,
)
damage_texts = combat_manager.check_shot_hit(request)
```

## 6. Data & Configuration

### Input Data

| Input             | Format      | Source                     | Schema                                    |
| ----------------- | ----------- | -------------------------- | ----------------------------------------- |
| Game Config       | YAML        | `src/games/shared/config/` | Resolution, FPS, game-specific parameters |
| Level Definitions | Binary/JSON | `src/games/[game]/levels/` | Level geometry, entity spawns, tile maps  |
| Sprite Sheets     | PNG         | `assets/sprites/`          | Texture atlases for game entities         |
| Game State        | JSON        | Runtime/saved games        | Game progress, scores, player data        |

### Output Data

| Output           | Format    | Destination                  | Description                              |
| ---------------- | --------- | ---------------------------- | ---------------------------------------- |
| Game Result      | JSON      | Launcher memory / `results/` | Final score, completion status, playtime |
| Test Reports     | JSON/HTML | `htmlcov/`                   | Coverage reports and test results        |
| Performance Logs | CSV       | `logs/perf_[timestamp].csv`  | FPS, render time, update time per frame  |

### Configuration

- **Environment variables**: `GAMES_HEADLESS` (run without display), `GAMES_CONFIG` (override config path)
- **Config files**: `src/games/shared/config/base.yaml` contains global settings (resolution, FPS, audio)
- **Game-specific**: Each game subdirectory may have game-specific config files
- **Key settings**: Screen resolution (default 1024x768), target FPS (60), vsync enabled, fullscreen toggle

## 7. Testing Specification

### Testing Strategy

Games employs a test pyramid with unit tests for individual game logic components, integration tests for launcher functionality and game-to-game transitions, and end-to-end tests validating full game playability. Minimum 25% coverage on shared infrastructure due to its critical role. Tests marked with slow/integration can be filtered. Linux CI uses xvfb for headless display, Windows CI uses native display.

### Test Organization

| Category    | Location             | Framework | Markers                    |
| ----------- | -------------------- | --------- | -------------------------- |
| Unit        | `tests/unit/`        | pytest    | `@pytest.mark.unit`        |
| Integration | `tests/integration/` | pytest    | `@pytest.mark.integration` |
| E2E         | `tests/e2e/`         | pytest    | `@pytest.mark.slow`        |
| Shared      | `tests/shared/`      | pytest    | `@pytest.mark.integration` |

### Coverage Requirements

| Scope                 | Minimum | Current | Enforced By                |
| --------------------- | ------- | ------- | -------------------------- |
| Overall               | 50%     | TBD     | CI (`--cov-fail-under=50`) |
| Shared infrastructure | 25%     | TBD     | CI manual check            |

### Required Test Scenarios

- [ ] Unit test: Tetris piece rotation produces expected shapes for all piece types
- [ ] Unit test: Piece collision detection correctly identifies blocking tiles
- [ ] Unit test: Board line-clear logic removes complete rows and shifts down
- [ ] Unit test: Force Field raycasting produces valid screen columns from map geometry
- [x] Unit test: Force Field top-level loop dispatches intro, gameplay, and clock-tick behavior through `src/games/Force_Field/src/game_loop.py`
- [ ] Unit test: Input handler correctly converts key events to game-specific actions
- [ ] Integration test: Launcher successfully discovers and lists all game modules
- [ ] Integration test: Game launch from launcher succeeds with no window errors
- [ ] Integration test: Game exit returns control to launcher without memory leaks
- [ ] E2E test: Tetris game runs for 60 seconds, displays score, accepts input
- [ ] E2E test: Force Field loads map, renders, and responds to movement input
- [ ] E2E test: Duum level generation produces navigable dungeon with connected rooms
- [ ] E2E test: Shared renderer renders sprites without corruption at 1024x768 resolution

## 8. Quality Standards

### Code Quality Tools

| Tool       | Version | Purpose                    | Blocking?         |
| ---------- | ------- | -------------------------- | ----------------- |
| ruff       | Latest  | Linting and import sorting | Yes               |
| mypy       | Latest  | Type checking              | Yes               |
| pytest     | Latest  | Testing framework          | Yes               |
| pytest-cov | Latest  | Coverage reporting         | Yes               |
| black      | Latest  | Code formatting            | No (ruff handles) |

### Design Principles

- **TDD**: Yes — new game features and shared components use test-driven development
- **Design by Contract (DbC)**: No — but assertions validate input bounds for collision/physics
- **DRY**: Yes — shared rendering, input, and physics modules prevent duplication across games
- **Orthogonality**: Yes — each game is self-contained; shared infrastructure is dependency-free

### CI/CD Pipeline

| Workflow                   | Trigger | Purpose                                            | Blocking? |
| -------------------------- | ------- | -------------------------------------------------- | --------- |
| `ci-standard.yml`          | Push/PR | Type check, lint, unit/integration tests, coverage | Yes       |
| `e2e-ubuntu.yml`           | Push/PR | E2E tests with xvfb on Ubuntu                      | Yes       |
| `coverage-integration.yml` | PR      | Codecov integration                                | Yes       |
| `spec-check.yml`           | Push/PR | Verify SPEC.md matches code                        | Yes       |

PR CI now prefers the local self-hosted runner fleet and falls back to
GitHub-hosted runners when the fleet is unavailable. These CI checks remain
merge-blocking without requiring PR review approval.

## 9. Dependencies

### Runtime Dependencies

| Package       | Version | Purpose                                    |
| ------------- | ------- | ------------------------------------------ |
| pygame        | 2.6.1   | Core game rendering and input handling     |
| numpy         | Latest  | Numerical computations (physics, geometry) |
| opencv-python | Latest  | Image processing for sprites and textures  |

### Development Dependencies

| Package     | Version | Purpose                                  |
| ----------- | ------- | ---------------------------------------- |
| pytest      | Latest  | Testing framework                        |
| pytest-cov  | Latest  | Coverage reporting                       |
| pytest-xvfb | Latest  | Virtual framebuffer for headless testing |
| mypy        | Latest  | Type checking                            |
| ruff        | Latest  | Linting                                  |
| black       | Latest  | Formatting                               |

### Fleet Dependencies

| Repo | Relationship | Description                                            |
| ---- | ------------ | ------------------------------------------------------ |
| None | N/A          | Standalone package with no internal fleet dependencies |

## 10. Deployment & Operations

### How to Run

```bash
# Prerequisites
# - Python 3.10+ installed
# - SDL2 development libraries (for Pygame)
# - On Linux: xvfb (for headless testing)

# Installation
git clone https://github.com/D-sorganization/Games
cd Games
pip install -e .
pip install -e ".[dev]"  # For development and testing

# Running Launcher
python -m src.games  # Opens launcher window

# Running Individual Game (programmatic)
python -c "from src.games.Tetris import TetrisGame; g = TetrisGame(); g.run()"

# Running Tests
pytest tests/unit/ -v
pytest tests/integration/ -v -m integration
pytest tests/e2e/ -v -m slow  # Slower E2E tests
pytest tests/ --cov=src/games --cov-report=html

# Headless Testing (Linux)
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 &
pytest tests/ -v
```

### Build Artifacts

| Artifact         | Format        | Destination                            |
| ---------------- | ------------- | -------------------------------------- |
| Game Executable  | Python module | Runnable via `python -m src.games`     |
| Test Coverage    | HTML          | `htmlcov/index.html`                   |
| Performance Logs | CSV           | `logs/perf_[timestamp].csv` (optional) |

## 11. Roadmap & Open Issues

### Current Phase

Active development. Core games (F1-F6, F8-F9) fully implemented and tested. F7 (QuatGolf) in progress with quaternion physics implementation. Shared rendering infrastructure stable. Focus on test coverage expansion and performance optimization.

### Completed (2026-04-06)

- **Force Field orchestrator split** (issue #715): Reduced `src/games/Force_Field/src/game.py` to a thin orchestrator by extracting session lifecycle, combat actions, gameplay runtime, and screen-flow responsibilities into focused modules. Added screen-flow tests covering intro transitions, map-select launch flow, and key-binding selection.
- **Force Field game-loop extraction** (issue #715): Moved the top-level state dispatch loop into `src/games/Force_Field/src/game_loop.py`, leaving `Game.run()` as a facade entry point and adding focused tests for intro timing, paused gameplay behavior, damage-flash decay, and frame clock ticking.

### Completed (2026-04-02)

- **run_assessment.py refactor** (issue #680): Extracted `file_discovery()`, `analyze_module()`, `calculate_scores()`, and `generate_report()` from the monolithic 394-line `run_assessment()` function. Each helper follows SRP; `run_assessment()` is now a thin orchestrator. 35 new unit tests cover every extracted function.

### Completed (2026-03-31)

- **Collision detection optimization** (issue #681): Wizard of Wor collision detection replaced O(n²) brute-force with O(n) spatial-grid approach; significant FPS improvement at high entity counts.

### Planned Work

| Priority | Item                                                            | Issue/PR | Target Date |
| -------- | --------------------------------------------------------------- | -------- | ----------- |
| P1       | Complete QuatGolf quaternion physics and course generation      | TBD      | Q2 2026     |
| P1       | Expand unit test coverage to 70% overall                        | TBD      | Q2 2026     |
| P2       | Add networked multiplayer support to Zombie Survival            | TBD      | Q3 2026     |
| P2       | Implement save/load game state for all games                    | TBD      | Q3 2026     |
| P3       | Performance optimization for raycasting engine (target 120 FPS) | TBD      | Q4 2026     |

### Known Limitations

- Raycasting engine (Force Field) limited to 2D top-down map data (no true 3D height)
- Procedural level generation may produce unsolvable mazes in rare cases (< 1%)
- Web-based Zombie Survival requires separate Node.js server for multiplayer features
- Game launcher not responsive during gameplay (single-threaded event loop)
- Save game feature not yet implemented (all progress lost on exit)
- Linux CI tests require xvfb; native display support limited to X11 (no Wayland)

## 12. Change Log

| Date       | Version | Changes                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ---------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-04-12 | 1.1.24  | Expanded raycaster branch coverage tests and applied Black formatting fixes across 7 files to satisfy the quality-gate CI check.                                                                                                                                                                                                                                                                                                                                                                                                                |
| 2026-04-11 | 1.1.20  | Partially addressed issue `#736` by extracting shared FPS defaults and controls across Duum, Force Field, and Zombie Survival into `games.shared` modules, plus deduplicating Duum world-particle setup. This adds `FPS_SHARED_CONSTANTS`, shared input binding profiles, and a shared `WorldParticle` import in Duum particle setup.                                                                                                                                                                                                           |
| 2026-04-11 | 1.1.21  | Partially addressed issue `#737` by decomposing `MonsterStyleRenderer.render` into smaller helper methods for body, head, arms, and legs rendering, reducing function size and preserving behavior.                                                                                                                                                                                                                                                                                                                                             |
| 2026-04-11 | 1.1.23  | Addresses issue `#743` by decomposing the top 5 oversized Python functions into thin orchestrators with single-responsibility helpers: `Force_Field/src/renderer.py::render_game` (108→24 LOC), `Force_Field/src/renderer.py::_render_portal` (105→30 LOC), `scripts/analyze_completist_data.py::generate_report` (106→15 LOC), `Tetris/tetris.py::TetrisGame.run` (102→27 LOC), and `Wizard_of_Wor/wizard_of_wor/enemy.py::Enemy.update` (96→21 LOC). Frame-step ordering preserved; added 8 unit tests for the new completist report helpers. |
| 2026-04-11 | 1.1.22  | Extracted shared FPS constructor initialization into `FPSGameBase` and rewired the Duum, Force Field, and Zombie Survival constructors through the shared setup path.                                                                                                                                                                                                                                                                                                                                                                           |
| 2026-04-11 | 1.1.19  | Refactored Force Field input handling to narrow direct game-object dependency chains behind handler accessors and action helpers, with focused regression coverage for pause and cheat-input behavior.                                                                                                                                                                                                                                                                                                                                          |
| 2026-04-11 | 1.1.18  | Introduced immutable parameter objects for the raycaster sprite, textured wall, and minimap render helpers, updated the raycaster wrappers to pass those render contexts, and added validation coverage for the new bundles.                                                                                                                                                                                                                                                                                                                    |
| 2026-04-10 | 1.1.16  | Partially addressed issue `#721` by extracting Duum weapon/combat orchestration out of `src/games/Duum/src/game.py` into `weapon_system.py`, keeping `Game` as the public façade, and adding focused weapon-system plus delegation tests around the new seam.                                                                                                                                                                                                                                                                                   |
| 2026-04-10 | 1.1.15  | Partially addressed issue `#721` by extracting Force Field and Duum HUD rendering out of their respective `ui_renderer.py` files into `ui_hud_views.py` modules, keeping `UIRenderer` as the public façade, and adding seam tests around the new HUD delegation points. Force Field `ui_renderer.py` reduced from 556 → 260 lines; Duum from 594 → 254 lines.                                                                                                                                                                                   |
| 2026-04-10 | 1.1.14  | Partially addressed issue `#721` by extracting Zombie Survival HUD rendering out of `src/games/Zombie_Survival/src/ui_renderer.py` into `ui_hud_views.py`, keeping `UIRenderer` as the public façade, and adding seam tests around the new HUD delegation points.                                                                                                                                                                                                                                                                               |
| 2026-04-10 | 1.1.13  | Partially addressed issue `#721` by extracting Zombie Survival session/level progression out of `src/games/Zombie_Survival/src/game.py` into `progression_flow.py`, delegating full-game start, level start, game-over, and portal-completion transitions through a focused helper module, and adding seam tests around the extracted progression behavior.                                                                                                                                                                                     |
| 2026-04-07 | 1.1.8   | Partially addressed issue `#721` by splitting Zombie Survival menu, pause/config, and progression rendering out of `src/games/Zombie_Survival/src/ui_renderer.py` into dedicated helper modules (`ui_menu_views.py`, `ui_overlay_views.py`, `ui_progress_views.py`), keeping `UIRenderer` as the public façade, and adding targeted delegation tests around the extracted seams.                                                                                                                                                                |
| 2026-04-07 | 1.1.7   | Partially addressed issue `#721` by splitting Duum menu, pause/config, and progression rendering out of `src/games/Duum/src/ui_renderer.py` into dedicated helper modules (`ui_menu_views.py`, `ui_overlay_views.py`, `ui_progress_views.py`), keeping `UIRenderer` as the public façade, and adding targeted delegation tests around the extracted seams.                                                                                                                                                                                      |
| 2026-04-07 | 1.1.6   | Partially addressed issue `#721` by splitting Force Field menu, pause/config, and progression rendering into dedicated helper modules (`ui_menu_views.py`, `ui_overlay_views.py`, `ui_progress_views.py`), keeping `UIRenderer` as the public façade, and adding targeted delegation tests around the extracted seams.                                                                                                                                                                                                                          |
| 2026-04-06 | 1.1.5   | Completed the Force Field orchestrator split by extracting the top-level state dispatcher into `src/games/Force_Field/src/game_loop.py`, documenting the runtime subsystem explicitly, and adding targeted loop tests for intro timing, gameplay updates, and frame clock ticking.                                                                                                                                                                                                                                                              |
| 2026-04-06 | 1.1.4   | Split the Force Field orchestrator into focused `game_session`, `combat_actions`, `gameplay_runtime`, and `screen_flow` modules, reducing `game.py` to a thin coordinator and adding screen-flow coverage for intro, setup, and key-config transitions.                                                                                                                                                                                                                                                                                         |
| 2026-04-14 | 1.1.26  | Refactor(#737,#746): decomposed 25 oversized functions across renderers and fps_game_base into focused helpers; added tests for game_state_types and fps_game_base sub-initializers improving coverage.                                                                                                                                                                                                                                                                                                                                         |
| 2026-04-06 | 1.1.3   | Narrowed the shared combat-manager hitscan interface to a request-based shot-resolution contract and documented the shared combat component explicitly.                                                                                                                                                                                                                                                                                                                                                                                         |
| 2026-04-02 | 1.1.2   | Refactored `scripts/run_assessment.py` (issue #680): extracted `file_discovery`, `analyze_module`, `calculate_scores`, `generate_report` from monolithic function; added 35 unit tests; `run_assessment()` is now a thin orchestrator.                                                                                                                                                                                                                                                                                                          |
| 2026-03-31 | 1.1.1   | Added self-hosted runner fallback behavior to PR CI documentation and normalized C++ headers/tests to satisfy the blocking clang-format check                                                                                                                                                                                                                                                                                                                                                                                                   |
| 2026-03-28 | 1.0.0   | Initial specification document                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| 2026-03-30 | 1.1.0   | A-N Assessment remediation: added DbC precondition validation to `game_launcher.py` (calculate_game_rects, handle_keyboard_navigation, draw_ui), `run_tests.py` (get_test_environment, run_game_tests), and scripts (analyze_completist_data, generate_assessment_summary, create_issues_from_assessment, mypy_autofix_agent). Added docstrings to MockRect methods in conftest.py. Added .env to .gitignore (infrastructure fix). Addresses issue #658.                                                                                        |
