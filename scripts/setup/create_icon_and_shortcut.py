#!/usr/bin/env python3
"""
Create a proper ICO file from PNG and desktop shortcut for Games Launcher
"""

import subprocess
import sys
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.shared.subprocess_utils import run_powershell

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
        print(f"⚠️  Failed to get Desktop path via PowerShell: {e}")

    # Fallback to home/Desktop if PowerShell fails
    print("⚠️  Using fallback Desktop path")
    return Path.home() / "Desktop"


def create_ico_from_png(png_path: Path, ico_path: Path) -> bool:
    """Convert PNG to ICO with multiple sizes"""
    global PIL_AVAILABLE, PIL_Image

    if not PIL_AVAILABLE or PIL_Image is None:
        print("PIL/Pillow not available, trying alternative method...")
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

            print(f"✅ Successfully created ICO file: {ico_path}")
            return True

    except Exception as e:
        print(f"❌ Error creating ICO file: {e}")
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

    print("🎮 Creating Games Launcher desktop shortcut...")
    print(f"📁 Current directory: {current_dir}")
    print(f"🖥️  Desktop path: {desktop_path}")
    print(f"🎯 Launcher path: {launcher_path}")
    print(f"🖼️  PNG icon: {png_icon_path}")
    print(f"🎨 ICO icon: {ico_icon_path}")

    # Check if PNG icon exists
    if not png_icon_path.exists():
        print(f"❌ PNG icon not found: {png_icon_path}")
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
        print("🎨 Using custom ICO icon")
    else:
        print("⚠️  Using default Python icon")

    ps_script += "$Shortcut.Save()\n"
    ps_script += f"Write-Host 'Desktop shortcut created: {shortcut_path}'\n"

    # Execute PowerShell script
    try:
        result = run_powershell(ps_script, capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ PowerShell execution successful:")
            print(result.stdout)

            if shortcut_path.exists():
                print("🎉 Desktop shortcut created successfully!")
            print(f"📍 Location: {shortcut_path}")
            return True
        else:
            print("❌ Shortcut file not found after creation")
            return False

    except subprocess.CalledProcessError as e:
        print(f"❌ PowerShell error: {e}")
        print(f"Error output: {e.stderr}")
        return False


def main() -> None:
    """Main function"""
    global PIL_AVAILABLE, PIL_Image

    print("🚀 Games Launcher Desktop Shortcut Creator")
    print("=" * 50)

    if not PIL_AVAILABLE:
        print("⚠️  PIL/Pillow not installed. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
            print("✅ Pillow installed successfully!")
            # Re-import after installation and update global state
            from PIL import Image as _PIL_Image

            PIL_Image = _PIL_Image
            PIL_AVAILABLE = True
            print("📦 Pillow imported successfully!")
        except Exception as e:
            print(f"❌ Failed to install Pillow: {e}")
            print("Continuing without custom icon conversion...")

    success = create_desktop_shortcut()

    if success:
        print("\n🎉 SUCCESS! Your Games Launcher shortcut is ready!")
        print("Look for 'Games Launcher' on your desktop with a cool Force Field icon!")
    else:
        print("\n❌ Something went wrong. Check the error messages above.")


if __name__ == "__main__":
    main()
