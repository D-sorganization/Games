# Games Repository

A collection of fun game projects and interactive simulations.

## Projects

### Games

- **Tetris** (`games/tetris.py`) - Classic Tetris game implementation in Python
- **Zombie Games Collection** (`games/zombie-games/`) - Three browser FPS experiences (Doom-inspired arena plus two zombie hallway variants) with rifles, sprinting, and zombie jump scares
- **Wizard of Wor** (`games/wizard_of_wor/`) - Remake of the classic Wizard of Wor arcade game

### Simulations

- **RRT Path Planner** (`rrt_path_planner/`) - Star Wars themed Rapidly-Exploring Random Tree (RRT) path planning algorithm with 3D visualization

## Project Structure

```
Games/
├── games/              # Game implementations
│   ├── tetris.py
│   ├── zombie-games/
│   │   ├── doom-game/
│   │   ├── zombie-hallway-v1/
│   │   └── zombie-hallway-v2/
│   └── wizard_of_wor/
├── rrt_path_planner/   # RRT path planning simulation
├── python/             # Python utilities and shared code
├── matlab/             # MATLAB code and utilities
├── docs/               # Documentation
├── data/               # Data files
└── output/             # Output files
```

## Getting Started

Each game/simulation has its own requirements and setup instructions. See the README files in each project directory for specific details.

## Development

This repository follows the project template standards with:
- CI/CD workflows for quality checks
- Pre-commit hooks for code quality
- Type checking and linting
- Comprehensive testing

## License

MIT License - See LICENSE file for details.
