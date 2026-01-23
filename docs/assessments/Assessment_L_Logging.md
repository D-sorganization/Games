# Assessment L: Logging

## Grade: 9/10

## Analysis
The application makes excellent use of Python's standard `logging` library. Both the launcher and individual games configure loggers. Critical errors are logged, and `Duum` even implements a file-based crash log.

## Strengths
- **Standard Library**: Uses built-in `logging` rather than print statements.
- **Context**: Logs include timestamps, log levels, and module names.
- **Crash Logging**: Implementation of `crash_log.txt` captures stack traces.

## Weaknesses
- **Console Dependency**: On Windows/GUI builds, `stdout/stderr` might be lost if not redirected to a file, making debugging hard for end-users.

## Recommendations
1.  **Rolling File Handler**: Configure the logging system to write to a rotating log file in a user data directory (`appdirs`) so logs persist after the application closes.
2.  **Global Exception Hook**: Implement `sys.excepthook` in the launcher to catch and log unhandled exceptions from all sources.
