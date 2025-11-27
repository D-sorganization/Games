# Doom-like FPS Game

A classic first-person shooter game built with HTML5 Canvas and JavaScript, featuring raycasting rendering (the same technique used in the original Doom).

## Features

- **3D Raycasting Engine**: Real-time 3D rendering using raycasting algorithm
- **First-Person Controls**:
  - WASD for movement
  - Mouse for looking around
  - Click to shoot
  - R to reload
  - ESC to pause and open the in-game menu
  - E to open doors
- **Enemy AI**: Enemies track and attack the player
- **Combat System**: Health, ammo, reloading, weapon switching (pistol, shotgun, BFG 2000), and damage mechanics
- **Gamepad Support**: Microsoft/Xbox-style controller mappings for movement, shooting, reloading, pausing, and swapping weapons
- **Pause Menu**: Resume or restart without leaving the browser tab
- **Improved HUD**: Clip and reserve ammo display plus contextual banner updates
- **Interactive Environment**: Doors that can be opened
- **Win/Lose Conditions**: Eliminate all enemies to reach the exit and win

## How to Play

1. Open `index.html` in a modern web browser
2. Click "START GAME"
3. Use WASD to move, mouse to look around
4. Use **1/2/3** (or **Q/F**) to swap between pistol, shotgun, and the BFG 2000
5. Click to shoot enemies; **R** reloads, **E** opens doors, **ESC** pauses/resumes
6. Xbox/Microsoft controller: left stick moves, right stick looks, **RT** shoots, **X** reloads, **Y** opens doors, **LB/RB** swap weapons, **Start** pauses
7. Kill all 5 enemies to unlock the exit (green wall)
8. Don't let your health reach 0!

## Game Elements

- **Brown Walls**: Solid obstacles
- **Gray Walls**: Doors (press E to open)
- **Green Wall**: Exit (only accessible after killing all enemies)
- **Red Monsters**: Enemies that chase and shoot at you
- **Health**: Starts at 100, decreases when enemies attack
- **Ammo**: Starts at 50 bullets

## Technical Details

- Built with vanilla JavaScript and HTML5 Canvas
- Implements raycasting for 3D perspective
- Real-time enemy AI with pathfinding
- Collision detection
- Weapon animations and recoil
- HUD display

## Controls Summary

| Control | Action |
|---------|--------|
| W / S | Move forward/backward |
| A / D | Strafe left/right |
| Mouse | Look around |
| Click | Shoot |
| 1 / 2 / 3 | Select pistol / shotgun / BFG 2000 |
| Q / F | Cycle weapons previous/next |
| R | Reload |
| E | Open door |
| ESC | Pause/Resume |
| Xbox/Microsoft controller | Left stick move, right stick look, **RT** shoot, **X** reload, **Y** interact, **LB/RB** swap weapons, **Start** pauses |

## Tips

- Conserve ammo - each weapon has its own reserve (pistol-friendly, limited BFG shots)
- Shotgun blasts multiple pellets per shot; line up close targets to maximize damage
- Keep moving to avoid enemy fire
- Enemies deal 10 damage per hit
- Use doors strategically to control enemy approach

Enjoy the game!
