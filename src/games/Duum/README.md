# Duum - The Reimagining

**Duum** is a high-octane Python FPS that reimagines the classic Doom experience using a custom raycasting engine. It features fast-paced combat, projectile-based weaponry (including a minigun), and a variety of enemy types.

## Features

- **Custom Raycasting Engine**: Supports vertical pitch (looking up/down), gradient sky/floors, and dynamic resolution scaling.
- **Weaponry**: Includes projectile-based weapons like the Minigun and Rocket Launcher, with specific logic for spin-up/spin-down and AOE damage.
- **Enemies**: Diverse enemy behaviors including:
  - **Melee**: Ninja-style attacks.
  - **Ranged**: Projectile attacks.
  - **Special**: Beast and Sniper variants.
- **Modern Controls**: Mouse look (with vertical pitch), WASD movement, and strafing.
- **Visuals**: Depth fog, visual bullet traces, and sprite-based rendering.

## Controls

- **WASD**: Move
- **Mouse**: Look / Aim
- **Left Click**: Fire Weapon
- **Space**: Jump (if applicable) / Interact
- **F9**: Toggle dynamic resolution scaling
- **Esc**: Pause / Menu

## How to Run

From the root of the repository:

```bash
python game_launcher.py
```
Select "Duum" from the launcher.

Alternatively, run directly from the terminal (ensure you are in the repo root):

```bash
# Set PYTHONPATH to include the game directory
PYTHONPATH=games/Duum python3 games/Duum/duum.py
```

## Development

- **Source Code**: `games/Duum/src/`
- **Tests**: `games/Duum/tests/`

To run tests:
```bash
PYTHONPATH=games/Duum python3 -m unittest discover games/Duum/tests
```
