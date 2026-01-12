# Jules' Game Collection

[![CI Standard](https://github.com/D-sorganization/Games/actions/workflows/ci-standard.yml/badge.svg)](https://github.com/D-sorganization/Games/actions/workflows/ci-standard.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Welcome to the Game Collection repository! This project hosts a variety of games developed in Python (using Pygame) and Web technologies, all accessible through a unified launcher.

## 🎮 Available Games

### 1. **Force Field**

A robust First-Person Shooter (FPS) featuring a custom raycasting engine, 3D environments, and challenging bot AI.

- **Location**: `games/Force_Field/`
- **Type**: Python (Pygame)

### 2. **Duum - The Reimagining**

A high-octane FPS reimagining the classic Doom experience with modern mechanics, projectile weapons (Minigun!), and diverse enemies.

- **Location**: `games/Duum/`
- **Type**: Python (Pygame)

### 3. **Tetris (Enhanced)**

A modern take on the classic puzzle game with hold mechanics, combos, particle effects, and difficulty selection.

- **Location**: `games/Tetris/`
- **Type**: Python (Pygame)

### 4. **Wizard of Wor**

A remake of the classic arcade shooter where you battle monsters in a maze. Supports 2-player co-op.

- **Location**: `games/Wizard_of_Wor/`
- **Type**: Python (Pygame)

### 5. **Peanut Butter Panic**

A quirky arcade-style game (Python package).

- **Location**: `games/Peanut_Butter_Panic/`
- **Type**: Python (Pygame)

### 6. **Zombie Games (Web)**

A collection of web-based 3D survival shooters.

- **Location**: `games/Zombie_Games/`
- **Type**: Web (HTML/JS)

## 🚀 How to Play

### Using the Game Launcher

The easiest way to play is using the unified game launcher:

```bash
python game_launcher.py
```

This will open a GUI where you can select and launch any game.

### Running Individual Games

You can also launch games directly from the terminal. See the `README.md` in each game's directory for specific instructions.

Example:

```bash
# Run Force Field
python games/Force_Field/force_field.py
```

## 🛠️ Development

### Prerequisites

- Python 3.8+
- Pygame (`pip install pygame`)
- Other dependencies as listed in `requirements.txt` or game-specific requirements.

### Installation

1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Documentation

- **AGENTS.md**: Guidelines for AI agents working on this repo.
- **Game Docs**: Each game folder contains its own `README.md` with detailed info.

## 🤝 Contributing

Feel free to submit Pull Requests to improve existing games or add new ones! Please follow the coding standards outlined in `AGENTS.md`.
