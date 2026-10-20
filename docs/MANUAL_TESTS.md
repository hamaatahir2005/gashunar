# End-to-end acceptance checklist (not yet executed)

Use a disposable dataset with `GAS_HUNAR_DATA` pointing to a test folder. Never test restore or crash recovery on production records.

- [ ] Launch on Windows 10 and Windows 11 without Python installed, disconnect internet first.
- [ ] Create first admin; reject short/mismatched passwords; restart and authenticate.
- [ ] Create cashier/kitchen/manager accounts; verify restricted pages and service-level access errors.
- [ ] Test five failed logins, password change, inactivity lock and second-instance prevention.
- [ ] Add Sorani/Arabic/English products, categories, barcode and local PNG/JPEG images; restart and verify persistence.
- [ ] Import valid CSV; import a duplicate/negative-price CSV and verify whole import rollback.
- [ ] Open drawer with 50,000 IQD; create recipe with 200 g meat; open stock 1,000 g.
- [ ] Hold two kebabs at 10,000 each; verify stock stays 1,000 g.
- [ ] Apply 10% discount, 5% tax and 10% service. Expected total 20,700 IQD.
- [ ] Pay 10,000 cash + 10,700 card. Verify one invoice, two payments, 600 g remaining.
- [ ] Retry same transaction key and verify no double charge or double stock deduction.
- [ ] Test partial payment, overpayment rejection, insufficient stock rollback and immutable confirmed orders.
- [ ] Refund whole sale with restock; verify 1,000 g stock and reversed revenue. Repeat refund and verify no duplicate.
- [ ] Refund without restock; verify COGS remains as waste cost.
- [ ] Add cash expense, reconcile drawer exactly and with a deliberate variance.
- [ ] Purchase ingredients, verify weighted cost and that purchase does not appear as an operating expense.
- [ ] Confirm dine-in order, test occupied table rejection and transfer; advance kitchen new→preparing→ready→completed.
- [ ] Create overlapping reservations and check conflict handling across timezones.
- [ ] Generate Sorani PDF with joined characters. Inspect 58mm, 80mm and A4 wrapping and totals.
- [ ] Select installed Windows printer through preview; test physical printing, offline printer errors and receipt reprints.
- [ ] Export report PDF/CSV; compare revenue, tax, COGS, expenses and cash to actual records.
- [ ] Create backup on USB; verify checksum/history; reject corrupt/unsupported file; stage restore and restart.
- [ ] Verify pre-restore recovery file and database integrity, including foreign keys.
- [ ] Kill test app during payment/backup and restart; verify no partial sale/invoice/stock changes.
- [ ] Inspect Sorani RTL, Arabic RTL, English LTR; dark/light; 1366×768, 150%/200% DPI and full-screen cashier shortcuts F2/F8/F9.
- [ ] Build EXE; install; enter records; upgrade; uninstall. Confirm database and uploads remain intact.
- [ ] Profile startup and queries with a large dataset; verify bounded reads and no frozen long operations.

Release remains blocked until full automated tests, GUI launch, printing and Windows lifecycle tests actually pass.
