# QuatGolf — 3D Golf Game

A 3D golf game built on the shared C++ engine modules.

## Architecture

```
QuatGolf/
  src/
    terrain/   — Heightmap terrain mesh, surface types
    course/    — Hole layouts, tee/green/pin placement
    physics/   — Ball flight (drag, lift, Magnus), terrain contact
    game/      — Shot controller, scorecard, game state
    main.cpp   — Thin orchestration
  shaders/     — Terrain + sky shaders
  assets/      — Course data
```

## Physics Model

Custom lightweight physics (no MuJoCo):

- **Ball flight:** Aerodynamic drag + lift + Magnus force (spin)
- **Terrain contact:** Height-map collision, bounce, rolling friction
- **Surface types:** Tee, fairway, rough, sand, green, water (each with friction/bounce)

## Controls

| Input               | Action                           |
| ------------------- | -------------------------------- |
| Mouse / Right Stick | Aim direction                    |
| Space / A Button    | Start power meter                |
| Space / A Button    | Confirm shot (release)           |
| 1-9                 | Select club                      |
| Tab / Y             | Camera: behind ball / free orbit |
| R / Back            | Reset ball                       |

## Dependencies

Uses shared C++ modules from `Games/src/games/shared/cpp/`:

- `math/` — Vec3, Quaternion, Mat4
- `core/` — Transform, AABB
- `renderer/` — GLLoader, Shader, Mesh, Texture, Camera
- `input/` — InputManager, Gamepad
