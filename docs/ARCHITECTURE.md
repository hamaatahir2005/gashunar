# Architecture and accounting contract

Python 3.12 / native Qt Widgets → service layer → SQLAlchemy sessions → local SQLite.
`ui` contains dialogs and views; `services` contains permissions and transactions; `models` contains the relational schema. `core` owns resource/data paths and decimal arithmetic. `printing` uses Qt's Unicode layout and ReportLab PDFs. No application code starts a server, cloud connection, telemetry, or network client.

## Persistence

All mutable data goes to `%LOCALAPPDATA%\GAS HUNAR` on Windows, or `$GAS_HUNAR_DATA` if explicitly configured. The database, uploads, logs, and backups survive installation upgrades and uninstall. A process-level QLockFile prevents two GUI instances opening the same dataset. Future LAN clients require an authenticated application service and deliberate concurrency testing; no multi-terminal synchronization exists.

SQLite uses foreign keys, WAL, FULL synchronous mode, and BEGIN IMMEDIATE for business writes. Money uses integer thousandths of IQD; displayed decimal precision never changes stored values. Ingredient quantities also use thousandths of the declared unit. Whole product quantities are supported. Decimal HALF_UP rounding applies at monetary boundaries. Tax and service charge are independently computed on the discounted subtotal, without tax-on-service.

## Sale lifecycle

A held order reserves a table but has no revenue, invoice, payment, or stock effect. Held orders can be replaced. Confirmation snapshots the order, deducts the recipe, issues a unique sequential invoice, and recognizes revenue. Payment can atomically confirm a held order. Confirmed orders cannot be edited; partial cash/card payments leave the order confirmed; fully paid orders become completed. Payment keys prevent retries from inserting duplicate payments. BEGIN IMMEDIATE prevents concurrent overpayment and stock races. Cash entries require an open drawer. Kitchen state progresses independently.

Full-order refunds reverse revenue and return only actual receipts. The operator chooses whether original ingredient movements are restored. Without restock, original COGS remains an expense of the wasted meal. Refunds are unique per order and reverse original stock movements even if recipes later change. Partial item refunds and split-bill reassignment are not implemented.

## Accounting

Revenue = confirmed subtotal − discounts + service charge − refund revenue, excluding collected tax. COGS = snapshotted order ingredient cost (or product fallback cost) − cost reversals for restocked refunds. Gross profit = revenue − COGS. Net profit = gross profit − operating expenses. Purchase records increase stock; they are not operating expenses. Weighted-average ingredient cost is updated on purchase. Held-order cost estimates are refreshed from current recipes and ingredient costs at confirmation; the confirmed cost snapshot is immutable.

Cash receipts differ from revenue: unpaid confirmed orders are revenue with a receivable. The cash movement metric includes recorded cash receipts less cash refunds and drawer-linked expenses; opening float and supplier purchase payments are separate. Purchase payments have no cash/card allocation in this release, so the dashboard does not claim a complete general-ledger cash balance. Supplier outstanding amounts derive from purchase total minus paid; no supplier settlement ledger yet. Employee salary profiles are not payroll expense until an actual expense is recorded.

## Security and recovery

First-run admin creation requires a unique username and a 10–256 character passphrase; Argon2id hashes are stored. Roles are database permission rows. Services check permissions and audit sensitive changes. Five failed logins cause a five-minute local lockout. Inactivity opens a modal login. No production passwords are seeded. Local SQLite is not encrypted: OS account security and disk encryption protect data at rest. Encrypted backup support is deferred.

Online backups use sqlite3.Connection.backup, integrity checks, schema checks, atomic rename, SHA-256 history, and retention. Restore stages a verified database; the next startup applies it before engine creation and preserves a pre-restore database. Database-only backups do not include image/receipt files: archive the whole data folder separately while the application is closed when migrating computers. Logs rotate and must be handled as business data.

Scheduled backups and report exports use Qt workers. Exit backup and dashboard aggregations are synchronous in this release. Tables/search views cap results at 500; product grid caps at 150; production pagination and large-data load testing remain open.
