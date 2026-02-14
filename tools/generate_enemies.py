import os
import sys

# Add Tools repo to Python path
TOOLS_PYTHON_PATH = r"c:\Users\diete\Repositories\Tools\src\shared\python"
if TOOLS_PYTHON_PATH not in sys.path:
    sys.path.append(TOOLS_PYTHON_PATH)

try:
    from humanoid_character_builder import (
        BodyParameters,
        CharacterBuilder,
    )
    from humanoid_character_builder.core.body_parameters import BuildType

    print("Successfully imported humanoid_character_builder")
except ImportError as e:
    print(f"Error importing humanoid_character_builder: {e}")
    sys.exit(1)

OUTPUT_DIR = r"c:\Users\diete\Repositories\Games\src\games\QuatGolf\assets\enemies"


def generate_enemy(name, params):
    print(f"Generating {name}...")
    builder = CharacterBuilder()
    result = builder.build(params)

    # Create specific folder for this enemy to keep assets organized
    # output_path = output_dir/name
    enemy_dir = os.path.join(OUTPUT_DIR, name)

    # export_urdf takes the directory path where it creates the URDF + meshes folder
    # but based on previous run, it creates a folder with the 'name' inside 'base_name' path?
    # No, let's look at api.py or experiment.
    # Assuming export_urdf(path) -> creates path/name.urdf and path/meshes/

    # Cleaning up the previous logic
    # Set the name in parameters so the file is named correctly
    params.name = name

    result.export_urdf(enemy_dir)
    print(f"Saved to {enemy_dir}/{name}.urdf")


def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 1. Grunt: Short, stocky
    grunt = BodyParameters(
        height_m=1.65,
        mass_kg=85.0,
        build_type=BuildType.ENDOMORPH,  # Stocky/Heavy
        muscularity=0.6,
        name="grunt",
    )
    generate_enemy("grunt", grunt)

    # 2. Scout: Tall, slim, fast
    scout = BodyParameters(
        height_m=1.85,
        mass_kg=70.0,
        build_type=BuildType.ECTOMORPH,  # Slim
        muscularity=0.4,
        name="scout",
    )
    generate_enemy("scout", scout)

    # 3. Tank: Huge, massive
    tank = BodyParameters(
        height_m=2.10,
        mass_kg=120.0,
        build_type=BuildType.MESOMORPH,  # Muscular/Athletic
        muscularity=0.9,
        name="tank",
    )
    generate_enemy("tank", tank)


if __name__ == "__main__":
    main()
