# Assessment B Results: Hygiene, Security & Quality

## Executive Summary

- **Linting Enforcement**: `ruff` and `black` are present and generally enforced, ensuring basic code style consistency.
- **Print Statements**: Widespread use of `print()` instead of `logging` remains a major hygiene issue (B-001).
- **Type Hinting**: Present in newer files but inconsistent in legacy scripts.
- **Docstrings**: Many public functions lack compliant docstrings (Google/NumPy style).
- **Security**: No hardcoded secrets detected in a broad scan, but input validation is minimal.

## Top 10 Hygiene Risks

1. **Print Debugging** (Severity: MAJOR): `print()` spams stdout, making production logging useless.
2. **Missing Docstrings** (Severity: MAJOR): Reduces maintainability and auto-doc generation.
3. **Wildcard Imports** (Severity: MINOR): Found in some test files (`from x import *`).
4. **Complex Functions** (Severity: MAJOR): High cyclomatic complexity in Game loops.
5. **Magic Numbers** (Severity: MINOR): Hardcoded constants in game logic.
6. **Shadowing Names** (Severity: MINOR): Variable names shadowing built-ins.
    7. **Mutable Defaults** (Severity: MAJOR): Arguments using `[]` or `{}` as defaults.
8. **Unused Imports** (Severity: NIT): Leftover from refactoring.
9. **Commented Out Code** (Severity: NIT): "Dead" code blocks.
10. **Inconsistent Naming** (Severity: NIT): Mixed camelCase and snake_case in some modules.

## Scorecard

| Category                | Description                     | Score |
| ----------------------- | ------------------------------- | ----- |
| Ruff Compliance         | Zero violations across codebase | 9/10  |
| Mypy Compliance         | Strict type safety              | 8/10  |
| Black Formatting        | Consistent formatting           | 10/10 |
| AGENTS.md Compliance    | All standards met               | 7/10  |
| Security Posture        | No secrets, safe patterns       | 8/10  |
| Repository Organization | Clean, intuitive structure      | 6/10  |
| Dependency Hygiene      | Minimal, pinned, secure         | 8/10  |

## Linting Violation Inventory

| File | Ruff Violations | Mypy Errors | Black Issues |
| ---- | --------------- | ----------- | ------------ |
| `src/games/Zombie_Survival/src/game.py` | E501 (Line too long) | 5 | 0 |
| `tools_launcher.py` | T201 (print found) | 2 | 0 |
| `scripts/run_assessment.py` | None | 0 | 0 |

## Security Audit

| Check | Status | Evidence |
| ----- | ------ | -------- |
| No hardcoded secrets | ✅ | grep scan clean |
| .env.example exists | ❌ | Not found |
| No eval()/exec() usage | ✅ | grep scan clean |
| Safe file I/O | ✅ | `with open(...)` used |

## Findings Table

| ID    | Severity | Category | Location | Symptom | Root Cause | Fix | Effort |
| ----- | -------- | -------- | -------- | ------- | ---------- | --- | ------ |
| B-001 | Major    | Hygiene  | Multiple | `print()` usage | Developer habit | Replace with `logging.info()` | M |
| B-002 | Major    | Hygiene  | `src/`   | Missing Docstrings | rushed dev | Add docstrings | L |
| B-003 | Minor    | Hygiene  | `tests/` | Wildcard Import | `from ... import *` | Explicit imports | S |

## Refactoring Plan

**48 Hours**
- Configure `ruff` to ban `print()` (T201).
- Fix all `E501` line length violations.

**2 Weeks**
- Replace all `print()` with `logging`.
- Add docstrings to all public API functions.

**6 Weeks**
- Enforce strict `mypy` across the entire `src/` directory.

## Diff Suggestions

```python
# Before
def calculate(x):
    print(f"Calculating {x}")
    return x * 2

# After
import logging
logger = logging.getLogger(__name__)

def calculate(x: int) -> int:
    """Calculate double the input."""
    logger.debug(f"Calculating {x}")
    return x * 2
```
