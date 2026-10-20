from datetime import datetime, timedelta, timezone
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from sqlalchemy import select, func
from models.schema import User, Role, Permission, AuditLog, Employee, now

HASHER = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)


def validate_password(password):
    if not 10 <= len(password) <= 256:
        raise ValueError('Password must contain 10–256 characters')


def validate_username(username):
    username = username.strip()
    if not username or len(username) > 80 or not username.isprintable():
        raise ValueError('Enter a username (maximum 80 characters)')
    return username


def ensure_available(session, username):
    if session.scalar(select(User.id).where(User.username == username)) is not None:
        raise ValueError('This username is already taken')


class Auth:
    def __init__(self, db):
        self.db = db

    def needs_setup(self):
        with self.db.read() as s:
            return s.scalar(select(func.count(User.id))) == 0

    def setup(self, username, password):
        validate_password(password)
        username = validate_username(username)
        with self.db.write() as s:
            if s.scalar(select(func.count(User.id))):
                raise ValueError('An administrator already exists')
            ensure_available(s, username)
            role = s.scalar(select(Role).where(Role.name == 'admin'))
            user = User(username=username, password_hash=HASHER.hash(password), role_id=role.id)
            s.add(user)
            s.flush()
            s.add(Employee(name=username, user_id=user.id))
            s.add(AuditLog(user_id=user.id, action='admin.setup', detail=username))
            return user.id

    def sign_up(self, username, password, confirmation, full_name=''):
        """Create the first administrator or a restricted cashier account, atomically.

        No caller-supplied role is accepted. Existing users/roles are never changed.
        The user must sign in normally after registration.
        """
        username = validate_username(username)
        validate_password(password)
        if password != confirmation:
            raise ValueError('Passwords do not match')
        full_name = full_name.strip() or username
        if len(full_name) > 120 or not full_name.isprintable():
            raise ValueError('Enter a name (maximum 120 characters)')
        with self.db.write() as s:
            ensure_available(s, username)
            first_account = s.scalar(select(func.count(User.id))) == 0
            role_name = 'admin' if first_account else 'cashier'
            role = s.scalar(select(Role).where(Role.name == role_name))
            if role is None:
                raise RuntimeError('Required account role is missing')
            user = User(username=username, password_hash=HASHER.hash(password), role_id=role.id, active=True)
            s.add(user)
            s.flush()
            s.add(Employee(user_id=user.id, name=full_name))
            s.add(AuditLog(user_id=user.id, action='admin.setup' if first_account else 'user.signed_up',
                           detail=f'{username}: {role_name}'))
            return user.id

    def login(self, username, password):
        user_id = None
        with self.db.write() as s:
            user = s.scalar(select(User).where(User.username == username.strip()))
            if user and user.active and (not user.locked_until or user.locked_until <= now()):
                try:
                    HASHER.verify(user.password_hash, password)
                    user_id = user.id
                    user.failed_logins = 0
                    if HASHER.check_needs_rehash(user.password_hash):
                        user.password_hash = HASHER.hash(password)
                    s.add(AuditLog(user_id=user.id, action='login', detail='success'))
                except (VerificationError, InvalidHashError):
                    user.failed_logins += 1
                    if user.failed_logins >= 5:
                        user.locked_until = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
                    s.add(AuditLog(user_id=user.id, action='login.failed', detail='Invalid credentials'))
        if user_id is None:
            raise PermissionError('Invalid credentials or account temporarily locked')
        return user_id

    def actions(self, user_id):
        with self.db.read() as s:
            user = s.get(User, user_id)
            if not user or not user.active:
                return set()
            return set(s.scalars(select(Permission.action).where(Permission.role_id == user.role_id)))

    def require(self, user_id, action):
        actions = self.actions(user_id)
        if '*' not in actions and action not in actions:
            raise PermissionError('You do not have permission for this operation')

    def change_password(self, user_id, old, new):
        validate_password(new)
        with self.db.write() as s:
            user = s.get(User, user_id)
            try:
                HASHER.verify(user.password_hash, old)
            except (VerificationError, InvalidHashError) as exc:
                raise PermissionError('Current password is incorrect') from exc
            user.password_hash = HASHER.hash(new)
            s.add(AuditLog(user_id=user_id, action='password.changed', detail=''))

    def create_user(self, actor, username, password, role_name):
        self.require(actor, 'settings')
        validate_password(password)
        username = validate_username(username)
        with self.db.write() as s:
            ensure_available(s, username)
            role = s.scalar(select(Role).where(Role.name == role_name))
            if not role:
                raise ValueError('Unknown role')
            user = User(username=username.strip(), password_hash=HASHER.hash(password), role_id=role.id)
            s.add(user)
            s.flush()
            s.add(Employee(user_id=user.id, name=username.strip()))
            s.add(AuditLog(user_id=actor, action='user.created', detail=f'{username}: {role_name}'))
            return user.id
