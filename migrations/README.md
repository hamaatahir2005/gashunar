# Versioned SQLite migrations

`database/engine.py` owns schema version 1 through SQLite `PRAGMA user_version`.
A new database is created under an exclusive transaction; role and settings seeds are inserted subsequently. Every connection enforces foreign keys, FULL synchronous durability, a busy timeout, and WAL mode. Startup runs integrity and foreign-key checks.

The application refuses an unversioned nonempty database or a schema newer than the executable. There are no destructive upgrade migrations in this release. Before adding version 2, add an explicit transactional v1→v2 migration, create a verified online backup, preserve historical monetary snapshots, and test upgrading a populated v1 database. `create_all` is never used as a substitute for altering an existing versioned schema.
