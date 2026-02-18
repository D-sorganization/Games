#!/usr/bin/env python3
"""
Create a proper ICO file from PNG and desktop shortcut for Games Launcher
"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.shared.subprocess_utils import run_powershell  # noqa: E402

# Global variables for PIL availability
PIL_AVAILABLE = False
PIL_Image: Any | None = None

try:
    from PIL import Image

    PIL_Image = Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_Image = None


def get_desktop_path() -> Path:
    """Get the correct Desktop path using Windows API via PowerShell"""
    try:
        result = run_powershell(
            "[Environment]::GetFolderPath('Desktop')",
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            desktop_path = result.stdout.strip()
            if desktop_path:
                return Path(desktop_path)
    except Exception as e:
        logger.warning("Failed to get Desktop path via PowerShell: %s", e)

    # Fallback to home/Desktop if PowerShell fails
    logger.warning("Using fallback Desktop path")
    return Path.home() / "Desktop"


def create_ico_from_png(png_path: Path, ico_path: Path) -> bool:
    """Convert PNG to ICO with multiple sizes"""
    global PIL_AVAILABLE, PIL_Image

    if not PIL_AVAILABLE or PIL_Image is None:
        logger.warning("PIL/Pillow not available, trying alternative method...")
        return False

    try:
        # Open the PNG image
        with PIL_Image.open(png_path) as img:
            # Convert to RGBA if not already
            if img.mode != "RGBA":
                img = img.convert("RGBA")

            # Create multiple sizes for the ICO file
            sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
            images = []

            for size in sizes:
                resized = img.resize(size, PIL_Image.Resampling.LANCZOS)
                images.append(resized)

            # Save as ICO with multiple sizes using proper multi-resolution approach
            images[0].save(
                ico_path,
                format="ICO",
                save_all=True,
                append_images=images[1:],
            )

            logger.info("Successfully created ICO file: %s", ico_path)
            return True

    except Exception as e:
        logger.error("Error creating ICO file: %s", e)
        return False


def create_desktop_shortcut() -> bool:
    """Create desktop shortcut with proper icon"""
    current_dir = Path.cwd()
    launcher_path = current_dir / "game_launcher.py"
    png_icon_path = current_dir / "launcher_assets" / "force_field_icon.png"
    ico_icon_path = current_dir / "launcher_assets" / "games_launcher.ico"

    # Get desktop path using Windows API
    desktop_path = get_desktop_path()
    shortcut_path = desktop_path / "Games Launcher.lnk"

    logger.info("Creating Games Launcher desktop shortcut...")
    logger.info("Current directory: %s", current_dir)
    logger.info("Desktop path: %s", desktop_path)
    logger.info("Launcher path: %s", launcher_path)
    logger.info("PNG icon: %s", png_icon_path)
    logger.info("ICO icon: %s", ico_icon_path)

    # Check if PNG icon exists
    if not png_icon_path.exists():
        logger.error("PNG icon not found: %s", png_icon_path)
        return False

    # Create ICO file from PNG
    ico_created = create_ico_from_png(png_icon_path, ico_icon_path)

    # Create PowerShell script to make the shortcut
    # Use single quotes to prevent variable expansion
    ps_script = f"""
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut('{shortcut_path}')
$Shortcut.TargetPath = 'python'
$Shortcut.Arguments = '"{launcher_path}"'
$Shortcut.WorkingDirectory = '{current_dir}'
$Shortcut.Description = 'Launch Games Collection - Force Field, Tetris, Doom and more!'
$Shortcut.WindowStyle = 1
"""

    if ico_created and ico_icon_path.exists():
        ps_script += f"$Shortcut.IconLocation = '{ico_icon_path}'\n"
        logger.info("Using custom ICO icon")
    else:
        logger.warning("Using default Python icon")

    ps_script += "$Shortcut.Save()\n"
    ps_script += f"Write-Host 'Desktop shortcut created: {shortcut_path}'\n"

    # Execute PowerShell script
    try:
        result = run_powershell(ps_script, capture_output=True, text=True)

        if result.returncode == 0:
            logger.info("PowerShell execution successful:")
            logger.info(result.stdout)

            if shortcut_path.exists():
                logger.info("Desktop shortcut created successfully!")
            logger.info("Location: %s", shortcut_path)
            return True
        else:
            logger.error("Shortcut file not found after creation")
            return False

    except subprocess.CalledProcessError as e:
        logger.error("PowerShell error: %s", e)
        logger.error("Error output: %s", e.stderr)
        return False


def main() -> None:
    """Main function"""
    global PIL_AVAILABLE, PIL_Image

    logger.info("Games Launcher Desktop Shortcut Creator")
    logger.info("=" * 50)

    if not PIL_AVAILABLE:
        logger.warning("PIL/Pillow not installed. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
            logger.info("Pillow installed successfully!")
            # Re-import after installation and update global state
            from PIL import Image as _PIL_Image

            PIL_Image = _PIL_Image
            PIL_AVAILABLE = True
            logger.info("Pillow imported successfully!")
        except Exception as e:
            logger.error("Failed to install Pillow: %s", e)
            logger.warning("Continuing without custom icon conversion...")

    success = create_desktop_shortcut()

    if success:
        logger.info("SUCCESS! Your Games Launcher shortcut is ready!")
        logger.info(
            "Look for 'Games Launcher' on your desktop with a cool Force Field icon!"
        )
    else:
        logger.error("Something went wrong. Check the error messages above.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
