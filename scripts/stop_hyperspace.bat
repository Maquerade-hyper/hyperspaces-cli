@echo off
setlocal

cd /d "%~dp0.."

echo ========================================
echo       STOP HYPERSPACE
echo ========================================
echo.

echo Looking for Hyperspace processes...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"$processes = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'apps\.control_plane\.main|apps\.agent\.main|runtime_manager\.py' }; if ($processes) { foreach ($p in $processes) { Write-Host ('Stopping PID ' + $p.ProcessId + ' - ' + $p.Name); Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue } } else { Write-Host 'No Hyperspace processes found.' }"

echo.
echo Hyperspace stopped.
echo.

endlocal