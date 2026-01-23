# Assessment D: Error Handling

## Grade: 8/10

## Analysis
The application demonstrates robust error handling in key areas. The launcher protects against missing files and failed launches. The games wrap their main loops in try/except blocks.

## Strengths
- **Graceful Degradation**: Launcher doesn't crash if a game manifest is invalid.
- **Logging**: Extensive use of `logging` module.
- **Crash Logs**: `Duum` writes a `crash_log.txt` on failure.

## Weaknesses
- **Inconsistency**: `Force_Field` catches exceptions but re-raises them without writing a crash log, whereas `Duum` writes one.
- **User Feedback**: If a game fails to launch, the user might not see the error if the console window closes immediately.

## Recommendations
1.  **Unified Crash Handler**: Create a shared `CrashHandler` in `games.shared` that writes to a centralized log and potentially displays a GUI error message.
2.  **Subprocess Error Capture**: The launcher could capture `stderr` from game subprocesses and log it if the exit code is non-zero.
