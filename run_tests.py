import os
import subprocess
import sys
from pathlib import Path


def run_tests() -> None:
    """Run pytest for each game test folder."""
    root_dir = Path(__file__).resolve().parent

    # List of game directories that have tests and need specific PYTHONPATH
    # (Name, Relative Path)
    games_to_test = [
        ("Duum", "games/Duum"),
        ("Force_Field", "games/Force_Field"),
        ("Peanut_Butter_Panic", "games/Peanut_Butter_Panic"),
        ("Tetris", "games/Tetris"),
        ("Wizard_of_Wor", "games/Wizard_of_Wor"),
        ("Zombie_Survival", "games/Zombie_Survival"),
    ]

    exit_code = 0

    for name, relative_path in games_to_test:
        print(f"=== Running tests for {name} ===")
        game_path = root_dir / relative_path
        test_path = game_path / "tests"

        if not test_path.exists():
            print(f"No tests found for {name} at {test_path}")
            continue

        # Set PYTHONPATH to include the game directory (for local src/package imports)
        # And also root_dir (for games.shared imports)
        env = os.environ.copy()

        original_pythonpath = env.get("PYTHONPATH", "")
        # Prepend paths. Use os.pathsep for cross-platform compatibility.
        new_pythonpath = (
            f"{game_path}{os.pathsep}{root_dir}{os.pathsep}{original_pythonpath}"
        )
        env["PYTHONPATH"] = new_pythonpath

        # Run pytest
        try:
            # -v for verbose to see what's running
            cmd = [sys.executable, "-m", "pytest", str(test_path)]
            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, env=env, capture_output=False)
            if result.returncode != 0:
                print(f"Tests failed for {name}")
                exit_code = 1
            else:
                print(f"Tests passed for {name}")
        except Exception as e:
            print(f"Error running tests for {name}: {e}")
            exit_code = 1

        print("\n")

    sys.exit(exit_code)


if __name__ == "__main__":
    run_tests()
