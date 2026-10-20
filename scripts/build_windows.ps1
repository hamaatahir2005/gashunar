param([switch]$Installer,[string]$Wheelhouse = "")
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
if ($env:OS -ne "Windows_NT") { throw "A Windows x64 build machine is required." }
function Run-Checked([scriptblock]$Command) { & $Command; if ($LASTEXITCODE -ne 0) { throw "Command failed ($LASTEXITCODE)" } }
if (!(Test-Path ".venv\Scripts\python.exe")) { Run-Checked { py -3.12 -m venv .venv } }
$Python = ".\.venv\Scripts\python.exe"
if ($Wheelhouse) {
    Run-Checked { & $Python -m pip install --no-index --find-links $Wheelhouse -r requirements-dev.txt }
} else {
    Run-Checked { & $Python -m pip install -r requirements-dev.txt }
}
Run-Checked { & $Python scripts\create_assets.py }
$env:QT_QPA_PLATFORM = "offscreen"
New-Item -ItemType Directory -Force dist | Out-Null
Run-Checked { & $Python -m pytest -q --junitxml=dist/test-results.xml }
Run-Checked { & $Python scripts\capture_screenshots.py --output dist\screenshots }
Remove-Item Env:QT_QPA_PLATFORM
Run-Checked { & $Python -m PyInstaller --clean --noconfirm packaging\gas-hunar.spec }
if (!(Test-Path "dist\GAS HUNAR.exe")) { throw "Expected EXE was not generated" }
$CheckDir = Join-Path (Get-Location).Path "dist\exe-self-check"
$CheckProcess = Start-Process -FilePath ".\dist\GAS HUNAR.exe" -ArgumentList @("--self-check", ('"' + $CheckDir + '"')) -PassThru
if (!$CheckProcess.WaitForExit(120000)) { $CheckProcess.Kill(); throw "Packaged EXE self-check timed out" }
if ($CheckProcess.ExitCode -ne 0) { throw "Packaged EXE self-check failed" }
$CheckResult = Get-Content "$CheckDir\self-check.json" -Raw | ConvertFrom-Json
if (!$CheckResult.success) { throw "Packaged EXE self-check did not succeed" }
& $Python -m pip freeze | Out-File -Encoding utf8 dist\build-dependencies.txt
Get-FileHash "dist\GAS HUNAR.exe" -Algorithm SHA256 | Format-List | Out-File dist\SHA256.txt
if ($Installer) {
    $Compiler = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if (!$Compiler) { throw "Install Inno Setup 6 and add ISCC.exe to PATH." }
    Run-Checked { & $Compiler.Source packaging\installer.iss }
    if (!(Test-Path "dist\GAS HUNAR Setup.exe")) { throw "Installer not generated" }
}
Write-Host "Build created. Complete docs/MANUAL_TESTS.md on Windows before release."
