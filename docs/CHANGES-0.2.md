# GAS HUNAR 0.2

Requested UI and reporting update:

- Persistent light/dark selector in the main header, accessible to every active role. Preferences are separate per user; they cannot alter tax or financial permissions.
- Redesigned navy/gold and light palettes, selected navigation, cleaner tables, responsive scrollable financial overview and better product tiles.
- Day/week/month net profit cards follow the selected end date. Net profit = net revenue − snapshotted food cost − operating expenses; collected tax is excluded. Refunds are recognized on refund date. Iraq business time is UTC+03:00; weeks are Saturday–Friday.
- Date editors support typing `YYYY-MM-DD` or using the calendar. Both range endpoints are included. Reports and PDF/CSV exports use the selected dates. This does not backdate or change completed sales.
- Add/edit product dialog includes local image selection, preview and description. Image decode, conversion, product and image-reference writes are validated; a failed database write cleans up the new uploaded file. Images appear in product tables and POS. Existing uploads remain in the application data folder.
- Receipt dialog provides installed-printer selection, persistent per-user printer/paper preferences, Unicode preview, native Windows print dialog and PDF export. 58mm/80mm thermal pages use wrapped layouts and measured receipt height; A4 remains supported. A physical printer must be installed in Windows. No hardware printer pass is claimed.
- Upgrade requires no table changes: new preferences use existing settings rows and defaults are merged for older databases.
- Windows CI adds public prerelease EXE downloads and a public build-previews branch so users do not need a GitHub artifact login to see screenshots or download the program.

Validation: local syntax and 10 dependency-free checks passed. Windows run 39393757558 passed 26 automated tests, packaged and ran the EXE self-check, and published public downloads/screenshots. The broader advanced-feature backlog in STATUS.md remains open.
