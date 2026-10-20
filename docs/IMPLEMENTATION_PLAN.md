# Delivery plan

This repository preserves a usable engineering starting point. It is not a claim that the master acceptance criteria have been met.

| Phase | Work | Status |
|---|---|---|
| 1 | Inspect environment; define layers, schema, accounting and security contracts | Done in source/documentation |
| 2 | Versioned database, setup/authentication, RBAC, settings and data paths | Source written; runtime blocked |
| 3 | Menu, images, CSV, held orders, confirmation, payments, invoices, refunds | Core source written; integration tests written, not run |
| 4 | Tables, reservations, kitchen; inventory, recipes, purchasing and expenses | Core source written; advanced workflows remain |
| 5 | Customer and employee records, finance, Unicode receipts, printing and reports | Basic source written; advanced ledgers and management UX remain |
| 6 | Backup/restore, scheduled workers, audit and inactivity lock | Source written; restoration tests not run |
| 7 | Sorani RTL native UI, dark/light theme and original artwork | Screens written and assets generated; visual/runtime review blocked |
| 8 | Automated verification and failure correction | 10 dependency-free tests passed; full dependency tests blocked |
| 9 | Windows build and installer | Configuration written; Windows build and lifecycle verification pending |
| 10 | Complete advanced features, load/security review, release acceptance | Open; see STATUS.md |

No production release is authorized by this checklist. Dependency availability is the next execution blocker, followed by actual test results and Windows testing. The remaining feature list in STATUS.md is intentionally explicit to prevent a basic screen from being mistaken for a completed advanced module.
