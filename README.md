# GAS HUNAR — گەس هونەر

A native, offline restaurant desktop application in Python 3.12, PySide6, SQLAlchemy and SQLite. **Development phase 0.1.0: substantial application source is present; production acceptance is incomplete.** See [the exact checklist](docs/STATUS.md), including missing features and verification blockers.

## Run from source

On a machine with Python 3.12:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python main.py
```

Linux development uses `.venv/bin/python`. No network is used by the application at runtime. Dependency installation/building requires available packages; an offline wheelhouse can be supplied to the Windows build script. A Python installation is only needed for development/building, not for a successfully packaged EXE.

Create your own first administrator passphrase. There is no default password. Kurdish Sorani/RTL and dark theme are defaults. Language/theme/settings persist; restart after changing language. Some secondary labels/errors are still English. For optional demo menu records, close the app and run `python scripts/seed_demo.py` after administrator setup. The demo never inserts fictional sales.

Writable data: `%LOCALAPPDATA%\GAS HUNAR` on Windows. Set `GAS_HUNAR_DATA` before launching to use another writable directory. Never place it in the installation folder. Backups are database-only; preserve the complete data folder when migrating images or attachments.

## Cashier workflow

1. Create menu items, ingredients and recipes; enter opening stock or purchases.
2. Open a cash drawer; select products, quantities, notes, order type and optional customer/table.
3. Hold to save a draft, or Pay to see the final discounted/taxed total and enter cash/card allocations. F2 focuses search/barcode, F8 holds, F9 pays.
4. Resume held/partially paid orders from Orders. Confirm sends an unpaid order to the local kitchen; Pay can also confirm atomically.
5. Complete kitchen states, reprint receipts, record expenses, reconcile/close drawer and create verified backups.

Money never uses binary floating-point arithmetic. Revenue excludes tax, includes service and differs from collected cash. Purchases are inventory, not operating expenses. Read [accounting rules and limitations](docs/ARCHITECTURE.md).

## Tests

```powershell
$env:QT_QPA_PLATFORM="offscreen"
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m unittest discover -s tests -p stdlib_checks.py -v
```

In the supplied Linux environment, only syntax compilation and the 10 dependency-free checks were executed successfully. Full tests and GUI launch are blocked by unavailable dependencies. No Windows EXE or installer has been generated. [Manual acceptance checklist](docs/MANUAL_TESTS.md).

## Windows build

Run on Windows x64 with Python 3.12; Inno Setup 6 is optional:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
# Optional installer:
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1 -Installer
# Pre-downloaded compatible Windows wheels:
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1 -Wheelhouse D:\wheels
```

The script stops on failed tests/builds. Expected artifacts **after successful Windows execution**: `dist/GAS HUNAR.exe` and optionally `dist/GAS HUNAR Setup.exe`. Includes icon, metadata, shortcuts, uninstall and persistent user data. Building on Linux does not produce a supported Windows EXE. Complete Windows installation/update/uninstall and physical printer validation before release.

## One-click Windows build and actual screenshots

On a Windows x64 development computer with Python 3.12 installed, double-click `BUILD-EXE.bat`. It installs dependencies, runs tests, captures actual native Qt windows using a temporary sample database, and packages the EXE. Output is `dist/GAS HUNAR.exe`; screenshots are in `dist/screenshots/`. Installation of dependencies needs internet or a compatible local wheelhouse. The generated program itself works offline. A failed test stops the build.

The screenshot script never opens restaurant data and marks captures as demo data. To capture separately: `python scripts/capture_screenshots.py --output dist/screenshots`. No screenshot is claimed until this command has run successfully.

An optional `.github/workflows/windows-build.yml` provides a manually triggered Windows build and downloadable EXE/screenshots artifact if you place the project in your own GitHub repository. It has not been run here and is not needed by the offline application.
