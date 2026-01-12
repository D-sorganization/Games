# Contributing to Games

Thank you for your interest in contributing! This document provides guidelines for contributing to the Games repository.

## 🚀 Quick Start

1. **Fork** the repository
2. **Clone** your fork locally
3. **Create a branch**: `git checkout -b feature/your-feature-name`
4. **Make changes** following our coding standards
5. **Test** your changes: `pytest`
6. **Commit** with a descriptive message
7. **Push** and create a Pull Request

## 📋 Development Setup

```bash
# Clone the repository
git clone https://github.com/D-sorganization/Games.git
cd Games

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install ruff black mypy pytest
```

## ✅ Code Standards

### Python

- **Formatter**: Black (default settings)
- **Linter**: Ruff
- **Type Checker**: MyPy (strict mode)
- Use type hints for all functions
- Follow Pygame best practices

### Before Committing

```bash
black .
ruff check . --fix
mypy games/ --ignore-missing-imports
pytest
```

## 🎮 Game Development Guidelines

### Adding a New Game

1. Create a new directory under `games/`
2. Follow the existing structure (src/, assets/, tests/)
3. Use the shared renderer components where possible
4. Add entry point script

### Performance

- Vectorize calculations with NumPy where possible
- Use sprite groups for efficient rendering
- Profile with cProfile for bottlenecks

### Assets

- Keep assets in the game's `assets/` directory
- Use standard formats (PNG, WAV)
- Credit sources in comments or README

## 🧪 Testing

- Add tests for game logic
- Run `pytest` before submitting PR
- Mock Pygame display for headless testing

## 📝 Commit Messages

Follow conventional commits:

- `feat:` New feature or game
- `fix:` Bug fix
- `docs:` Documentation
- `perf:` Performance improvement

Example: `feat(duum): Add wall texture support`

## 📖 Documentation

- Update CHANGELOG.md under [Unreleased]
- Document game controls in game README
- Add docstrings to public functions

## 🤝 Pull Request Process

1. Ensure CI passes (ruff, black, mypy)
2. Test gameplay manually
3. Update documentation
4. Request review from maintainers
