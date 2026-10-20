from sqlalchemy import select
from models.schema import Setting, AuditLog
from database.engine import DEFAULTS
from core.money import decimal


class Settings:
    def __init__(self, db, auth):
        self.db, self.auth = db, auth

    def all(self):
        with self.db.read() as s:
            return {v.key: v.value for v in s.scalars(select(Setting))}

    def save(self, actor, values):
        self.auth.require(actor, 'settings')
        for key, value in values.items():
            if key not in DEFAULTS:
                raise ValueError('Unknown setting: ' + key)
            if key in ('tax_rate', 'service_rate') and not 0 <= decimal(value) <= 100:
                raise ValueError('Rates must be between 0 and 100')
            if key in ('backup_minutes', 'backup_retention', 'lock_minutes') and not 1 <= int(value) <= 10080:
                raise ValueError('Interval out of range')
            if key == 'precision' and value not in ('0', '1', '2', '3'):
                raise ValueError('Precision must be 0–3')
            if key == 'language' and value not in ('ckb', 'ar', 'en'):
                raise ValueError('Unsupported language')
            if key == 'theme' and value not in ('dark', 'light'):
                raise ValueError('Unsupported theme')
            if key == 'prevent_negative_stock' and value not in ('true', 'false'):
                raise ValueError('Invalid stock policy')
            if key == 'paper_width' and value not in ('58', '80', 'A4'):
                raise ValueError('Unsupported paper size')
            if key == 'currency' and value != 'IQD':
                raise ValueError('This release uses IQD only')
            if len(value) > 2000:
                raise ValueError('Setting too long')
        with self.db.write() as s:
            for key, value in values.items():
                s.merge(Setting(key=key, value=value))
            s.add(AuditLog(user_id=actor, action='settings.changed', detail=', '.join(values)))
