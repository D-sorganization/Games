# SPEC.md — Repository Specification Document

## 1. Identity

| Field | Value |
|-------|-------|
| **Repository Name** | `Games` |
| **GitHub URL** | `https://github.com/D-sorganization/Games` |
| **Owner** | D-sorganization |
| **Primary Language(s)** | Python 3.10+ (Pygame), JavaScript (Three.js for web) |
| **License** | MIT |
| **Current Version** | N/A |
| **Spec Version** | 1.0.0 |
| **Last Spec Update** | 2026-03-28 |

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

Games is a standalone entertainment application within the D-sorganization fleet with no dependencies on other fleet repositories. It depends on Pygame 2.6.1 for core rendering and input, OpenCV for image processing, and optionally provides Three.js-based web game implementations. The system is self-contained with all game logic, shared utilities, and test infrastructure included.

### Module Map

```
Games/
├── src/games/                      # Main game implementations
│   ├── Force_Field/               # FPS with raycasting engine
│   │   ├── engine/                # Raycasting renderer and physics
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
│   │   ├── maze/                  # Procedural maze generation
│   │   ├── enemies/               # Enemy patterns and AI
│   │   └── items/                 # Collectible items
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
└── docs/                          # Documentation and design docs
```

### Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Game Launcher | `src/games/` | Central entry point, game discovery, selection UI, execution orchestration |
| Force Field Engine | `src/games/Force_Field/engine/` | Raycasting renderer, 3D-to-2D projection, collision detection |
| Duum Level Generation | `src/games/Duum/levels/` | Procedural dungeon generation, room connectivity |
| Tetris Logic | `src/games/Tetris/` | Piece mechanics, board state, gravity, line clearing |
| Shared Renderers | `src/games/shared/renderers/` | Common rendering abstractions, 2D drawing, sprite management |
| C++ Bindings | `src/games/shared/cpp_bindings/` | ctypes interface to compiled performance-critical code |
| Input Handler | `src/games/shared/input/` | Unified keyboard/controller input abstraction |
| Three.js Client | `web/zombie-survival/` | Browser-based 3D rendering for Zombie Survival |

## 5. Desired Functionality

### Core Features

| # | Feature | Status | Description |
|---|---------|--------|-------------|
| F1 | Force Field FPS with Raycasting | ✅ | First-person shooter with 2D raycasting engine, texture mapping, enemy spawning, collision detection |
| F2 | Duum (Doom Reimagining) | ✅ | Roguelike dungeon crawler with procedural levels, monster AI, weapon variety, scoring system |
| F3 | Enhanced Tetris | ✅ | Classic Tetris with pieces, gravity, line clearing, increasing difficulty, score tracking, hold piece |
| F4 | Wizard of Wor Remake | ✅ | Arcade-style maze game with procedural mazes, enemy patterns, collectible items, lives system |
| F5 | Peanut Butter Panic | ✅ | Side-scrolling platformer with physics, platforms, enemies, collectibles, level progression |
| F6 | Zombie Survival (Web 3D) | ✅ | Web-based 3D game using Three.js, multiplayer-ready backend, spawn waves, survival mechanics |
| F7 | QuatGolf (Quaternion Golf) | 🔄 | Golf game with quaternion-based ball rotation physics, procedural courses, AI opponents |
| F8 | Unified Launcher | ✅ | Central game selection interface, launch management, window handling, game exit/resume |
| F9 | Shared Rendering Infrastructure | ✅ | Common rendering abstractions supporting 2D drawing, sprite management, color/texture handling |

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

## 6. Data & Configuration

### Input Data

| Input | Format | Source | Schema |
|-------|--------|--------|--------|
| Game Config | YAML | `src/games/shared/config/` | Resolution, FPS, game-specific parameters |
| Level Definitions | Binary/JSON | `src/games/[game]/levels/` | Level geometry, entity spawns, tile maps |
| Sprite Sheets | PNG | `assets/sprites/` | Texture atlases for game entities |
| Game State | JSON | Runtime/saved games | Game progress, scores, player data |

### Output Data

| Output | Format | Destination | Description |
|--------|--------|-------------|-------------|
| Game Result | JSON | Launcher memory / `results/` | Final score, completion status, playtime |
| Test Reports | JSON/HTML | `htmlcov/` | Coverage reports and test results |
| Performance Logs | CSV | `logs/perf_[timestamp].csv` | FPS, render time, update time per frame |

### Configuration

- **Environment variables**: `GAMES_HEADLESS` (run without display), `GAMES_CONFIG` (override config path)
- **Config files**: `src/games/shared/config/base.yaml` contains global settings (resolution, FPS, audio)
- **Game-specific**: Each game subdirectory may have game-specific config files
- **Key settings**: Screen resolution (default 1024x768), target FPS (60), vsync enabled, fullscreen toggle

## 7. Testing Specification

### Testing Strategy

Games employs a test pyramid with unit tests for individual game logic components, integration tests for launcher functionality and game-to-game transitions, and end-to-end tests validating full game playability. Minimum 25% coverage on shared infrastructure due to its critical role. Tests marked with slow/integration can be filtered. Linux CI uses xvfb for headless display, Windows CI uses native display.

### Test Organization

| Category | Location | Framework | Markers |
|----------|----------|-----------|---------|
| Unit | `tests/unit/` | pytest | `@pytest.mark.unit` |
| Integration | `tests/integration/` | pytest | `@pytest.mark.integration` |
| E2E | `tests/e2e/` | pytest | `@pytest.mark.slow` |
| Shared | `tests/shared/` | pytest | `@pytest.mark.integration` |

### Coverage Requirements

| Scope | Minimum | Current | Enforced By |
|-------|---------|---------|-------------|
| Overall | 50% | TBD | CI (`--cov-fail-under=50`) |
| Shared infrastructure | 25% | TBD | CI manual check |

### Required Test Scenarios

- [ ] Unit test: Tetris piece rotation produces expected shapes for all piece types
- [ ] Unit test: Piece collision detection correctly identifies blocking tiles
- [ ] Unit test: Board line-clear logic removes complete rows and shifts down
- [ ] Unit test: Force Field raycasting produces valid screen columns from map geometry
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

| Tool | Version | Purpose | Blocking? |
|------|---------|---------|-----------|
| ruff | Latest | Linting and import sorting | Yes |
| mypy | Latest | Type checking | Yes |
| pytest | Latest | Testing framework | Yes |
| pytest-cov | Latest | Coverage reporting | Yes |
| black | Latest | Code formatting | No (ruff handles) |

### Design Principles

- **TDD**: Yes — new game features and shared components use test-driven development
- **Design by Contract (DbC)**: No — but assertions validate input bounds for collision/physics
- **DRY**: Yes — shared rendering, input, and physics modules prevent duplication across games
- **Orthogonality**: Yes — each game is self-contained; shared infrastructure is dependency-free

### CI/CD Pipeline

| Workflow | Trigger | Purpose | Blocking? |
|----------|---------|---------|-----------|
| `ci-standard.yml` | Push/PR | Type check, lint, unit/integration tests, coverage | Yes |
| `e2e-ubuntu.yml` | Push/PR | E2E tests with xvfb on Ubuntu | Yes |
| `coverage-integration.yml` | PR | Codecov integration | Yes |
| `spec-check.yml` | Push/PR | Verify SPEC.md matches code | Yes |

## 9. Dependencies

### Runtime Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| pygame | 2.6.1 | Core game rendering and input handling |
| numpy | Latest | Numerical computations (physics, geometry) |
| opencv-python | Latest | Image processing for sprites and textures |

### Development Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| pytest | Latest | Testing framework |
| pytest-cov | Latest | Coverage reporting |
| pytest-xvfb | Latest | Virtual framebuffer for headless testing |
| mypy | Latest | Type checking |
| ruff | Latest | Linting |
| black | Latest | Formatting |

### Fleet Dependencies

| Repo | Relationship | Description |
|------|-------------|-------------|
| None | N/A | Standalone package with no internal fleet dependencies |

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

| Artifact | Format | Destination |
|----------|--------|-------------|
| Game Executable | Python module | Runnable via `python -m src.games` |
| Test Coverage | HTML | `htmlcov/index.html` |
| Performance Logs | CSV | `logs/perf_[timestamp].csv` (optional) |

## 11. Roadmap & Open Issues

### Current Phase

Active development. Core games (F1-F6, F8-F9) fully implemented and tested. F7 (QuatGolf) in progress with quaternion physics implementation. Shared rendering infrastructure stable. Focus on test coverage expansion and performance optimization.

### Planned Work

| Priority | Item | Issue/PR | Target Date |
|----------|------|----------|-------------|
| P1 | Complete QuatGolf quaternion physics and course generation | TBD | Q2 2026 |
| P1 | Expand unit test coverage to 70% overall | TBD | Q2 2026 |
| P2 | Add networked multiplayer support to Zombie Survival | TBD | Q3 2026 |
| P2 | Implement save/load game state for all games | TBD | Q3 2026 |
| P3 | Performance optimization for raycasting engine (target 120 FPS) | TBD | Q4 2026 |

### Known Limitations

- Raycasting engine (Force Field) limited to 2D top-down map data (no true 3D height)
- Procedural level generation may produce unsolvable mazes in rare cases (< 1%)
- Web-based Zombie Survival requires separate Node.js server for multiplayer features
- Game launcher not responsive during gameplay (single-threaded event loop)
- Save game feature not yet implemented (all progress lost on exit)
- Linux CI tests require xvfb; native display support limited to X11 (no Wayland)

## 12. Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2026-03-28 | 1.0.0 | Initial specification document |
