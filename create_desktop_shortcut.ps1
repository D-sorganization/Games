# PowerShell script to create desktop shortcut for Games Launcher
param(
    [string]$DesktopPath = [Environment]::GetFolderPath("Desktop")
)

# Get current directory and paths
$CurrentDir = (Get-Location).Path
$LauncherPath = Join-Path $CurrentDir "game_launcher.py"
$IconPath = Join-Path $CurrentDir "launcher_assets\force_field_icon.png"
$IcoPath = Join-Path $CurrentDir "launcher_assets\games_launcher.ico"
$ShortcutPath = Join-Path $DesktopPath "Games Launcher.lnk"

# Create WScript Shell object
$WshShell = New-Object -comObject WScript.Shell

# Create shortcut
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "python"
$Shortcut.Arguments = "`"$LauncherPath`""
$Shortcut.WorkingDirectory = $CurrentDir
$Shortcut.Description = "Launch Games Collection"
$Shortcut.WindowStyle = 1  # Normal window

# Set icon if it exists
if (Test-Path $IconPath) {
    # Try to create ICO file from PNG for better shortcut appearance
    try {
        Add-Type -AssemblyName System.Drawing
        $png = [System.Drawing.Image]::FromFile($IconPath)
        $ico = New-Object System.Drawing.Bitmap $png, 32, 32
        $ico.Save($IcoPath, [System.Drawing.Imaging.ImageFormat]::Icon)
        $png.Dispose()
        $ico.Dispose()
        
        $Shortcut.IconLocation = $IcoPath
        Write-Host "Custom games icon set successfully!"
    } catch {
        Write-Host "Could not convert PNG to ICO, using default icon"
        $Shortcut.Description = "Launch Games Collection - Features Force Field, Tetris, Doom and more!"
    }
} else {
    $Shortcut.Description = "Launch Games Collection - Features Force Field, Tetris, Doom and more!"
}

# Save the shortcut
$Shortcut.Save()

Write-Host "Desktop shortcut created successfully at: $ShortcutPath"
Write-Host "Shortcut points to: $LauncherPath"
Write-Host "Working directory: $CurrentDir"

# Optional: Clean up and provide info
if (Test-Path $IcoPath) {
    Write-Host "Custom icon created at: $IcoPath"
} else {
    Write-Host "Note: Using default Python icon. For custom icon, convert $IconPath to .ico format manually"
}