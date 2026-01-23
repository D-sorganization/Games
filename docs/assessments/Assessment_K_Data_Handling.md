# Assessment K: Data Handling

## Grade: 8/10

## Analysis
The application handles data primarily through JSON manifest files and direct file system access for assets. Save data is handled via simple text files. This approach is appropriate for the scale of the project (arcade games).

## Strengths
- **JSON Manifests**: Structured metadata for games allows for flexible configuration.
- **Asset Loading**: Games handle their own asset paths, often using `pathlib` for cross-platform compatibility.

## Weaknesses
- **Save format**: The save system (writing a single integer to `savegame.txt`) is very primitive and brittle. It lacks validation, checksums, or structure (JSON).
- **Hardcoded Paths**: Some asset loading relies on specific directory structures that, if changed, would break the game.

## Recommendations
1.  **Structured Saves**: Transition `savegame.txt` to `savegame.json` to allow saving more state (score, inventory) and enable validation.
2.  **Asset Manager**: Create a shared `AssetManager` to centralize path resolution and error handling for missing files.
