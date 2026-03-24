# Assessment M: Configuration Management

## Executive Summary
Configuration is largely handled via Python constants files (e.g., `constants.py`) rather than external configuration files.

## Scorecard
| Category | Description | Weight | Score | Evidence / Remediation |
|---|---|---|---|---|
| Modifiability | Ability to change settings without recompiling | 2x | 6/10 | Constants require code changes to modify game behavior. |
| Environment | Usage of ENV vars | 2x | 8/10 | CI uses ENV vars appropriately, but games do not. |

## Findings Table
| ID | Severity | Category | Location | Symptom | Root Cause | Fix | Effort |
|---|---|---|---|---|---|---|---|
| M-001 | Major | Hardcoding | `game_launcher.py` | Adding games requires modifying Python. | The `GAMES` list is hardcoded. | Use a JSON manifest or environment variable config. | S |
