$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\School Comms Aggregator.lnk")
$Shortcut.TargetPath = "$env:USERPROFILE\school-comms-aggregator\dist\School Comms Aggregator.exe"
$Shortcut.WorkingDirectory = "$env:USERPROFILE\school-comms-aggregator"
$Shortcut.Save()
Write-Host "Shortcut created successfully!"
