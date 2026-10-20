@echo off
setlocal
cd /d "%~dp0"
echo GAS HUNAR - Windows EXE and screenshot builder
where py >nul 2>nul
if errorlevel 1 (
    echo Python 3.12 is needed on this BUILD computer. The final EXE will not require Python.
    echo Install Python 3.12 x64, then run this file again.
    pause
    exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\build_windows.ps1"
if errorlevel 1 (
    echo Build failed. Read the error above. No successful EXE is claimed.
    pause
    exit /b 1
)
echo Ready: dist\GAS HUNAR.exe
echo Screenshots: dist\screenshots\
start "" "%~dp0dist"
pause
