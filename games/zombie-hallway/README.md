# Zombie Hallway

A browser-friendly first-person hallway run where you avoid zombies, stay out of melee range, and battle a fireball-throwing boss at the end of the corridor.

## How to play

1. Open `index.html` in a modern browser (Chrome/Firefox) with network access for the Three.js CDN.
2. Click **Enter the hallway** to lock the pointer.
3. Controls:
   - **Mouse Left**: Aim (locks pointer) and narrows the field of view while held
   - **Mouse Right**: Fire pistol (10 damage per shot)
   - **WASD**: Move
   - **Space**: Jump
4. Avoid zombies (10 damage per melee hit) and the boss (15 damage per melee hit plus slow fireballs). Each zombie has 80 HP; the boss has 160 HP. Your pistol deals 10 damage.
5. Hide behind occasional buildings in the hallway to break line of sight.

## Features

- Football-field-length hallway with walls, ceiling, and collision so you cannot walk through geometry
- A handful of buildings spaced down the run for cover
- Health UI and visible health bars above zombies and the boss
- Zombies pursue the player with leg animations tied to their movement speed
- Boss is double-sized with double health and shoots slow-moving fireballs in addition to melee damage
- Minimal styling HUD/reticle for a clean shooter feel
