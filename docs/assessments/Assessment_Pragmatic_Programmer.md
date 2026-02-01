# Assessment: Pragmatic Programmer Review

## Craftsmanship Scorecard

| Principle | Score (0-10) | Notes |
| :--- | :--- | :--- |
| **DRY** (Don't Repeat Yourself) | 4/10 | **CRITICAL FAILURE**. Massive duplication in `scripts/`. |
| **Orthogonality** | 5/10 | God Classes in Games (`__init__` > 100 lines) couple logic tightly. |
| **Reversibility** | 6/10 | Vendor code (Three.js) is hard to swap. Configs are hardcoded. |
| **Tracer Bullets** | 9/10 | End-to-end functionality (Launcher -> Game) works perfectly. |
| **Broken Windows** | 7/10 | Code is generally clean (linted), but test coverage is a broken window. |
| **Documentation** | 6/10 | "Self-documenting" code is relied upon too heavily. |
| **Overall** | **6/10** | **Functional but brittle.** |

## Key Findings

### 1. DRY Violations (The "Copy-Paste" Problem)
The automated review detected **Major Duplication** in the `scripts/` directory.
-   `scripts/generate_assessment_summary.py` and `scripts/shared/assessment_utils.py` share large blocks.
-   `scripts/setup/generate_high_quality_sounds.py` repeats logic 8+ times.
-   **Impact**: Changing assessment logic requires editing 2-3 files. High risk of inconsistency.

### 2. Orthogonality & Coupling (The "God Class" Problem)
-   **Game Classes**: `Duum/src/game.py` and `Zombie_Survival/src/game.py` have `__init__` methods exceeding 50 lines that initialize *everything* (Audio, Video, Logic, Input).
-   **Impact**: You cannot test "Input" without initializing "Video". You cannot reuse "Physics" without "Audio". This is low orthogonality.
-   **Rendering**: `render_hud` functions are massive and mix logic with drawing commands.

### 3. "Broken Windows" Theory
-   **Test Coverage**: The low test coverage (0.14 ratio) is a broken window. It signals that "we don't test here", encouraging new code to be untested.
-   **Script Hygiene**: While `src/` is clean, `scripts/` are allowed to be messy (duplicated). This rot will spread.

## Recommendations

1.  **Refactor Scripts (Immediate)**: Extract shared logic from `generate_assessment_summary.py` into `scripts/shared/assessment_utils.py`. Delete the duplicates.
2.  **Decouple Game Loop (Medium)**: Break `Game.__init__` into `Game.load_assets()`, `Game.init_systems()`, etc. Pass dependencies (like `Renderer`) into constructors rather than creating them inside.
3.  **Fix Test Culture (High)**: Mandate that every bug fix comes with a test. "Stop the bleeding" on coverage.

## Conclusion

The project works well but suffers from "Script Rot" and "Monolithic Game Classes". It violates DRY and Orthogonality significantly in these areas. While the *Product* is good, the *Craftsmanship* needs a dedicated refactoring sprint to improve maintainability.
