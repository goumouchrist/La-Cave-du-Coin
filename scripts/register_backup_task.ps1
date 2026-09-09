<#
Enregistre une tâche planifiée Windows qui exécute scripts/backup.py toutes les
4 heures, comme prévu par le cahier des charges (§8 Sauvegarde).

À exécuter UNE FOIS sur le PC de la boutique, dans PowerShell EN ADMINISTRATEUR,
depuis le dossier du projet :

    .\scripts\register_backup_task.ps1
#>

$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path
$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\pythonw.exe"
$BackupScript = Join-Path $ProjectRoot "scripts\backup.py"

if (-not (Test-Path $PythonExe)) {
    Write-Error "Python introuvable dans .venv ($PythonExe). Créez d'abord le venv (voir README.md)."
    exit 1
}

$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$BackupScript`"" -WorkingDirectory $ProjectRoot
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 4) -RepetitionDuration ([TimeSpan]::MaxValue)
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd

Register-ScheduledTask -TaskName "LaCaveDuCoin-Backup" -Action $Action -Trigger $Trigger -Settings $Settings -Description "Sauvegarde automatique de La Cave du Coin toutes les 4h" -Force

Write-Host "Tâche planifiée 'LaCaveDuCoin-Backup' créée : exécution toutes les 4h."
Write-Host "Vérifiez dans le Planificateur de tâches Windows (taskschd.msc)."
