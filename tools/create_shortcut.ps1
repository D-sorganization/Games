$WshShell = New-Object -comObject WScript.Shell
$DesktopPath = [Environment]::GetFolderPath("Desktop")
Write-Host "Detected Desktop Path: $DesktopPath"

$ShortcutFile = "$DesktopPath\Game Launcher.lnk"
$Shortcut = $WshShell.CreateShortcut($ShortcutFile)
$Shortcut.TargetPath = "C:\Users\diete\Repositories\Games\Play Games.bat"
$Shortcut.WorkingDirectory = "C:\Users\diete\Repositories\Games"
$Shortcut.Description = "Launch Games"
$Shortcut.Save()

Write-Host "Created shortcut at: $ShortcutFile"
