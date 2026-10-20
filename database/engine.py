from contextlib import contextmanager
from pathlib import Path
import sqlite3
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from models.schema import Base, Role, Permission, Setting, ExpenseCategory

SCHEMA_VERSION = 1
DEFAULTS = {'language': 'ckb', 'theme': 'dark', 'restaurant_name': 'GAS HUNAR — گەس هونەر',
            'address': '', 'phone': '', 'receipt_header': 'بەخێربێن', 'receipt_footer': 'سوپاس بۆ سەردانەکەتان',
            'currency': 'IQD', 'precision': '0', 'tax_rate': '0', 'service_rate': '0',
            'prevent_negative_stock': 'true', 'invoice_prefix': 'GH-', 'paper_width': '80', 'printer_name': '',
            'backup_minutes': '60', 'backup_retention': '30', 'backup_location': '', 'lock_minutes': '15'}
ROLE_ACTIONS = {'admin': ['*'], 'manager': ['products', 'pos', 'kitchen', 'tables', 'inventory', 'expenses', 'reports', 'customers', 'employees', 'refunds', 'backup'],
                'cashier': ['pos', 'customers'], 'waiter': ['pos', 'tables'], 'kitchen': ['kitchen']}


class Database:
    def __init__(self, path):
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(f'sqlite:///{self.path}', connect_args={'timeout': 15})
        @event.listens_for(self.engine, 'connect')
        def configure(connection, _):
            connection.execute('PRAGMA foreign_keys=ON')
            connection.execute('PRAGMA busy_timeout=15000')
            connection.execute('PRAGMA synchronous=FULL')
        self.sessions = sessionmaker(self.engine, expire_on_commit=False)
        self.migrate()

    def migrate(self):
        # Refuse unknown/newer schemas before any writes. Version changes must have explicit migrations.
        with sqlite3.connect(self.path) as connection:
            version = connection.execute('PRAGMA user_version').fetchone()[0]
            if version > SCHEMA_VERSION:
                raise RuntimeError('This database requires a newer GAS HUNAR version')
            if version == 0:
                tables = connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
                if tables:
                    raise RuntimeError('Unversioned database: restore a supported backup instead')
        if version == 0:
            with self.engine.begin() as connection:
                connection.exec_driver_sql('BEGIN EXCLUSIVE')
                Base.metadata.create_all(connection)
                with Session(bind=connection) as session:
                    for name, actions in ROLE_ACTIONS.items():
                        role = Role(name=name)
                        session.add(role)
                        session.flush()
                        session.add_all(Permission(role_id=role.id, action=a) for a in actions)
                    session.add_all(Setting(key=k, value=v) for k, v in DEFAULTS.items())
                    session.add_all(ExpenseCategory(name=x) for x in ['Salaries', 'Rent', 'Electricity', 'Water', 'Gas', 'Internet', 'Maintenance', 'Transportation', 'Other'])
                    session.flush()
                connection.exec_driver_sql(f'PRAGMA user_version={SCHEMA_VERSION}')
        with sqlite3.connect(self.path) as connection:
            connection.execute('PRAGMA journal_mode=WAL')
        if self.integrity() != 'ok':
            raise RuntimeError('Database integrity check failed')

    @contextmanager
    def read(self):
        with self.sessions() as session:
            yield session

    @contextmanager
    def write(self):
        # A reserved writer lock serializes inventory, invoice, payment and first-admin checks.
        with self.sessions() as session:
            session.connection().exec_driver_sql('BEGIN IMMEDIATE')
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    def integrity(self):
        with sqlite3.connect(self.path) as connection:
            result = connection.execute('PRAGMA integrity_check').fetchone()[0]
            foreign = connection.execute('PRAGMA foreign_key_check').fetchall()
        return result if not foreign else 'foreign key violations'
