# Assessment L Results: Long-Term Maintainability

## Executive Summary

- **Code Quality**: The codebase is generally clean, typed, and linted. This is a huge plus for maintainability.
- **Tech Debt**: The "God Class" pattern in `Game` logic is the main debt. As games grow, these files become unmaintainable.
- **Bus Factor**: The `Raycaster` and math logic are complex and dense. New maintainers would struggle to modify the rendering core without breaking it.
- **Dependencies**: The stack is simple (`pygame`, `numpy`). Low risk of abandonment.
- **Documentation**: "Why" comments are missing in complex algorithms (DDA raycasting).

## Top 10 Maintainability Risks

1.  **God Classes (Critical)**: `src/games/*/src/game.py` files are too large and do too much.
2.  **Complex Math (Major)**: Raycasting logic in `Raycaster` is dense and under-documented.
3.  **Copy-Paste (Major)**: `Zombie_Survival` and `Duum` share logic but are separate files. Fixes in one must be manually ported.
4.  **Script Rot (Minor)**: Helper scripts in `scripts/` are less maintained than src.
5.  **Vendor Code (Minor)**: `three.module.js` is a large blob of external code.
6.  **Hardcoded Strings (Minor)**: Paths and asset names scattered in code.
7.  **Test Gaps (Major)**: Fear of refactoring due to lack of tests.
8.  **Bus Factor (Major)**: Few contributors understand the whole system.
9.  **Config Management (Minor)**: No central config schema.
10. **Magic Numbers (Nit)**: Gameplay constants in logic.

## Scorecard

| Category | Description | Score | Notes |
| :--- | :--- | :--- | :--- |
| Deprecated Deps | 0 | 10/10 | Clean. |
| Unmaintained Code | <10% | 9/10 | Most files active. |
| Bus Factor | >2 | 3/10 | High complexity/low docs. |
| Upgrade Path | Documented | 5/10 | Simple pip upgrade. |

## Maintainability Assessment

| Area | Status | Risk | Action |
| :--- | :--- | :--- | :--- |
| Dependency age | ✅ | Low | Standard libs. |
| Code coverage | ❌ | High | Needs tests. |
| Bus factor | ⚠️ | High | Document algorithms. |

## Findings Table

| ID | Severity | Category | Location | Symptom | Root Cause | Fix | Effort |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| L-001 | Critical | Maintainability | `Game` classes | 1000+ lines | Coupling | Refactor | L |
| L-002 | Major | Maintainability | `Raycaster` | "Magic" math | Complexity | Add explaining comments | M |

## Remediation Roadmap

**48 Hours**:
- Add comments explaining the DDA algorithm in `Raycaster`.

**2 Weeks**:
- Refactor `Zombie_Survival` to inherit more from `Duum` or a shared base class to reduce duplication.

**6 Weeks**:
- Implement a true ECS (Entity Component System) to kill the God Classes.

## Diff Suggestions

### Extract Constant
```python
<<<<<<< SEARCH
    if dist < 0.5:
        # collision
=======
    COLLISION_THRESHOLD = 0.5
    if dist < COLLISION_THRESHOLD:
        # collision
>>>>>>> REPLACE
```
