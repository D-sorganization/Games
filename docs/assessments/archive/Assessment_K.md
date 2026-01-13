# Assessment K Results: Reproducibility & Provenance

## Executive Summary

*   **Game Determinism**: Most logic is deterministic *if* the random seed is controlled. However, `random` usage is scattered and rarely seeded explicitly for gameplay.
*   **Procedural Gen**: `Force_Field` uses Cellular Automata. Without a fixed seed, map generation is random every time. This is good for "Replayability" but bad for "Reproducibility" (e.g., bug reporting).
*   **Version Tracking**: Git is the only version tracking. No semantic versioning of the game builds.
*   **Experiment Tracking**: Not applicable (this is not a research repo), though high scores are a form of "result tracking".

## Reproducibility Audit

| Component    | Deterministic? | Seed Controlled? | Notes |
| ------------ | -------------- | ---------------- | ----- |
| **Map Gen**  | ❌             | ❌               | Random every run. |
| **Enemy AI** | ❌             | ❌               | Random decisions. |
| **Physics**  | ✅             | N/A              | Deterministic logic. |

## Remediation Roadmap

**2 Weeks**:
*   Add a "Seed" option to `Force_Field` config.
*   Log the seed on startup to stdout/log file so bugs can be reproduced on the same map.

## Findings

| ID    | Severity | Category      | Location            | Symptom                            | Fix                                  |
| ----- | -------- | ------------- | ------------------- | ---------------------------------- | ------------------------------------ |
| K-001 | Minor    | Debugging     | `src/map.py`        | Cannot reproduce map bugs          | Log random seed used                 |
