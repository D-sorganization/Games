# Assessment G: Dependencies

## Grade: 8/10

## Analysis
Dependencies are managed via a root `requirements.txt`. The list is concise (`pygame`, `opencv-python`, `numpy`, `pytest`). However, the lack of a lock file (like `package-lock.json` or `poetry.lock`) means builds are not strictly reproducible if transitive dependencies update.

## Strengths
- **Minimalism**: Keeps the dependency tree relatively shallow.
- **Standard Libraries**: Heavy reliance on standard `pathlib`, `logging`, `subprocess`.

## Weaknesses
- **No Lock File**: Installing from `requirements.txt` might yield different versions in the future.
- **Heavy Packages**: `opencv-python` is a large dependency if only used for minor image processing (e.g., intro video).

## Recommendations
1.  **Lock Dependencies**: Use `pip-tools` (pip-compile) or `poetry` to generate a lock file to ensure reproducible builds.
2.  **Review OpenCV Usage**: If OpenCV is only used for playing a video, consider if `pygame`'s native movie support (or a lighter alternative) suffices to reduce install size.
