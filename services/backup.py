from contextlib import closing
import hashlib
import os
from pathlib import Path
import sqlite3
from datetime import datetime, timezone
from models.schema import BackupHistory, AuditLog
from models.schema import Base
from database.engine import SCHEMA_VERSION


class Backup:
    def __init__(self, db, auth):
        self.db, self.auth = db, auth

    @staticmethod
    def verify(path):
        path = Path(path).resolve()
        if not path.is_file():
            raise ValueError('Backup file not found')
        with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as con:
            if con.execute('PRAGMA integrity_check').fetchone()[0] != 'ok' or con.execute('PRAGMA foreign_key_check').fetchall():
                raise ValueError('Backup integrity verification failed')
            if con.execute('PRAGMA user_version').fetchone()[0] != SCHEMA_VERSION:
                raise ValueError('Unsupported backup schema version')
            tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not set(Base.metadata.tables) <= tables:
                raise ValueError('File is not a GAS HUNAR database')
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def create(self, actor, folder=None, retention=30, automatic=False):
        if not automatic:
            self.auth.require(actor, 'backup')
        target_dir = Path(folder or self.db.path.parent / 'backups').resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / ('gas-hunar-' + datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f') + '.sqlite3')
        temporary = target.with_suffix('.partial')
        try:
            with closing(sqlite3.connect(self.db.path)) as source, closing(sqlite3.connect(temporary)) as dest:
                source.backup(dest, pages=256)
            digest = self.verify(temporary)
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
        with self.db.write() as s:
            s.add(BackupHistory(path=str(target), sha256=digest))
            s.add(AuditLog(user_id=actor, action='backup.created', detail=str(target)))
        for old in sorted(target_dir.glob('gas-hunar-*.sqlite3'), reverse=True)[max(int(retention), 1):]:
            old.unlink()
        return target

    def stage_restore(self, actor, source):
        self.auth.require(actor, 'backup')
        self.verify(source)
        # Applied at next startup before any engine connections; current session is never overwritten.
        self.create(actor)
        target = self.db.path.parent / 'restore-pending.sqlite3'
        temporary = target.with_suffix('.partial')
        with closing(sqlite3.connect(Path(source).resolve().as_uri() + '?mode=ro', uri=True)) as src, closing(sqlite3.connect(temporary)) as dest:
            src.backup(dest)
        self.verify(temporary)
        os.replace(temporary, target)
        return target

    @staticmethod
    def apply_pending(db_path):
        path = Path(db_path)
        pending = path.parent / 'restore-pending.sqlite3'
        if not pending.exists():
            return False
        Backup.verify(pending)
        # App holds a process-level QLockFile. Preserve live DB before replacement.
        if path.exists():
            recovery = path.parent / ('before-restore-' + datetime.now().strftime('%Y%m%d%H%M%S') + '.sqlite3')
            with closing(sqlite3.connect(path)) as src, closing(sqlite3.connect(recovery)) as dst:
                src.backup(dst)
                src.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        for suffix in ('-wal', '-shm'):
            Path(str(path)+suffix).unlink(missing_ok=True)
        os.replace(pending, path)
        return True
