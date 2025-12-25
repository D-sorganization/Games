# Wizard of Wor

A Python remake of the classic arcade game "Wizard of Wor". Navigate the maze, defeat the monsters, and survive as long as you can.

## Features

- **Classic Gameplay**: Arcade-style shooting and movement.
- **Maze Generation**: Dynamic maze layouts.
- **Enemies**: Various monster types with distinct behaviors.
- **Multiplayer**: Support for two players (co-op).

## Controls

### Player 1
- **WASD**: Move
- **Space**: Shoot

### Player 2 (if enabled)
- **Arrow Keys**: Move
- **Enter/Return**: Shoot

*(Note: Verify exact controls in-game or code)*

## How to Run

From the root of the repository:

```bash
python game_launcher.py
```
Select "Wizard of Wor" from the launcher.

Alternatively, run directly from the terminal:

```bash
python games/Wizard_of_Wor/wizard_of_wor/game.py
```

## Development

- **Source Code**: `games/Wizard_of_Wor/wizard_of_wor/`
- **Tests**: `games/Wizard_of_Wor/tests/`

To run tests:
```bash
PYTHONPATH=games/Wizard_of_Wor python3 -m unittest discover games/Wizard_of_Wor/tests
```
