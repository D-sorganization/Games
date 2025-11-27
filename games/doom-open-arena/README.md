# Doom-like Open-Arena FPS

A classic first-person shooter built with HTML5 Canvas and JavaScript, now placed in a wide-open arena to make navigation and combat readability clearer while keeping the raycasted 3D perspective.

## Features

- **3D Raycasting Engine**: Real-time 3D rendering using a raycasting algorithm
- **First-Person Controls**:
  - WASD for movement
  - Mouse for looking around
  - Click to shoot
  - E to open doors
- **Enemy AI**: Enemies track and attack the player with new variants (dinosaurs, demons, raiders)
- **Combat System**: Health, ammo, and damage mechanics
- **Map Overlay**: Toggleable minimap to help with navigation across the open arena
- **Weapon Handling**: Ability to holster and re-draw your weapon
- **Interactive Environment**: Doors that can be opened for new sightlines inside the central ruins
- **Win/Lose Conditions**: Eliminate all enemies to reach the exit and win

## How to Play

1. Open `index.html` in a modern web browser
2. Click "START GAME"
3. Use WASD to move, mouse to look around
4. Click to shoot enemies (you have 50 bullets)
5. Press E to open doors (gray walls)
6. Kill all enemies to unlock the exit (green wall)
7. Don't let your health reach 0!

## Game Elements

- **Brown Walls**: Solid obstacles and short ruins that provide cover in the open field
- **Gray Walls**: Doors (press E to open)
- **Green Wall**: Exit in the northeast corner (only accessible after killing all enemies)
- **Enemies**: Demons, dinosaurs, and raiders that chase and shoot at you through the open arena
- **Health**: Starts at 100, decreases when enemies attack
- **Ammo**: Starts at 50 bullets

## Arena Layout

- A mostly open 16x16 field with perimeter walls
- Sparse cover segments forming central ruins, including a single door to practice opening mechanics
- Exit tile tucked near the northeast side to encourage crossing the open ground once all enemies fall

## Technical Details

- Built with vanilla JavaScript and HTML5 Canvas
- Implements raycasting for 3D perspective
- Real-time enemy AI with pathfinding
- Collision detection
- Weapon animations and recoil
- HUD display

## Controls Summary

| Key | Action |
|-----|--------|
| W | Move forward |
| S | Move backward |
| A | Strafe left |
| D | Strafe right |
| Mouse | Look around |
| Click | Shoot |
| E | Open door |
| H | Holster/draw weapon |
| M | Toggle minimap |

## Tips

- Conserve ammo - you only have 50 bullets for 4 enemies
- Each enemy takes multiple shots to kill
- Keep moving to avoid enemy fire
- Enemies deal varied damage based on their type
- Use doors strategically to control enemy approach

Enjoy the game!
