# Force Field - Development Guide

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- Git
- Virtual environment tool (venv, conda, etc.)

### Setup Development Environment

```bash
# Clone the repository
git clone <repository-url>
cd Games/games/Force_Field

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install

# Run the game
python force_field.py
```

## 🏗️ Architecture Overview

### Core Components

```
Force_Field/
├── src/                    # Source code
│   ├── game.py            # Main game loop and state management
│   ├── player.py          # Player character logic
│   ├── bot.py             # Enemy AI and behavior
│   ├── map.py             # Level generation and collision
│   ├── raycaster.py       # 3D rendering engine
│   ├── renderer.py        # Graphics rendering
│   ├── ui_renderer.py     # User interface
│   ├── sound.py           # Audio management
│   ├── constants.py       # Game configuration
│   ├── config.py          # Runtime configuration
│   ├── security.py        # Security utilities
│   └── performance_monitor.py  # Performance tracking
├── tests/                 # Test suite
├── assets/                # Game assets (sounds, images)
└── docs/                  # Documentation
```

### Key Design Patterns

- **Component-based Architecture**: Game entities are composed of reusable components
- **State Machine**: Game states (menu, playing, paused) are managed centrally
- **Observer Pattern**: Events are handled through a centralized system
- **Strategy Pattern**: Different AI behaviors and weapon types

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run specific test file
python -m pytest tests/test_game_logic.py -v

# Run performance tests
python -m pytest tests/test_performance.py -v
```

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **Performance Tests**: Performance monitoring validation
- **Security Tests**: Security feature validation

## 🔧 Code Quality

### Linting and Formatting

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/ --ignore-missing-imports

# Security scanning
bandit -r src/
```

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

- **Black**: Code formatting
- **Ruff**: Linting and import sorting
- **MyPy**: Type checking
- **Bandit**: Security scanning

## 🎮 Game Development

### Adding New Features

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/new-weapon-system
   ```

2. **Implement Feature**
   - Add code in appropriate modules
   - Follow existing patterns and conventions
   - Add comprehensive tests

3. **Test Thoroughly**
   ```bash
   python -m pytest tests/ -v
   ruff check src/
   black --check src/
   ```

4. **Create Pull Request**
   - Use conventional commit messages
   - Include tests and documentation
   - Ensure CI passes

### Adding New Weapons

1. **Update Constants**
   ```python
   # In src/constants.py
   WEAPONS["new_weapon"] = {
       "name": "New Weapon",
       "damage": 50,
       "range": 20,
       # ... other properties
   }
   ```

2. **Implement Logic**
   - Add weapon behavior in `player.py`
   - Add rendering in `renderer.py`
   - Add sound effects in `sound.py`

3. **Add Tests**
   ```python
   def test_new_weapon_functionality(self):
       player = Player(10, 10, 0)
       player.switch_weapon("new_weapon")
       # Test weapon behavior
   ```

### Adding New Enemy Types

1. **Define Enemy Type**
   ```python
   # In src/constants.py
   ENEMY_TYPES["new_enemy"] = {
       "color": (255, 0, 0),
       "health_mult": 1.5,
       "speed_mult": 0.8,
       # ... other properties
   }
   ```

2. **Implement AI Behavior**
   - Extend `Bot` class with new behaviors
   - Add specific movement patterns
   - Add attack patterns

## 🔒 Security Guidelines

### Save File Security
- All save files are validated for path traversal
- Content is scanned for suspicious patterns
- File sizes are limited to prevent DoS

### Input Validation
- All user inputs are sanitized
- File paths are validated and restricted
- Configuration values are range-checked

### Secrets Management
- Use `.env` files for configuration
- Never commit sensitive data
- Use environment variables for secrets

## 📊 Performance Optimization

### Profiling

```bash
# Profile the game
python -m cProfile -o profile.stats force_field.py

# Analyze profile
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(20)"
```

### Performance Monitoring

The game includes built-in performance monitoring:

```python
from src.performance_monitor import PerformanceMonitor

monitor = PerformanceMonitor()
monitor.start_frame()
# ... game logic ...
monitor.end_frame()

print(f"FPS: {monitor.get_fps():.1f}")
```

### Optimization Tips

1. **Rendering Optimization**
   - Adjust `RENDER_SCALE` in constants
   - Reduce `NUM_RAYS` for lower quality/higher performance
   - Optimize raycasting algorithm

2. **AI Optimization**
   - Limit bot update frequency
   - Use spatial partitioning for collision detection
   - Implement level-of-detail for distant bots

3. **Memory Optimization**
   - Reuse particle objects
   - Limit particle count
   - Use object pooling for projectiles

## 🐛 Debugging

### Debug Mode

Enable debug mode via environment variable:

```bash
export FORCE_FIELD_DEBUG=true
export FORCE_FIELD_SHOW_DEBUG_INFO=true
python force_field.py
```

### Common Issues

1. **Performance Issues**
   - Check FPS counter
   - Review performance monitor output
   - Reduce render scale or map size

2. **Audio Issues**
   - Ensure pygame audio is initialized
   - Check audio file formats
   - Verify volume settings

3. **Collision Issues**
   - Enable debug visualization
   - Check map generation
   - Verify collision detection logic

## 📝 Contributing

### Code Style
- Follow PEP 8 guidelines
- Use type hints for all functions
- Write comprehensive docstrings
- Add unit tests for new features

### Commit Messages
Use conventional commit format:
- `feat(scope): description`
- `fix(scope): description`
- `docs(scope): description`
- `test(scope): description`

### Pull Request Process
1. Create feature branch
2. Implement changes with tests
3. Ensure all CI checks pass
4. Request code review
5. Address feedback
6. Merge when approved

## 📚 Resources

- [Pygame Documentation](https://www.pygame.org/docs/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Raycasting Tutorial](https://lodev.org/cgtutor/raycasting.html)
- [Game Development Patterns](https://gameprogrammingpatterns.com/)

## 🆘 Support

For questions or issues:
1. Check existing documentation
2. Search GitHub issues
3. Create new issue with detailed description
4. Include error logs and system information