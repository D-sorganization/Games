# FPS Shooter Game

A raycasting-based first-person shooter game built with Python and Pygame, featuring a 90x90 map with walls and buildings.

## Features

- **90x90 Map Grid**: Large map with plenty of room for exploration
- **First-Person Perspective**: Raycasting engine for 3D rendering (Wolfenstein 3D style)
- **Buildings and Walls**: Multiple structures including:
  - Large rectangular buildings
  - L-shaped structures
  - Central courtyard
  - Scattered walls for cover
- **Smooth Controls**:
  - WASD for movement (forward, back, strafe left/right)
  - Mouse look for aiming
  - Arrow keys as alternative rotation controls
- **Shooting Mechanics**:
  - Left-click to shoot
  - Ammo counter
  - Muzzle flash effect
- **HUD Display**:
  - Health indicator
  - Ammo counter
  - Minimap showing full map layout and player position
  - Crosshair
- **Performance**: Runs at 60 FPS

## Map Layout

The 90x90 map features:

- **Border walls**: Complete perimeter walls
- **Building 1**: Large rectangular structure (top-left, rows 10-25, cols 10-30)
- **Building 2**: Medium building (top-right, rows 10-20, cols 60-75)
- **Building 3**: L-shaped building (bottom-left, rows 60-80, cols 10-40)
- **Building 4**: Square building (bottom-right, rows 65-80, cols 65-80)
- **Central courtyard**: Walled area in the center (rows/cols 40-50)
- **Scattered walls**: Additional cover throughout the map

## Controls

- **W**: Move forward
- **S**: Move backward
- **A**: Strafe left
- **D**: Strafe right
- **Mouse**: Look around
- **Arrow Keys**: Alternative rotation (Left/Right)
- **Left Click**: Shoot
- **ESC**: Quit game

## Requirements

- Python 3.x
- Pygame

## Installation

```bash
# Install pygame if not already installed
pip install pygame

# Run the game
python fps_shooter.py
```

## How to Play

1. Run the game using the command above
2. Use WASD to navigate through the map
3. Use your mouse to look around
4. Left-click to shoot
5. Check the minimap (top-right) to navigate the 90x90 map
6. Explore the different buildings and structures

## Technical Details

- **Rendering**: Raycasting algorithm for pseudo-3D perspective
- **Map Size**: 90x90 grid
- **Resolution**: 1200x800 pixels
- **FOV**: 60 degrees
- **Color-coded walls**: Different wall types have different colors
  - Gray: Standard walls
  - Brown/Orange: Building structures
  - Light gray: Courtyard walls

## Code Structure

- `Map`: Handles the 90x90 grid and wall/building placement
- `Player`: Manages player position, rotation, and shooting
- `Raycaster`: Implements the raycasting algorithm for 3D rendering
- `Game`: Main game loop and rendering

## Future Enhancements

Possible additions:
- Enemies/targets
- Different weapon types
- Health packs and ammo pickups
- Multiple levels
- Sound effects
- Textures for walls
