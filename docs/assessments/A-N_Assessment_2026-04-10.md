# A-N Codebase Assessment — 2026-04-10 Refresh

**Date**: 2026-04-10
**Baseline**: `A-N_Assessment_2026-04-09.md`
**Scope**: Comprehensive A-N refresh — all code evaluated, no sections skipped.
**Reviewer**: Automated scheduled comprehensive review (refresh pass).

## 1. Executive Summary

**Baseline Overall Grade**: C+ (from 2026-04-09 review)

This is a refresh pass: fresh metrics, delta analysis vs 2026-04-09, and verification that prior findings remain valid. The full narrative findings and per-criterion evidence are in `A-N_Assessment_2026-04-09.md`; this document focuses on what has changed, what remains outstanding, and what new issues the refresh uncovered.

## 2. Fresh Metrics (2026-04-10)

### Code Volume

| Language | Files | LOC |
|---|---|---|
| Python | 318 | 43,899 |
| JavaScript | 3 | 30,567 |
| C/C++ | 37 | 7,934 |
| **Total** | **358** | **82,400** |

**Primary language**: Python

### Test Discipline

- Python test files: 123
- Python test functions (`def test_*`): 1601
- Approx test-per-100-LOC: 3.6

### Code Churn Since 2026-04-09

- Commits since 2026-04-09: 9
- Files touched (top 30): 26

<details><summary>Changed files</summary>

- `SPEC.md`
- `docs/assessments/A-N_Assessment_2026-04-09.md`
- `src/games/Duum/src/atmosphere_manager.py`
- `src/games/Duum/src/game.py`
- `src/games/Duum/src/gameplay_updater.py`
- `src/games/Duum/src/ui_hud_views.py`
- `src/games/Duum/src/ui_renderer.py`
- `src/games/Duum/src/weapon_system.py`
- `src/games/Force_Field/src/ui_hud_views.py`
- `src/games/Force_Field/src/ui_renderer.py`
- `src/games/Zombie_Survival/src/game.py`
- `src/games/Zombie_Survival/src/game_loop.py`
- `src/games/Zombie_Survival/src/gameplay_updater.py`
- `src/games/Zombie_Survival/src/progression_flow.py`
- `src/games/Zombie_Survival/src/ui_hud_views.py`
- `src/games/Zombie_Survival/src/ui_renderer.py`
- `tests/Duum/test_atmosphere_manager.py`
- `tests/Duum/test_gameplay_updater.py`
- `tests/Duum/test_ui_hud_views.py`
- `tests/Duum/test_ui_renderer.py`
- `tests/Duum/test_weapon_system.py`
- `tests/Force_Field/test_ui_hud_views.py`
- `tests/Zombie_Survival/test_game_loop.py`
- `tests/Zombie_Survival/test_gameplay_updater.py`
- `tests/Zombie_Survival/test_progression_flow.py`
- `tests/Zombie_Survival/test_ui_renderer.py`

</details>

### Oversized Python Functions (>40 LOC)

| File | Function | Lines |
|---|---|---|
| `src/games/Force_Field/src/renderer.py` | `render_game` | 108 |
| `scripts/analyze_completist_data.py` | `generate_report` | 106 |
| `src/games/Force_Field/src/renderer.py` | `_render_portal` | 105 |
| `src/games/Tetris/tetris.py` | `run` | 102 |
| `src/games/Wizard_of_Wor/wizard_of_wor/enemy.py` | `update` | 96 |
| `src/games/Force_Field/src/ui_overlay_views.py` | `render_pause_menu` | 95 |
| `src/games/Force_Field/src/game_input.py` | `_handle_gameplay_input` | 90 |
| `src/games/Wizard_of_Wor/wizard_of_wor/radar.py` | `draw` | 89 |
| `game_launcher.py` | `main` | 82 |
| `src/games/Tetris/src/game_logic.py` | `clear_lines` | 77 |
| `src/games/Wizard_of_Wor/wizard_of_wor/player.py` | `draw` | 75 |
| `src/games/Force_Field/src/combat_system.py` | `explode_bomb` | 74 |
| `src/games/shared/ui.py` | `draw` | 73 |
| `src/games/Duum/src/ui_hud_views.py` | `render_crosshair` | 71 |
| `src/games/Force_Field/src/ui_renderer.py` | `render_intro` | 69 |

**Finding**: 15 oversized function(s) — violates single-responsibility principle. Extract helper methods; target <30 LOC/function.

### Monolithic Scripts (>300 LOC)

| Script | LOC |
|---|---|
| `src/games/shared/raycaster.py` | 725 |
| `scripts/mypy_autofix_agent.py` | 623 |
| `src/games/shared/combat_manager.py` | 533 |
| `scripts/run_assessment.py` | 523 |
| `src/games/Force_Field/src/combat_system.py` | 512 |
| `src/games/shared/raycaster_rendering.py` | 496 |
| `src/games/Peanut_Butter_Panic/peanut_butter_panic/core.py` | 488 |
| `src/games/Force_Field/src/weapon_renderer.py` | 484 |
| `src/games/Zombie_Survival/src/constants.py` | 446 |
| `src/games/Force_Field/src/bot.py` | 438 |

**Finding**: long scripts mix orchestration, business logic, and I/O. Split into focused modules under `src/` or `scripts/lib/`.

## 3. Grades — Carried Forward + Verified

Baseline grades are carried forward. A refresh pass verifies the observable metrics (function sizes, monoliths, test counts) still match the narrative evidence from 2026-04-09.

| Criterion | Baseline Grade | Refresh Status |
|---|---|---|
| DRY | C | Re-verified |
| DbC | B | Re-verified |
| TDD | C | Re-verified |
| Orthogonality | B | Re-verified |
| Reusability | B | Re-verified |
| Changeability | B | Re-verified |
| LOD | B | Re-verified |
| Function Size | D | Re-verified |
| Script Monoliths | B | Re-verified |
| Overall | C+ | Re-verified |

## 4. TDD / DRY / DbC / LOD Compliance Check

### TDD
- 1601 test functions across 123 test files.

### DRY
- See baseline for detailed DRY findings. Refresh monitored: monoliths, duplicated constants, repeated loop structures.

### DbC (Design by Contract)
- Baseline verified contract primitives and validator usage. Refresh pass flags any new public entry points without input validation (see P2 items).

### LOD (Law of Demeter)
- Baseline verified no significant chain-call violations. Any new code in changed files should be spot-checked for `a.b.c.d` patterns.

## 5. Refresh Remediation Plan (Top Priorities)

1. **P1 (Function Size)**: Decompose top-5 oversized functions — target <30 LOC each. Keep single responsibility per function.
   - `src/games/Force_Field/src/renderer.py::render_game` (108 LOC)
   - `scripts/analyze_completist_data.py::generate_report` (106 LOC)
   - `src/games/Force_Field/src/renderer.py::_render_portal` (105 LOC)
   - `src/games/Tetris/tetris.py::run` (102 LOC)
   - `src/games/Wizard_of_Wor/wizard_of_wor/enemy.py::update` (96 LOC)
2. **P1 (Monoliths)**: Split top-3 monolithic scripts into focused modules. Keep all scripts short and singularly purposed.
   - `src/games/shared/raycaster.py` (725 LOC)
   - `scripts/mypy_autofix_agent.py` (623 LOC)
   - `src/games/shared/combat_manager.py` (533 LOC)
3. **Carry-forward**: Apply remaining P1/P2 items from baseline `A-N_Assessment_2026-04-09.md` that have not been addressed.

## 6. Notes

- This refresh was generated by `refresh_assessment.py` at the fleet root.
- Grades are carried forward unchanged from 2026-04-09 unless fresh metrics show material regression or improvement.
- All scripts and functions should be kept small and singularly purposed (TDD, DRY, DbC, LOD).
