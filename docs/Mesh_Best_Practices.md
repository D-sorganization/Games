# Best Practices for Mesh-Based Character Integration

This guide outlines best practices for integrating mesh-based characters into the QuatGolf engine, leveraging the standard `HumanoidRig` and `humanoid_character_builder`.

## 1. Asset Pipeline

### File Formats

- **Structure**: Use **URDF** (Unified Robot Description Format) for defining the skeletal hierarchy, joint limits, and physics properties.
- **Geometry**: Use **Binary STL** for static mesh data. Avoid ASCII STL for production assets due to file size.
- **Textures**: Ideally, use vertex colors or material properties defined in URDF. If complex texturing is needed, ensure the loader supports UV mapping (current `STLLoader` supports vertex normals but basic coloring).

### Asset Generation

- **Automation**: Do not manually edit generated URDFs or meshes. Use the `humanoid_character_builder` (in `Tools` repo) to generate assets. This ensures consistency between physics (inertia tensors) and visuals.
- **Scripting**: Create generation scripts (like `tools/generate_enemies.py`) to reproduce assets deterministically.

## 2. Rendering Optimization

### Flyweight Pattern

- **Resource Sharing**: Load the `HumanoidRig` once. This object contains the immutable mesh data and bind pose hierarchy.
- **Instances**: Create lightweight `HumanoidEnemy` instances that hold only mutable state (joint angles, world transforms). Pass the shared `HumanoidRig` pointer to instances.
- **Memory**: This approach saves GPU memory by uploading geometry only once per character *type* (e.g., Grunt, Scout), regardless of how many enemies are spawned.

### Drawing

- **Batching**: Iterate through the rig nodes once. For each node, if it has a mesh, draw it using the instance's calculated world matrix.
- **Future Optimization**: For massive crowds, consider implementing GPU instancing where joint states are passed in a texture or uniform buffer, allowing a single draw call per mesh type.

## 3. Coordinate Systems

- **Convention**: QuatGolf uses a **Z-up, Right-Handed** coordinate system.
- **Consistency**: Ensure all tools (character builder) export in Z-up. `humanoid_character_builder` defaults to Z-up.
- **Transforms**:
  - `offset_matrix`: The transform from parent link to child link (bind pose).
  - `world_matrix`: The cumulative transform of a link in world space, including dynamic joint rotations.

## 4. Physics & Simulation

- **Collision**: Use primitive shapes (Box, Sphere, Capsule) for physics collision checking whenever possible. They are significantly faster than mesh colliders.
- **Visuals**: Visual meshes can be higher fidelity. The `HumanoidRig` supports loading visual meshes while the physics engine (if integrated) should use the `<collision>` tags from URDF.
- **Inertia**: Accurate inertia tensors are critical for stable simulation. The builder calculates these based on geometry density.

## 5. Development Workflow

1. **Define**: Create a `BodyParameters` preset for the new enemy type.
2. **Generate**: Run `generate_enemies.py` to produce URDF and meshes.
3. **Load**: Update `main.cpp` or a level loader to load the new URDF using `HumanoidRig::load()`.
4. **Spawn**: Instantiate `HumanoidEnemy` and attach the rig.
