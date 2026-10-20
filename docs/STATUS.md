# Implementation and verification checklist

Release: **0.1.0 development phase — not production accepted**.

## Created in source

- [x] Modular Python project; SQLAlchemy schema for all requested baseline tables.
- [x] SQLite version-1 initialization, foreign keys, WAL, reserved write locks, integrity checks.
- [x] First-admin setup, Argon2id, role permissions, lockout, password change, audit records.
- [x] Persisted language/theme/tax/receipt/backup settings; Kurdish primary RTL navigation.
- [x] Native Qt dashboard, POS, orders, product, table, kitchen, inventory, purchase, expense, customer, employee, report, settings and backup screens.
- [x] Product creation/edit/archive, category creation, barcode search, safe local image conversion, atomic CSV import, CSV export.
- [x] Product cart, quantities/notes, order types, fixed/percent discounts, tax/service, held orders, confirmation, immutable confirmed sales.
- [x] Cash/card/split-tender/partial payments, invoice sequencing, payment retry keys, whole-order refunds.
- [x] Drawer opening/closing/count variance; table occupancy and transfers; reservation service and basic reservation form.
- [x] Kitchen workflow and periodic refresh on the local machine.
- [x] Ingredient records, recipes, negative-stock protection, movements, adjustments/waste reasons, purchases, suppliers, weighted average costs.
- [x] Expense entry/edit with closed-drawer restrictions; customer profiles; employee account creation and attendance toggling.
- [x] Revenue/COGS/profit summaries; report PDF/CSV export; customer receivable calculation service.
- [x] Qt print preview and receipt PDF source for 58mm/80mm/A4 with bundled Unicode font.
- [x] Verified online backup source, schedule, retention, staged restore, recovery copy.
- [x] Original icon/logo assets and redistributable font/license.
- [x] PyInstaller spec, Windows PowerShell build script, Inno Setup definition.
- [x] Automated test source for authentication, permissions, products, orders, discounts/tax, payments, refunds, inventory, purchase accounting, expenses/profit, migrations, backup/restore, Unicode receipts and screen construction.

“Created in source” is not a runtime verification claim.

## Actually executed in this Linux environment

- [x] Python 3.12 syntax compilation of all source and tests: succeeded.
- [x] Dependency-free unittest suite: **10 tests passed** (arithmetic, formatting, localization, icon/font).
- [x] Icon/logo generator: ran successfully; PNG, ICO, SVG and Unicode font exist.
- [ ] Full Pytest suite: blocked because PySide6, SQLAlchemy, Argon2 and Pytest cannot be installed without network permissions. Two permission-waiting installation calls were interrupted; subsequent non-escalated requests fail with socket PermissionError. No test pass is claimed.
- [ ] Native application launch and GUI smoke test: blocked by absent runtime dependencies.
- [ ] ReportLab Arabic-shaping receipt generation: not executed (shaping dependencies absent).
- [ ] SQLite business integration/backup tests: not executed (ORM dependency absent).
- [ ] Windows EXE generated or verified: **no EXE exists**.
- [ ] Installer generated or verified: **no installer exists**.

## Remaining product work

- [ ] Complete professional floor-plan canvas, editable positions, table merge and bill splitting.
- [ ] POS interfaces for variant/modifier selection, modifier-recipe costs, priorities, kitchen ticket printing.
- [ ] Partial item refunds, payment corrections, zero-value checkout UX, customer credit policy.
- [ ] Reservation lifecycle/cancellation UI, UTC/timezone-safe display throughout, occupied-table timing.
- [ ] Full customer history, loyalty earning/redemption and customer statements.
- [ ] Employee profiles/salary editing, salary/attendance reports, granular role/permission editor.
- [ ] Supplier settlement ledger, purchase returns, inventory valuation/report UI and recipe editor listing/deletion.
- [ ] Expense attachments, approval workflow, custom expense category management.
- [ ] Daily financial closing, product/category profitability and complete cash-flow ledger.
- [ ] All requested dashboard comparisons; full cash balance; extended tax reconciliation.
- [ ] Receipt logo/editor and date formatting, saved printer preference, direct Windows printer/thermal hardware tests.
- [ ] Complete Arabic/Sorani field/error translations and external linguistic review. Navigation is translated; some fields/errors remain English.
- [ ] Optional encrypted backups, asset-inclusive backup/restore, backup-history checksum selection during restore.
- [ ] Paginated query UI, large-dataset performance, async dashboard/exit backup, responsive screen polish and screenshots.
- [ ] Optional additional currencies; only IQD is supported.
- [ ] Release dependency lock with tested versions, signed EXE, supported Windows 10/11 matrix, install/update/uninstall tests.

## Next execution order

1. Install requirements in a permitted environment (or use a local wheelhouse), run the full test suite, fix failures.
2. Run and visually inspect each Qt screen in Sorani/Arabic/English, dark/light, 1366×768 and high DPI.
3. Implement remaining money/stock/restore edge cases before adding remaining management UI.
4. Complete manual offline/printer/recovery tests, build on Windows, test installer/update behavior. Only then advance release acceptance.

## Follow-up: EXE and screenshot delivery

Added `BUILD-EXE.bat`, an actual Qt screenshot capture script using temporary demo records, and a manually triggered Windows CI workflow. The Windows build script now captures screenshots after passing tests and before packaging. These Windows commands and screenshot generation remain unexecuted in this Linux environment. There is no actual EXE or system screenshot to deliver yet. A further dependency installation permission wait was interrupted; no runtime dependencies became available.
