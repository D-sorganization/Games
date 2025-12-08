This PR introduces a significant overhaul to the Force Field game, focusing on graphical fidelity, audio immersion, and stability.

## Key Changes

### Graphics

- **High-Fidelity Weapons:** Replaced primitive block rendering with detailed polygon-based models for the Pistol, Rifle, Shotgun, and Plasma Gun.
- **Enhanced Enemy Sprites:** completely rewritten enemy rendering with 'Doom-style' sprites featuring animated eyes, mouths, and drool effects.
- **Death Animations:** Enemies now melt into goo upon death and leave persistent corpses (puddles) in the arena.
- **Tetris:** Added gradient backgrounds and 3D bevel effects to blocks.

### Audio

- **New Sound Engine:** Implemented a new `SoundManager` with support for unique weapon sounds.
- **Procedural Sound Generation:** Added scripts to generate high-quality synthesized sounds for all weapons, impacts, and ambience.
- **Dynamic Heartbeat:** Added a tension system where a heartbeat sound plays faster as the player nears enemies.
- **Kill Combo Voice:** Added synthesized catchphrases ('COOL', 'AWESOME', 'BRUTAL') for kill streaks.
- **Darker Ambience:** Updated background music to a darker, more serious drone track.

### Gameplay & Stability

- **Crash Fix:** Fixed a reported crash when using the Bomb ('F' key) by adding robust error handling.
- **Enemy Spawning:** Improved level generation to ensure mixed enemy types and guaranteed Boss/Demon spawns at level end.
- **Weapon Feel:** Added visual recoil and bobbing animations.

## Testing Since Last Commit

- Validated game launch.
- Verified unique sounds for all weapons.
- Confirmed 'F' key no longer crashes the game.
- Verified enemy death animations and sound triggers.
