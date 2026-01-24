# Assessment: Logging (Category L)

## Grade: 9/10

## Analysis
The `logging` module is used correctly in `game_launcher.py`, replacing `print` statements.

## Strengths
- **Standard Lib**: Uses Python's built-in `logging`.
- **Configuration**: Configured with timestamp and level.

## Weaknesses
- **Granularity**: Could benefit from file-based logging in addition to console, for post-mortem debugging of the launcher.

## Recommendations
1. **File Handler**: Add a `RotatingFileHandler` to the logger to persist logs.
