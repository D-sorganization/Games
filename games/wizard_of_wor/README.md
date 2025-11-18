# Wizard of Wor Remake

A faithful remake of the classic 1980 Atari arcade game "Wizard of Wor" built with Python and Pygame.

## Game Overview

Wizard of Wor is a dungeon crawler shooter where you navigate through mazes, battle various monsters, and try to survive as long as possible while racking up points. The game features:

- **Classic dungeon maze gameplay** with walls and corridors
- **Multiple enemy types** with different behaviors and difficulty levels
- **Radar system** showing enemy positions in real-time
- **Progressive difficulty** with levels getting harder
- **Score tracking** and lives system

## Enemy Types

### Burwor (Purple)
- **Speed**: Slow
- **Points**: 100
- **Behavior**: Chases player, doesn't shoot
- **Threat Level**: Low

### Garwor (Orange)
- **Speed**: Medium
- **Points**: 200
- **Behavior**: Chases player and shoots
- **Threat Level**: Medium

### Thorwor (Red)
- **Speed**: Fast
- **Points**: 300
- **Behavior**: Aggressive chaser, shoots frequently
- **Threat Level**: High

### Worluk (Cyan - Invisible)
- **Speed**: Slow
- **Points**: 1000
- **Behavior**: Invisible enemy that blinks in and out
- **Threat Level**: Special

### Wizard of Wor (Yellow)
- **Speed**: Very Fast
- **Points**: 2500
- **Behavior**: Appears when few enemies remain, extremely aggressive
- **Threat Level**: Maximum

## Controls

### Movement
- **W** or **↑** - Move Up
- **S** or **↓** - Move Down
- **A** or **←** - Move Left
- **D** or **→** - Move Right

### Actions
- **SPACE** - Shoot
- **ENTER** - Start game / Continue to next level / Restart
- **ESC** - Pause / Return to menu / Quit

## Installation

1. Make sure you have Python 3.7+ installed
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## How to Play

1. Run the game:
   ```bash
   python game.py
   ```

2. Press **ENTER** at the main menu to start

3. Navigate through the dungeon and shoot all enemies to complete the level

4. Avoid enemy bullets and direct contact with enemies

5. Use the radar in the top-right to track enemy positions

6. Clear all enemies to advance to the next level

## Gameplay Tips

- **Use the radar** - The mini-map shows all enemy positions, even invisible ones (in gray)
- **Corner enemies** - Trap enemies in corners or corridors for easy shots
- **Watch your back** - Enemies can shoot, so don't stand still
- **Wizard warning** - When you see the Wizard spawn, be extra careful - he's fast and deadly
- **Worluk hunting** - The invisible Worluk appears on levels 2+, watch the radar for gray dots

## Game Mechanics

### Scoring
- Clear levels to increase your score
- Bonus points for rare enemies like Worluk and the Wizard
- Try to beat your high score!

### Lives
- You start with 3 lives
- Lose a life when hit by enemy bullets or touching enemies
- Game over when all lives are lost

### Level Progression
- Each level increases in difficulty
- More dangerous enemy types appear in later levels
- Enemy spawn patterns change per level

## Technical Details

### Requirements
- Python 3.7+
- Pygame 2.5.0+

### Project Structure
```
wizard_of_wor/
├── game.py           # Main game loop and logic
├── player.py         # Player character class
├── enemy.py          # All enemy types
├── bullet.py         # Projectile system
├── dungeon.py        # Maze generation and collision
├── radar.py          # Mini-map radar system
├── constants.py      # Game constants and configuration
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

## Credits

- **Original Game**: Wizard of Wor © 1980 Midway Games
- **Remake**: Built with Python and Pygame
- **Version**: 1.0.0

## License

This is a fan remake created for educational purposes. All rights to the original Wizard of Wor belong to their respective owners.

---

Enjoy the game and try to defeat the Wizard of Wor! 🧙‍♂️
