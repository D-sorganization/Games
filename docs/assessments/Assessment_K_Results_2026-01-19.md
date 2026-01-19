# Assessment K Results: Reproducibility & Provenance

## Executive Summary

Reproducibility is high due to simple requirements. Games are deterministic in logic (seeds can be set) but rely on `random` module.

*   **Determinism**: Games use `random`. No explicit seed control for gameplay (replayability).
*   **Environment**: `requirements.txt` locks dependencies reasonably well.

## Scorecard

| Category | Score | Evidence | Remediation |
| :--- | :--- | :--- | :--- |
| **Deterministic Execution** | **5/10** | `random` used freely. | Add seed config. |
| **Version Tracking** | **8/10** | Git used effectively. | Tag releases. |
| **Random Seed Handling** | **2/10** | Not exposed. | Add `--seed` arg. |

## Remediation Roadmap

**2 Weeks**:
*   Add a `--seed` command line argument to all games to allow deterministic runs (useful for testing and speedrunning).
