# CLAUDE.md

Quick-reference for developers and AI agents working in this repository.

## Branch Policy

All work on `main` branch. PRs target `main`.

## Project Overview

**Games** is a collection of Python (Pygame) and web-based games accessible through a unified GUI launcher (`game_launcher.py`). The shared engine lives in `src/games/shared/` and individual games live under `src/games/<GameName>/`.

Key games: Force Field (FPS raycaster), Duum (Doom-style FPS), Tetris, Wizard of Wor, Peanut Butter Panic, Zombie Survival (web).

## Architecture

```
src/games/
  shared/          # Shared engine: raycaster, base classes, ECS components, UI
  Force_Field/     # FPS game using shared raycaster
  Duum/            # Doom-style FPS using shared raycaster
  Tetris/          # Classic puzzle game
  Wizard_of_Wor/   # Arcade maze shooter
  Peanut_Butter_Panic/
  Zombie_Survival/ # Web-based (HTML/JS)
tests/             # Mirrors src/games/ structure
scripts/           # Utility scripts
tools/             # Build and quality tooling
```

- **Shared engine** (`src/games/shared/`): raycaster, base classes (player, bot, map, projectile), ECS-style components, event bus, spatial grid, particle system, UI renderers.
- **Game launcher**: `game_launcher.py` at the repo root provides a Pygame GUI to select and launch games.
- **Package layout**: `setuptools` with `src/` layout (`pyproject.toml`); install with `pip install -e .`.

## Dev Commands

```bash
# Setup
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e .

# Lint
ruff check .                    # Linting (E, F, W, I, B, UP rules)
ruff check . --fix              # Auto-fix lint issues

# Format
black --check .                 # Check formatting (line-length 88)
black .                         # Auto-format

# Type check
mypy scripts/ tools/ *.py --ignore-missing-imports

# Test
pytest tests/                   # Run all tests
pytest tests/ -m "not slow"     # Skip slow tests
pytest tests/ --cov=src/games/shared --cov-branch  # With coverage

# Pre-commit
pip install pre-commit
pre-commit install
pre-commit install --hook-type pre-push
pre-commit run --all-files      # Run all commit-time hooks
```

## CI/CD

The primary workflow is **ci-standard.yml** (`.github/workflows/ci-standard.yml`). It runs on pushes to `main` and on pull requests.

### Jobs

1. **quality-gate** -- ruff lint, black format check, mypy (advisory), placeholder detection (no TODO/FIXME in `.py` files).
2. **security-scan** -- `pip-audit` against `requirements.txt`.
3. **tests** -- `pytest` with coverage on Python 3.11, runs under `xvfb` with SDL dummy drivers for headless Pygame.
4. **rust-quality-gate** -- conditional; activates only when `Cargo.toml` exists.

Tool versions are pinned and must match `.pre-commit-config.yaml`: Ruff 0.14.10, Black 26.1.0, MyPy 1.13.0.

### Pre-commit hooks

- **On commit**: ruff lint+format, black, prettier (YAML/JSON/MD), no-wildcard-imports, no-debug-statements, no-print-in-src.
- **On push**: mypy, bandit (security), pytest unit tests, semgrep, radon (complexity).

## Coding Conventions

- **Python 3.10+** target (`py310` in ruff/black config).
- **Logging over print**: use `logging` module; `print()` is banned in `src/` via pre-commit hook.
- **No wildcard imports**: always import explicitly.
- **No bare except**: catch specific exceptions.
- **Type hints**: required on function signatures.
- **Design by Contract (DbC)**: validate inputs at API boundaries; use `assert` for internal invariants; document pre/postconditions in docstrings.
- **DRY**: extract shared logic into `src/games/shared/`; any block >5 lines duplicated in 2+ places must be refactored.
- **Orthogonality**: no circular imports; separate UI logic from game logic.
- **Test-Driven Development (TDD)**: write failing test first (RED), make it pass (GREEN), then refactor (REFACTOR).
- **Commit messages**: conventional commits (`feat:`, `fix:`, `docs:`, `perf:`).

## Dependencies

Core: `pygame`, `numpy`, `opencv-python`. Dev/test: `pytest`, `pytest-cov`, `pytest-timeout`, `ruff`, `black`, `mypy`, `bandit`, `pre-commit`.

Pinned versions are in `requirements.txt` (runtime) and `requirements.lock` (CI lockfile).
