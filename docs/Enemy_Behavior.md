# Enemy Behavior & Integration

This document outlines the architecture and behavior of enemies in QuatGolf.

## Architecture

### Components

1. **`HumanoidRig` (`loader/HumanoidRig.h`)**:
    * **Role**: Flyweight resource containing the skeletal hierarchy and mesh data. Loaded once per enemy type (e.g., Grunt, Scout).
    * **Data**: `RigNode` tree, `Mesh` objects (GL buffers), bind pose transforms.

2. **`HumanoidEnemy` (`loader/HumanoidEnemy.h`)**:
    * **Role**: Visual instance of a rig.
    * **Data**: Shared pointer to `HumanoidRig`, per-instance `joint_angles`, `world_matrices`.
    * **Responsibility**: Update animation matrices, draw meshes.

3. **`Enemy` (`game/Enemy.h`)**:
    * **Role**: Game entity wrapper.
    * **Data**: `HumanoidEnemy` instance, `velocity`, `state`, `state_timer`.
    * **Responsibility**: AI logic, state transitions, high-level update.

4. **`EnemyManager` (`game/EnemyManager.h`)**:
    * **Role**: Central manager for all enemies.
    * **Responsibility**: Spawning, batch updating/drawing, collision detection.

## AI State Machine

The `Enemy` class implements a simple state machine:

| State | Behavior | Transition |
|-------|----------|------------|
| **Idle** | Plays idle animation (breathing). | Transitions to **Watch** after 3s. |
| **Watch** | Rotates to face the player/ball. | Transitions back to **Idle** after 5s. |
| **Panic** | Triggered by collision. Resets timer. | Stays in Panic (currently placeholder). |
| **Celebrate** | (Planned) Triggered by player events. | - |

## Collision System

Enemies act as physical obstacles for the golf ball.

### Implementation

* **Shape**: Vertical Cylinder (Capsule approximation).
  * **Height**: 1.8m
  * **Radius**: 0.4m
* **Logic**: Located in `Enemy::check_collision`.
* **Interaction**: Elastic bounce.
  * Ball velocity is reflected off the collision normal.
  * Energy loss coefficient: 0.7.
  * Console log: "Bonk! Enemy hit."

### Tuning

Adjust `cy_r` and `cy_h` in `Enemy::check_collision` to change the hit volume.

## Future Improvements

* **Ragdoll Physics**: Switch to ragdoll on high-velocity impact.
* **Pathfinding**: Use navigation mesh to move around obstacles.
* **Goalkeeper Logic**: Move sideways to block shots actively.
