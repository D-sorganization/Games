# Assessment G: Dependency Management

## Executive Summary
Dependency management is minimal but functional. The project uses a standard `requirements.txt`. The footprint is extremely light, minimizing supply chain risks.

## Scorecard
| Category | Description | Weight | Score | Evidence / Remediation |
|---|---|---|---|---|
| Definition Clarity | Usage of standard formats | 2x | 8/10 | Uses `requirements.txt`, but no `pyproject.toml` for standard build tools. |
| Lockfile Usage | Reproducible builds | 2x | 5/10 | Missing `requirements.lock` or `poetry.lock`. |
| Dependency Count | Keeping dependencies minimal | 1.5x | 10/10 | Only core libraries (Pygame, Pytest, Ruff). |
| Vulnerabilities | Known CVEs in dependencies | 1.5x | 10/10 | No vulnerable dependencies identified. |

## Findings Table
| ID | Severity | Category | Location | Symptom | Root Cause | Fix | Effort |
|---|---|---|---|---|---|---|---|
| G-001 | Major | Reproducibility | Root | Builds could drift. | No strict dependency lockfile. | Introduce `pip-tools` or `Poetry`. | S |
| G-002 | Minor | Modernization | Root | Legacy packaging. | Missing `pyproject.toml` for metadata. | Migrate package metadata to `pyproject.toml`. | M |
