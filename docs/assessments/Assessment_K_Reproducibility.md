# Assessment K Results: Reproducibility & Provenance

## Executive Summary

- **Reproducibility**: The primary barrier to full reproducibility is the absence of a `requirements.lock` file. Two users might get different versions of `pygame` or `numpy`.
- **Determinism**: The game loops are generally deterministic (single-threaded). However, random number generation (`random` module) is not consistently seeded, meaning procedural generation (if any) varies per run.
- **Provenance**: There is no tracking of "game runs" or replays, so bugs are hard to reproduce exactly.
- **Environment**: No Dockerfile provided to guarantee OS-level dependencies.

## Top 10 Reproducibility Risks

1.  **Dependency Drift (Critical)**: `requirements.txt` allows floating versions.
2.  **Unseeded Randomness (Major)**: Procedural elements (enemy spawns) are not seeded.
3.  **OS Differences (Major)**: Rendering differences between OS (DirectX vs OpenGL via SDL) are not accounted for.
4.  **No Dockerfile (Minor)**: "Works on my machine" syndrome risk.
5.  **No Replay System (Minor)**: Cannot re-run a game session exactly.
6.  **Time Delta (Minor)**: Logic tied to `clock.tick()` might vary slightly on different CPUs.
7.  **Asset Hash (Nit)**: No check that assets are unmodified.
8.  **Config Versioning (Nit)**: Configs not versioned with code.
9.  **Log Provenance (Nit)**: Logs don't capture git commit hash.
10. **Hardware (Nit)**: Sound/Input hardware differences affect gameplay.

## Scorecard

| Category | Description | Score | Notes |
| :--- | :--- | :--- | :--- |
| Deterministic Execution | 100% | 9/10 | Single thread, no race conditions. |
| Version Tracking | Full | 4/10 | Missing lock file. |
| Random Seed Handling | Documented | 6/10 | Implicit system time seed. |
| Result Reproduction | Bit-exact | 5/10 | Env dependent. |

## Reproducibility Audit

| Component | Deterministic? | Seed Controlled? | Notes |
| :--- | :--- | :--- | :--- |
| Game Logic | ✅ | ❌ | Spawns are random. |
| Rendering | ✅ | N/A | Floating point diffs possible. |
| Physics | ✅ | N/A | Simple AABB. |

## Findings Table

| ID | Severity | Category | Location | Symptom | Root Cause | Fix | Effort |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| K-001 | Critical | Reproducibility | Root | Dependency Drift | No lock file | Generate lock | S |
| K-002 | Major | Reproducibility | Games | Random Spawns | No seed config | Allow fixed seed | S |

## Remediation Roadmap

**48 Hours**:
- Create `requirements.lock`.

**2 Weeks**:
- Add a `--seed` argument to `game_launcher.py` and pass it to games.

**6 Weeks**:
- Create a `Dockerfile` for a standardized testing environment.

## Diff Suggestions

### Seeding
```python
<<<<<<< SEARCH
import random
# ...
    def spawn_enemy(self):
        x = random.randint(0, 100)
=======
import random
# ...
    def set_seed(self, seed):
        random.seed(seed)

    def spawn_enemy(self):
        x = random.randint(0, 100)
>>>>>>> REPLACE
```
