# Doom-like FPS Game

A classic first-person shooter game built with HTML5 Canvas and JavaScript, featuring raycasting rendering (the same technique used in the original Doom).

## Features

- **3D Raycasting Engine**: Real-time 3D rendering using raycasting algorithm
- **First-Person Controls**:
  - WASD for movement (hold **Shift** to sprint)
  - Mouse for looking around (left click aims, right click fires)
  - E to open doors
- **Enemy AI**: Enemies track and attack the player with new variants (dinosaurs, demons, raiders)
- **Combat System**: Health, ammo, pistol/rifle loadout, and damage mechanics
- **Map Overlay**: Toggleable minimap to help with navigation
- **Weapon Handling**: Ability to holster and re-draw your weapon
- **Zombie Flavor**: Zombie-themed jump scare overlay when you die
- **Interactive Environment**: Doors that can be opened
- **Win/Lose Conditions**: Eliminate all enemies to reach the exit and win

## How to Play

1. Open `index.html` in a modern web browser
2. Click "START GAME"
3. Use WASD to move, mouse to look around, hold Shift to sprint
4. Left click to aim, right click to fire (pistol starts with 120 ammo, rifle with 90)
5. Press E to open doors (gray walls)
6. Kill all enemies to unlock the exit (green wall)
7. Don't let your health reach 0!

## Game Elements

- **Brown Walls**: Solid obstacles
- **Gray Walls**: Doors (press E to open)
- **Green Wall**: Exit (only accessible after killing all enemies)
- **Enemies**: Demons, dinosaurs, and raiders that chase and shoot at you
- **Health**: Starts at 100, decreases when enemies attack
- **Ammo**: Starts at 120 pistol rounds and 90 rifle rounds

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
| Left Click | Aim |
| Right Click | Shoot |
| E | Open door |
| H | Holster/draw weapon |
| M | Toggle minimap |
| 1 / 2 | Switch pistol / rifle |

## Tips

- Conserve ammo - pistol has 120 rounds and rifle has 90, but bosses soak damage
- Each enemy takes multiple shots to kill
- Keep moving to avoid enemy fire
- Enemies deal varied damage based on their type
- Use doors strategically to control enemy approach

Enjoy the game!
