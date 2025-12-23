# Enhanced PowerShell script to create desktop shortcut with proper icon
param(
    [string]$DesktopPath = [Environment]::GetFolderPath("Desktop")
)

# Get current directory and paths
$CurrentDir = (Get-Location).Path
$LauncherPath = Join-Path $CurrentDir "game_launcher.py"
$IconPath = Join-Path $CurrentDir "launcher_assets\force_field_icon.png"
$IcoPath = Join-Path $CurrentDir "launcher_assets\games_launcher.ico"
$ShortcutPath = Join-Path $DesktopPath "Games Launcher.lnk"

Write-Host "Creating desktop shortcut for Games Launcher..."
Write-Host "Current directory: $CurrentDir"
Write-Host "Icon source: $IconPath"

# Remove existing shortcut if it exists
if (Test-Path $ShortcutPath) {
    Remove-Item $ShortcutPath -Force
    Write-Host "Removed existing shortcut"
}

# Remove existing ICO if it exists to recreate it properly
if (Test-Path $IcoPath) {
    Remove-Item $IcoPath -Force
    Write-Host "Removed existing ICO file"
}

# Create WScript Shell object
$WshShell = New-Object -comObject WScript.Shell

# Create shortcut
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "python"
$Shortcut.Arguments = "`"$LauncherPath`""
$Shortcut.WorkingDirectory = $CurrentDir
$Shortcut.Description = "Launch Games Collection - Force Field, Tetris, Doom and more!"
$Shortcut.WindowStyle = 1  # Normal window

# Better PNG to ICO conversion using .NET
if (Test-Path $IconPath) {
    try {
        Write-Host "Converting PNG to ICO..."
        
        # Load required assemblies
        Add-Type -AssemblyName System.Drawing
        Add-Type -AssemblyName System.Windows.Forms
        
        # Load the PNG image
        $originalImage = [System.Drawing.Image]::FromFile($IconPath)
        
        # Create multiple sizes for the ICO (16x16, 32x32, 48x48)
        $sizes = @(16, 32, 48)
        $iconImages = @()
        
        foreach ($size in $sizes) {
            $resizedImage = New-Object System.Drawing.Bitmap($originalImage, $size, $size)
            $iconImages += $resizedImage
        }
        
        # Create ICO file with multiple sizes
        $iconStream = New-Object System.IO.FileStream($IcoPath, [System.IO.FileMode]::Create)
        
        # ICO file header
        $iconStream.Write([byte[]]@(0, 0, 1, 0), 0, 4)  # ICO signature and type
        $iconStream.Write([System.BitConverter]::GetBytes([uint16]$iconImages.Count), 0, 2)  # Number of images
        
        $imageDataOffset = 6 + ($iconImages.Count * 16)  # Header + directory entries
        
        # Write directory entries
        for ($i = 0; $i -lt $iconImages.Count; $i++) {
            $img = $iconImages[$i]
            $iconStream.WriteByte($img.Width)   # Width
            $iconStream.WriteByte($img.Height)  # Height
            $iconStream.WriteByte(0)            # Color count (0 for true color)
            $iconStream.WriteByte(0)            # Reserved
            $iconStream.Write([System.BitConverter]::GetBytes([uint16]1), 0, 2)  # Planes
            $iconStream.Write([System.BitConverter]::GetBytes([uint16]32), 0, 2) # Bits per pixel
            
            # Calculate image data size (rough estimate)
            $imageSize = $img.Width * $img.Height * 4 + 40  # RGBA + header
            $iconStream.Write([System.BitConverter]::GetBytes([uint32]$imageSize), 0, 4)
            $iconStream.Write([System.BitConverter]::GetBytes([uint32]$imageDataOffset), 0, 4)
            $imageDataOffset += $imageSize
        }
        
        $iconStream.Close()
        
        # Dispose of images
        foreach ($img in $iconImages) {
            $img.Dispose()
        }
        $originalImage.Dispose()
        
        # Alternative: Use simpler conversion
        $bitmap = New-Object System.Drawing.Bitmap($IconPath)
        $resized = New-Object System.Drawing.Bitmap($bitmap, 32, 32)
        $icon = [System.Drawing.Icon]::FromHandle($resized.GetHicon())
        
        # Save as ICO
        $fileStream = [System.IO.File]::Create($IcoPath)
        $icon.Save($fileStream)
        $fileStream.Close()
        
        $bitmap.Dispose()
        $resized.Dispose()
        $icon.Dispose()
        
        Write-Host "ICO file created successfully!"
        
        # Set the icon for the shortcut
        $Shortcut.IconLocation = $IcoPath
        Write-Host "Custom icon set for shortcut"
        
    } catch {
        Write-Host "Error converting PNG to ICO: $($_.Exception.Message)"
        Write-Host "Using PNG directly as icon..."
        
        # Try using PNG directly (some systems support this)
        $Shortcut.IconLocation = "$IconPath,0"
    }
} else {
    Write-Host "PNG icon file not found at: $IconPath"
}

# Save the shortcut
$Shortcut.Save()

Write-Host ""
Write-Host "=== SHORTCUT CREATED ==="
Write-Host "Location: $ShortcutPath"
Write-Host "Target: python `"$LauncherPath`""
Write-Host "Working Directory: $CurrentDir"
if (Test-Path $IcoPath) {
    Write-Host "Icon: $IcoPath"
} else {
    Write-Host "Icon: Default Python icon"
}
Write-Host ""
Write-Host "You should now see 'Games Launcher' on your desktop with a custom icon!"