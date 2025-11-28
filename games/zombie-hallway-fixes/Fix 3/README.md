# Zombie Hallway FPS (v1)

A lightweight Three.js demo of a long hallway survival run. Survive zombies and a boss while staying mobile.

Three.js and PointerLockControls are bundled locally under `../../vendor/three` so the game runs without CDN access.

## Controls
- Click canvas to lock pointer
- WASD to move, Space to jump, Shift to sprint
- Left click to shoot, Right click to aim (tighter FOV)
- Press **1** for pistol or **2** for rifle (harder hits, shorter cooldown)

## Gameplay
- Zombies deal 10 damage in melee and have 80 HP
- Boss is larger, fires slow fireballs, and has 160 HP
- Pistol deals 10 damage per shot; rifle deals 18. Ammo starts at 60 pistol / 90 rifle.
- Zombie jump scare appears when the player dies

Open `index.html` in a browser to play.
