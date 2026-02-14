# Shared C++ Game Modules

Reusable C++ header-only libraries for 3D games, mirroring the Python `shared/` pattern.

## Modules

| Module        | Headers                                    | Purpose                                    |
| ------------- | ------------------------------------------ | ------------------------------------------ |
| **math/**     | Vec3, Quaternion, Mat4                     | 3D vector math, quaternion rotation, SLERP |
| **core/**     | Transform, AABB, Entity, Projectile        | Game object primitives                     |
| **input/**    | InputAction, Gamepad, InputManager         | Unified keyboard/mouse/gamepad             |
| **renderer/** | GLLoader, Shader, Mesh, Texture, OBJLoader | OpenGL 3.3 rendering                       |

## Usage

All modules are header-only. Include via relative path from your game:

```cpp
#include "shared/cpp/math/Vec3.h"
#include "shared/cpp/input/InputManager.h"
```

Or add to your CMake:

```cmake
target_include_directories(my_game PRIVATE ${CMAKE_SOURCE_DIR}/src/games/shared/cpp)
```

## Namespace

All shared code lives under `qe::` (QuatEngine namespace):

- `qe::math::` — Vec3, Quaternion, Mat4
- `qe::core::` — Transform, AABB, Entity, Projectile
- `qe::input::` — InputAction, Gamepad, InputManager
- `qe::renderer::` — GLLoader, Shader, Mesh, Texture

## Design Principles

- **Header-only** — zero build steps, just `#include`
- **DbC** — preconditions/postconditions documented per class
- **No external deps** — math and core are self-contained
- **SDL2 optional** — only input/ and renderer/ require SDL2
