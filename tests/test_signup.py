import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from concurrent.futures import ThreadPoolExecutor
import pytest
from sqlalchemy import select,func
from PySide6.QtWidgets import QApplication,QDialog,QLineEdit
from database.engine import Database
from services.auth import Auth
from models.schema import User,Role,Employee,AuditLog
from ui.login import Login

PASSWORD='a-secure-registration-passphrase'


@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])


def test_first_signup_is_admin_and_survives_restart(tmp_path):
    path=tmp_path/'signup.sqlite3';db=Database(path);auth=Auth(db)
    user=auth.sign_up(' owner ',PASSWORD,PASSWORD,'بەڕێوەبەر')
    assert not auth.needs_setup();assert auth.login('owner',PASSWORD)==user;assert auth.actions(user)=={'*'}
    with db.read() as s:
        assert s.get(User,user).password_hash.startswith('$argon2id$')
        assert s.scalar(select(Employee).where(Employee.user_id==user)).name=='بەڕێوەبەر'
    db.engine.dispose();reopened=Database(path)
    assert Auth(reopened).login('owner',PASSWORD)==user
    reopened.engine.dispose()


def test_later_signup_is_only_cashier(system):
    x=system;user=x['auth'].sign_up('new.cashier',PASSWORD,PASSWORD,'New employee')
    assert x['auth'].login('new.cashier',PASSWORD)==user
    assert x['auth'].actions(user)=={'pos','customers'}
    for action in ('reports','settings','refunds','employees','products'):
        with pytest.raises(PermissionError):x['auth'].require(user,action)
    with x['db'].read() as s:
        audit=s.scalar(select(AuditLog).where(AuditLog.user_id==user,AuditLog.action=='user.signed_up'))
        assert audit and PASSWORD not in audit.detail
    with pytest.raises(TypeError):x['auth'].sign_up('elevated',PASSWORD,PASSWORD,role_name='admin')


def test_invalid_registration_is_atomic(system):
    x=system
    cases=[('',PASSWORD,PASSWORD,''),('bad\nuser',PASSWORD,PASSWORD,''),('u'*81,PASSWORD,PASSWORD,''),
           ('normal','short','short',''),('normal','x'*257,'x'*257,''),('normal',PASSWORD,'mismatch',''),
           ('normal',PASSWORD,PASSWORD,'x'*121)]
    with x['db'].read() as s:before=s.scalar(select(func.count(User.id)))
    for args in cases:
        with pytest.raises(ValueError):x['auth'].sign_up(*args)
    with x['db'].read() as s:assert s.scalar(select(func.count(User.id)))==before
    with pytest.raises(ValueError,match='already taken'):x['auth'].sign_up(' admin ',PASSWORD,PASSWORD)
    assert x['auth'].login('admin','a-secure-test-passphrase')==x['admin']


def test_concurrent_first_signups_cannot_create_two_admins(tmp_path):
    db=Database(tmp_path/'race.sqlite3');auth=Auth(db)
    with ThreadPoolExecutor(max_workers=2) as pool:
        users=list(pool.map(lambda name:auth.sign_up(name,PASSWORD,PASSWORD),['first','second']))
    roles=[auth.actions(user) for user in users]
    assert sum('*' in actions for actions in roles)==1
    assert sum(actions=={'pos','customers'} for actions in roles)==1
    db.engine.dispose()


def test_concurrent_duplicate_signup_creates_one_user(system):
    auth=system['auth']
    def register(_):
        try:return auth.sign_up('same-user',PASSWORD,PASSWORD)
        except ValueError:return None
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(register,range(2)))
    assert sum(user is not None for user in results)==1


def test_signup_and_login_ui_flow(app,tmp_path):
    db=Database(tmp_path/'ui.sqlite3');auth=Auth(db)
    dialog=Login(auth,'en');dialog.show();app.processEvents()
    assert dialog.tabs.currentIndex()==1
    dialog.signup_name.setText('Restaurant owner');dialog.signup_username.setText('owner')
    dialog.signup_password.setText(PASSWORD);dialog.repeat.setText('wrong')
    dialog.create_account();assert 'do not match' in dialog.message.text();assert auth.needs_setup()
    dialog.repeat.setText(PASSWORD);dialog.create_account()
    assert dialog.tabs.currentIndex()==0;assert dialog.username.text()=='owner'
    assert dialog.user is None and dialog.password.text()==''
    assert dialog.signup_password.text()=='' and dialog.repeat.text()==''
    dialog.password.setText('incorrect');dialog.submit()
    assert dialog.user is None and dialog.result()!=QDialog.DialogCode.Accepted
    dialog.password.setText(PASSWORD);dialog.submit()
    assert dialog.result()==QDialog.DialogCode.Accepted
    assert auth.actions(dialog.user)=={'*'}
    new=Login(auth,'ckb');assert new.tabs.currentIndex()==0 and new.tabs.count()==2
    new.tabs.setCurrentIndex(1);new.signup_username.setText('کاشێر');new.signup_name.setText('کارمەندی نوێ')
    new.signup_password.setText(PASSWORD);new.repeat.setText(PASSWORD);new.create_account()
    new.password.setText(PASSWORD);new.submit();assert auth.actions(new.user)=={'pos','customers'}
    locked=Login(auth,'en',allow_signup=False);assert locked.tabs.count()==1 and locked.signup_page is None
    locked.reject();db.engine.dispose()


def test_password_fields_do_not_silently_truncate(app,system):
    dialog=Login(system['auth'],'en');dialog.tabs.setCurrentIndex(1)
    dialog.signup_username.setText('long-password');dialog.signup_password.setText('x'*257);dialog.repeat.setText('x'*257)
    assert len(dialog.signup_password.text())==257
    dialog.create_account();assert '10–256' in dialog.message.text()
    assert dialog.signup_password.echoMode()==QLineEdit.EchoMode.Password
    dialog.reject()


def test_login_ui_localized_and_no_signup_during_unlock(app,system):
    for language in ('ckb','ar','en'):
        dialog=Login(system['auth'],language)
        assert dialog.tabs.count()==2
        dialog.tabs.setCurrentIndex(1);dialog.signup_username.setText('admin');dialog.signup_password.setText(PASSWORD);dialog.repeat.setText(PASSWORD)
        dialog.create_account();assert dialog.message.text()
        dialog.reject()
