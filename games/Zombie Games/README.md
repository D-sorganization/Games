# Zombie Shooter Games

This folder contains three zombie-themed first-person shooter games, each with unique gameplay mechanics.

## Games

### 1. Doom Raycaster (`doom-raycaster/`)
A classic Doom-style raycaster FPS with:
- **Graphics**: Retro 2D raycasting engine (pseudo-3D)
- **Weapons**: Pistol and Rifle with weapon switching (keys 1/2)
- **Features**:
  - Minimap (toggle with M)
  - Holster/draw weapon (H key)
  - Doors that can be opened (E key)
  - Sprint mode (hold Shift)
- **Objective**: Navigate the maze, kill all zombies and the boss, reach the exit

### 2. Hallway Survival (`hallway-survival/`)
A 3D corridor shooter with:
- **Graphics**: Full 3D using Three.js
- **Weapons**: Pistol (60 rounds) and Rifle (90 rounds)
- **Features**:
  - Weapon switching (keys 1/2)
  - Sprint and jump mechanics
  - Cover obstacles in the hallway
  - Boss enemy with enhanced health
- **Objective**: Survive the zombie horde and defeat the boss

### 3. Hallway Enhanced (`hallway-enhanced/`)
An enhanced version of the hallway shooter with:
- **Graphics**: Full 3D using Three.js
- **Weapons**: Pistol with 120 rounds
- **Features**:
  - Fireball attacks from boss enemy
  - Kill counter
  - Enhanced sprint and jump mechanics
  - Cover obstacles
  - Damage flash effects
- **Objective**: Eliminate all zombies and survive boss attacks

## Controls (All Games)

- **WASD** - Move
- **Mouse** - Look around
- **Right Click** - Aim (tighter FOV)
- **Left Click** - Fire weapon
- **Shift** - Sprint (hold)
- **Space** - Jump (3D games only)
- **1/2** - Switch weapons (Doom Raycaster and Hallway Survival)
- **E** - Open doors (Doom Raycaster only)
- **H** - Holster/Draw weapon (Doom Raycaster only)
- **M** - Toggle minimap (Doom Raycaster only)

## Technical Notes

All games use local vendor files for Three.js dependencies to avoid CDN loading issues. Archived versions with CDN imports are available in `../archived-versions/`.

## Tips

- Use cover to avoid enemy attacks
- Aim (right-click) for better accuracy
- Conserve ammo for tougher enemies
- Sprint strategically to avoid getting cornered
