import logging
import os
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def get_test_environment(game_path: Path, root_dir: Path) -> dict[str, str]:
    """Create environment with proper PYTHONPATH for game tests."""
    env = os.environ.copy()
    original_pythonpath = env.get("PYTHONPATH", "")
    src_path = root_dir / "src"
    new_pythonpath = (
        f"{game_path}{os.pathsep}{root_dir}{os.pathsep}"
        f"{src_path}{os.pathsep}{original_pythonpath}"
    )
    env["PYTHONPATH"] = new_pythonpath
    return env


def run_game_tests(name: str, game_path: Path, root_dir: Path) -> bool:
    """Run tests for a single game and return success status."""
    logger.info("=== Running tests for %s ===", name)
    test_path = game_path / "tests"

    if not test_path.exists():
        logger.warning("No tests found for %s at %s", name, test_path)
        return True

    env = get_test_environment(game_path, root_dir)

    try:
        cmd = [sys.executable, "-m", "pytest", str(test_path)]
        logger.info("Running: %s", " ".join(cmd))
        result = subprocess.run(cmd, env=env, capture_output=False)

        if result.returncode != 0:
            logger.error("Tests failed for %s", name)
            return False
        else:
            logger.info("Tests passed for %s", name)
            return True
    except Exception as e:
        logger.error("Error running tests for %s: %s", name, e)
        return False


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
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    run_tests()
