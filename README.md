# GAS HUNAR — گەس هونەر

Native, offline Windows restaurant management application: Python 3.12, PySide6, SQLAlchemy and SQLite. **Version 0.2 is a development release.** The remaining production/advanced-feature backlog is tracked in [docs/STATUS.md](docs/STATUS.md).

## Download and run

- [Download Windows EXE — no Python required](https://github.com/hamaatahir2005/gashunar/releases/download/v0.2.0-build-4/GAS.HUNAR.exe)
- [Release and SHA-256](https://github.com/hamaatahir2005/gashunar/releases/tag/v0.2.0-build-4)
- [Real screenshots: dark/light, POS, products, reports, receipt](https://github.com/hamaatahir2005/gashunar/tree/build-previews)
- [Successful Windows test/build run](https://github.com/hamaatahir2005/gashunar/actions/runs/39393757558)

GitHub public release downloads work without signing in. GitHub normalizes spaces in release asset names to dots; the packaged artifact contains the original `GAS HUNAR.exe` filename.

Create your own administrator account on first launch. There is no default password or cloud login. The application works without internet; screenshots contain isolated demo records, not your restaurant data. Writable data is stored under `%LOCALAPPDATA%\GAS HUNAR`, never inside the executable or installation folder. `GAS_HUNAR_DATA` can override this for testing.

## بەکارهێنانی تایبەتمەندییە نوێکان

- لە سەرەوەی شاشە، **ڕووکار** بگۆڕە بۆ **ڕوون** یان **تاریک**. هەڵبژاردەکە بۆ هەر بەکارهێنەرێک جیاواز پاشەکەوت دەکرێت.
- لە داشبۆرد و ڕاپۆرت، **لە بەرواری** و **تا بەرواری** بنووسە یان لە ڕۆژژمێر هەڵیبژێرە؛ پاشان **حیسابکردن** دابگرە. هەردوو بەروارەکە دەژمێردرێن.
- کارتەکانی **قازانجی ڕۆژ، هەفتە و مانگ** بەپێی بەرواری کۆتایی هەڵبژێردراو حیساب دەکرێن. کات: عێراق؛ هەفتە: شەممە تا هەینی.
- لە **بەرهەمەکان → زیادکردنی بەرهەم → بارکردنی وێنە** وێنەی ناوخۆیی هەڵبژێرە. نرخ و ناو و کۆد بنووسە و پاشەکەوتی بکە. وێنە لە کاشێر و لیستی بەرهەمەکان دەردەکەوێت.
- لە وەسڵدا پرێنتەری دامەزراوی Windows و پانی **٥٨ ملم / ٨٠ ملم / A4** هەڵبژێرە. **پێشبینینی چاپ، چاپکردن و PDF** بەردەستن. هەڵبژاردەکانی پرێنتەر پاشەکەوت دەکرێن.

## Cashier and accounting

Open a drawer before cash operations. Select products, quantities and notes, choose takeaway/dine-in/delivery, then hold or pay. F2 focuses search/barcode, F8 holds, F9 pays. Resume held/partially paid orders under Orders. Confirmation issues an invoice and deducts recipes atomically. Confirmed sales are immutable. Cash/card allocations and partial payments are supported; full-order refunds can optionally restore original stock movements.

Net profit = net revenue − food cost − operating expenses. Tax is excluded from revenue. Purchases are inventory assets, not duplicate operating expenses. Cash receipts differ from revenue. Date filters do not change or backdate confirmed sales. Read [accounting rules](docs/ARCHITECTURE.md).

## Verified scope

Windows CI run `39393757558` passed **26 tests**, captured real Qt screens, built the EXE, and actually executed its self-check (SQLite, backups, Unicode PDF, thermal Qt PDF, theme switching and native window capture). Local syntax compilation and 10 dependency-free checks also passed. Physical thermal printing, installer/update behavior and a full Windows 10/11 device matrix remain unverified.

## Development and packaging

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python main.py
```

For a Windows x64 build with tests and screenshots, run `BUILD-EXE.bat` or:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
# Optional installer; requires Inno Setup 6 on PATH:
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1 -Installer
# Offline build with compatible pre-downloaded Windows wheels:
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1 -Wheelhouse D:\wheels
```

Development/building needs Python and available dependencies. The packaged application does not. Expected build output: `dist/GAS HUNAR.exe`; optional installer: `dist/GAS HUNAR Setup.exe`. The installer has not been built or accepted yet. Uninstall configuration preserves restaurant data.

Tests: `python -m pytest -q`; dependency-free checks: `python -m unittest discover -s tests -p stdlib_checks.py -v`. Linux development uses `.venv/bin/python`. Manual acceptance checklist: [docs/MANUAL_TESTS.md](docs/MANUAL_TESTS.md).

Backups use SQLite's online backup API, integrity checks, retention and staged restore. Backups are database-only: when moving computers, close the app and preserve the full data folder for uploaded images. Optional demo menu: `python scripts/seed_demo.py` after first-run admin setup, with the app closed and an empty menu. No fictional sales are inserted into real restaurant data.
