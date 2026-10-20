import logging
import sys
from logging.handlers import RotatingFileHandler
from PySide6.QtWidgets import QApplication,QDialog,QMessageBox
from PySide6.QtCore import QLockFile,Qt
from PySide6.QtGui import QFontDatabase,QFont,QIcon
from core.paths import data_dir,resource
from database.engine import Database
from services.auth import Auth
from services.settings import Settings
from services.backup import Backup
from ui.login import Login
from ui.window import Window
from ui.theme import stylesheet


def run():
    app=QApplication(sys.argv);app.setApplicationName('GAS HUNAR');app.setOrganizationName('GAS HUNAR');app.setStyle('Fusion')
    root=data_dir();handler=RotatingFileHandler(root/'application.log',maxBytes=2_000_000,backupCount=3,encoding='utf-8');logging.basicConfig(level=logging.INFO,handlers=[handler])
    lock=QLockFile(str(root/'application.lock'));lock.setStaleLockTime(0)
    if not lock.tryLock(100):QMessageBox.warning(None,'GAS HUNAR','Another instance is using this database.');return 1
    try:
        Backup.apply_pending(root/'gas-hunar.sqlite3');db=Database(root/'gas-hunar.sqlite3');auth=Auth(db);settings=Settings(db,auth).all()
        font=resource('assets/DejaVuSans.ttf')
        if font.exists():QFontDatabase.addApplicationFont(str(font));app.setFont(QFont('DejaVu Sans',10))
        app.setStyleSheet(stylesheet(settings['theme']));app.setLayoutDirection(Qt.LayoutDirection.RightToLeft if settings['language'] in ('ckb','ar') else Qt.LayoutDirection.LeftToRight)
        app.setWindowIcon(QIcon(str(resource('assets/gas-hunar.ico'))))
        login=Login(auth,settings['language'])
        if login.exec()!=QDialog.DialogCode.Accepted:return 0
        window=Window(db,auth,login.user);window.show();result=app.exec();db.engine.dispose();return result
    except Exception as exc:
        logging.exception('Startup failure');QMessageBox.critical(None,'GAS HUNAR',str(exc));return 1
    finally:lock.unlock()
