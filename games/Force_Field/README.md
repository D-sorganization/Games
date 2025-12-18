# Force Field - Arena Combat

A raycasting-based first-person shooter game built with Python and Pygame, featuring a 90x90 map with walls, buildings, and challenging bot enemies. Fight through increasingly difficult waves of enemies in an arena combat experience!

## Features

### Combat System
- **Rifle Weapon**: Realistic rifle rendering in first-person view
- **3 Enemy Bots per Level**: Bots spawn in three corners while you spawn in the fourth
- **Smart Bot AI**: Bots track, chase, and attack the player
- **Level Progression**: Each level increases difficulty
  - Bots gain +3 health per level
  - Bots gain +2 damage per level
  - Starting stats: 50 HP, 10 damage
- **Hit Detection**: Accurate shooting with line-of-sight checks
- **Health System**: Player has 100 HP, tracked with visual health bar

### Game Modes
- **Start Menu**: Working start button to begin the game
- **Arena Combat**: Fight waves of bots
- **Level Complete Screen**: Progress to next level after killing all bots
- **Game Over Screen**: Shows stats when player dies

### Map & Environment
- **90x90 Map Grid**: Massive arena with room for tactical gameplay
- **First-Person Perspective**: Raycasting engine for 3D rendering (Wolfenstein 3D style)
- **Multiple Buildings**:
  - Large rectangular buildings (top-left)
  - Medium building (top-right)
  - L-shaped structure (bottom-left)
  - Square building (bottom-right)
  - Central courtyard with walls
  - Scattered walls for cover

### Controls & UI
- **Movement**:
  - WASD: Move forward/back, strafe left/right
  - Mouse: Look around
  - Arrow keys: Alternative rotation
- **Combat**:
  - Left Click: Aim
  - Right Click: Shoot rifle
  - ESC: Return to menu
- **HUD Display**:
  - Health bar with color-coded status
  - Level counter
  - Enemy counter
  - Ammo counter
  - Real-time minimap showing player (green) and enemies (red)
  - Crosshair with center dot
- **Visual Effects**:
  - Muzzle flash when shooting
  - Rifle weapon model
  - Depth-based shading

### Spawn System
Each level, the four corners of the map are randomly assigned:
- Player spawns in one corner
- Three bots spawn in the other three corners
- Ensures fair and varied starting positions

## How to Play

### Starting the Game
1. Run `python force_field.py`
2. Click the **START GAME** button
3. You'll spawn in a random corner with 3 bots in the other corners

### Gameplay Loop
1. **Navigate** the 90x90 map using WASD
2. **Find** and **eliminate** all 3 enemy bots
3. **Use cover** from buildings and walls to avoid bot attacks
4. **Check minimap** (top-right) to locate enemies
5. **Complete the level** by killing all bots
6. **Progress** to next level with stronger enemies
7. **Survive** as long as possible!

### Strategy Tips
- Use buildings and walls as cover
- Watch your health bar - bots deal damage when they have line of sight
- Bots will chase you relentlessly
- Check minimap to avoid being surrounded
- Higher levels = tougher bots (more HP and damage)

## Game Stats

### Player Stats
- Health: 100 HP
- Rifle Damage: 25 HP per shot
- Rifle Range: 15 units
- Movement Speed: 0.1 units/frame
- Ammo: 999 (unlimited shooting)

### Bot Stats (Level 1)
- Health: 50 HP (increases by +3 per level)
- Damage: 10 HP (increases by +2 per level)
- Speed: 0.05 units/frame
- Attack Range: 10 units
- Attack Cooldown: 60 frames (~1 second)

### Example Progression
- **Level 1**: Bots have 50 HP, deal 10 damage
- **Level 2**: Bots have 53 HP, deal 12 damage
- **Level 3**: Bots have 56 HP, deal 14 damage
- **Level 5**: Bots have 62 HP, deal 18 damage
- **Level 10**: Bots have 77 HP, deal 28 damage

## Controls Summary

### Menu
- **Mouse**: Hover and click START GAME button

### Gameplay
- **W**: Move forward
- **S**: Move backward
- **A**: Strafe left
- **D**: Strafe right
- **SPACE**: Hold for Force Field Shield (Protects you, but you cannot move)
- **Mouse**: Look around
- **Left Click**: Aim
- **Right Click**: Shoot rifle
- **P**: Pause Game
- **ESC**: Return to menu

### Between Levels
- **SPACE**: Continue to next level
- **ESC**: Return to menu

## Requirements

- Python 3.x
- Pygame

## Installation

```bash
# Install pygame if not already installed
pip install pygame

# Navigate to game directory
cd "games/Force Field"

# Run the game
python force_field.py
```

## Technical Details

### Rendering
- **Engine**: Custom raycasting engine for pseudo-3D perspective
- **Resolution**: 1200x800 pixels
- **Performance**: 60 FPS target
- **FOV**: 60 degrees
- **Ray Count**: 600 rays (SCREEN_WIDTH // 2)

### Color Coding
- **Walls**: Different colors for different structures
  - Gray: Standard walls
  - Brown/Orange: Building structures
  - Light gray: Courtyard walls
- **Entities**:
  - Purple/Magenta: Enemy bots
  - Green: Player (on minimap)
  - Red: Enemies (on minimap)

### AI System
- Bots use pathfinding to chase the player
- Line-of-sight checks for both movement and attacks
- Collision avoidance with walls and other bots
- Attack cooldown system prevents instant-kills

### Code Structure
- `Map`: 90x90 grid with wall/building placement
- `Player`: Movement, shooting, health management
- `Bot`: AI behavior, combat, health scaling
- `Raycaster`: 3D rendering and bot detection
- `Button`: UI element for menus
- `Game`: Main game loop, state management, screens

## Game Screens

1. **Main Menu**: Title, instructions, and start button
2. **Gameplay**: First-person view with HUD
3. **Level Complete**: Shows level stats and progression
4. **Game Over**: Shows survival stats and final score

## Difficulty Progression

The game gets progressively harder:
- Each level adds 3 HP to bot health
- Each level adds 2 damage to bot attacks
- By level 10, bots are significantly more dangerous
- Strategic use of cover becomes essential at higher levels

## Future Enhancement Ideas

- Multiple weapon types (pistol, shotgun, etc.)
- Power-ups (health packs, ammo boxes, damage boost)
- More bot varieties with different behaviors
- Larger bot waves (4, 5, 6+ enemies)
- Different map layouts per level
- Boss fights every 5 levels
- Leaderboard/high score system
- Sound effects and music
- Textured walls and sprites

---

**Good luck, soldier! See how many levels you can survive!**
