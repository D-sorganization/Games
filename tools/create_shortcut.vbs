Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "C:\Users\diete\Desktop\Game Launcher.lnk"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "C:\Users\diete\Repositories\Games\Play Games.bat"
oLink.WorkingDirectory = "C:\Users\diete\Repositories\Games"
oLink.Description = "Launch Games"
' Attempt to use the force field icon, but .lnk usually needs .ico. 
' Some windows versions might accept .png or just fail to show it.
' We will default to standard which will pick up the batch file icon or system default.
' oLink.IconLocation = "C:\Users\diete\Repositories\Games\launcher_assets\force_field_icon.png"
oLink.Save
