# Sound Functionality Checklist

Please check the following audio features in the Force Field game:

## Intro Sequence

- [ ] **Water Sound**: Should play immediately when the "Upstream Drift" fish intro appears (Phase 1).
- [ ] **Music Box Intro**: Should play a creepy untuned music box melody shortly after the water sound (approx 2 seconds in).
- [ ] **Demented Laugh**: Should play when "FROM THE DEMENTED MIND OF JASPER" text appears (Phase 2).

## In-Game Audio

- [ ] **Background Music**: Should cycle through 4 tracks based on level (Bell Trap -> Drum -> Horror -> Piano).
- [ ] **Gun Sounds**: Pistol, Rifle, and Shotgun should sound significantly louder/punchier than before.
- [ ] **Bomb**: Pressing 'F' should trigger a synthesized explosion sound (Safe WAV) and NOT crash the game.
- [ ] **Enemy Scream**: Enemies should emit a fast, high-pitched scream when they die (2x speed effect).
- [ ] **Player Damage**:
  - [ ] **Oww**: An "Oww" sound should play immediately when you take damage.
  - [ ] **Groan**: If health is below 50%, a male groan should play intermittently (every ~4 seconds).
- [ ] **Heartbeat & Breath**:
  - [ ] **Dynamic Speed**: Heartbeat and Breath sounds should faster as you get closer to enemies, but with smoother transitions (not erratic).
  - [ ] **Pause Menu**: When paused, the Heartbeat and Breath should play at a steady, elevated pace (approx 70 BPM).

## Tech Checks

- [ ] **Console Output**: Check the console for "DEBUG: Video not opened..." to see the path of the missing video file, if applicable.
- [ ] **Crash Log**: Ensure no crash logs are generated when using the Bomb key (F).
