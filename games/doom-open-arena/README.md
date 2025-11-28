# Doom-like Open-Arena FPS

A classic first-person shooter built with HTML5 Canvas and JavaScript, now placed in a wide-open arena to make navigation and combat readability clearer while keeping the raycasted 3D perspective. This variant offers the strongest sense of space among the available Doom builds thanks to its open sightlines, enemy variety, and newly refined horizon rendering.

## Features

- **3D Raycasting Engine**: Real-time 3D rendering using a raycasting algorithm and layered
  sky/floor gradients for clear vertical perspective cues, now with parallax sky drift, aurora shimmer, and layered floor fog for depth
- **Cinematic Lighting**: Directional wall lighting with rim highlights, grounded enemy shadows, and a soft vignette to focus the view
- **10-Level Gauntlet**: Ten hand-authored arenas with distinct layouts, exits, and chokepoints inspired by classic Doom pacing
- **First-Person Controls**:
  - WASD for movement
  - Mouse for looking around
  - Click to shoot
  - E to open doors
- **Enemy AI**: Enemies track and attack the player with new variants (dinosaurs, demons, raiders)
- **Combat System**: Health, ammo, and damage mechanics with random weapon loadouts and per-level ammo top-ups
- **Map Overlay**: Toggleable minimap to help with navigation across the open arena
- **Weapon Handling**: Ability to holster and re-draw your weapon
- **Interactive Environment**: Doors that can be opened for new sightlines inside the central ruins
- **Win/Lose Conditions**: Clear each arena of enemies to open the exit, advance through all ten levels, and beat the campaign

## How to Play

1. Open `index.html` in a modern web browser
2. Click "START GAME"
3. Use WASD to move, mouse to look around
4. Click to shoot enemies (weapon and ammo amount are randomized each run)
5. Press E to open doors (gray walls)
6. Kill all enemies to unlock the exit (green wall), then step on it to travel to the next level
7. Clear all 10 arenas to win and don't let your health reach 0!

## Game Elements

- **Brown Walls**: Solid obstacles and short ruins that provide cover in the open field
- **Gray Walls**: Doors (press E to open)
- **Green Wall**: Exit that only activates after enemies fall, leading you to the following arena
- **Enemies**: Demons, dinosaurs, and raiders that chase and shoot at you through the open arena with randomized counts
- **Health**: Starts at 100, decreases when enemies attack
- **Ammo**: Starts from a random weapon loadout and tops up slightly every level

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

- Conserve ammo — your starting weapon and magazine size are randomized each run
- Enemy counts shift between levels, so sweep the whole arena before sprinting to the exit
- Keep moving to avoid enemy fire and use corners to break line of sight
- Enemies deal varied damage based on their type and per-run aggression roll
- Use doors strategically to control enemy approach

Enjoy the game!
