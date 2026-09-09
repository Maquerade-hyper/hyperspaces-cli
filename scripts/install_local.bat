@echo off
setlocal

cd /d "%~dp0.."

echo ========================================
echo       HYPERSPACE LOCAL INSTALL
echo ========================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Python virtual environment not found.
    echo.
    echo Expected:
    echo   %CD%\.venv\Scripts\python.exe
    echo.
    exit /b 1
)

call .venv\Scripts\activate.bat

echo Initializing runtime installation...
echo.

python -c "from hyperspace.infrastructure.runtime import initialize_installation; m=initialize_installation(); print('Product:     ' + m.product_name); print('Version:     ' + m.version); print('Install dir: ' + m.install_dir); print('Data dir:    ' + m.data_dir); print('Platform:    ' + m.platform)"

if errorlevel 1 (
    echo.
    echo Installation initialization FAILED.
    exit /b 1
)

echo.
echo Verifying installation...
echo.

python -c "from hyperspace.infrastructure.runtime import verify_installation; r=verify_installation(); print('Initialized: ' + str(r['installation_initialized'])); print('Directories: ' + str(r['directories_ok'])); print('Modules:     ' + str(r['modules_ok'])); print('READY:       ' + str(r['ready'])); raise SystemExit(0 if r['ready'] else 1)"

if errorlevel 1 (
    echo.
    echo Installation verification FAILED.
    exit /b 1
)

echo.
echo ========================================
echo Hyperspace installation READY.
echo ========================================
echo.

endlocal