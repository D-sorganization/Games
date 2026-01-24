import os
import subprocess
import sys
from pathlib import Path


def get_test_environment(game_path: Path, root_dir: Path) -> dict[str, str]:
    """Create environment with proper PYTHONPATH for game tests."""
    env = os.environ.copy()
    original_pythonpath = env.get("PYTHONPATH", "")
    src_path = root_dir / "src"
    new_pythonpath = f"{game_path}{os.pathsep}{root_dir}{os.pathsep}{src_path}{os.pathsep}{original_pythonpath}"
    env["PYTHONPATH"] = new_pythonpath
    return env


def run_game_tests(name: str, game_path: Path, root_dir: Path) -> bool:
    """Run tests for a single game and return success status."""
    print(f"=== Running tests for {name} ===")
    test_path = game_path / "tests"

    if not test_path.exists():
        print(f"No tests found for {name} at {test_path}")
        return True

    env = get_test_environment(game_path, root_dir)

    try:
        cmd = [sys.executable, "-m", "pytest", str(test_path)]
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, env=env, capture_output=False)

        if result.returncode != 0:
            print(f"Tests failed for {name}")
            return False
        else:
            print(f"Tests passed for {name}")
            return True
    except Exception as e:
        print(f"Error running tests for {name}: {e}")
        return False
    finally:
        print("\n")


def run_tests() -> None:
    """Run tests for all games in the repository."""
    root_dir = Path(__file__).resolve().parent

    games_to_test = [
        ("Duum", "src/games/Duum"),
        ("Force_Field", "src/games/Force_Field"),
        ("Peanut_Butter_Panic", "src/games/Peanut_Butter_Panic"),
        ("Tetris", "src/games/Tetris"),
        ("Wizard_of_Wor", "src/games/Wizard_of_Wor"),
        ("Zombie_Survival", "src/games/Zombie_Survival"),
    ]

    all_passed = True
    for name, relative_path in games_to_test:
        game_path = root_dir / relative_path
        if not run_game_tests(name, game_path, root_dir):
            all_passed = False

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    run_tests()
