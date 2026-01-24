# Assessment: Configuration (Category M)

## Grade: 7/10

## Analysis
Configuration is distributed (manifests) and central (constants in launcher). However, the hardcoded paths that caused the structure issue lower the score.

## Strengths
- **Manifests**: Good decentralized config.
- **Constants**: Defined at top of files.

## Weaknesses
- **Hardcoded Paths**: `games/` vs `src/games/` hardcoding caused breakage.

## Recommendations
1. **Dynamic Paths**: Use relative paths from `__file__` reliably (which is attempted but failed due to folder move).
2. **Env Vars**: Support `GAMES_DIR` environment variable override.
