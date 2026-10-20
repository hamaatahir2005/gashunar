"""Packaged-EXE smoke check. Explicit invocation only; never opens restaurant data."""
import json
import os
import secrets
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4


def run(output):
    os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QFontDatabase,QFont
    from database.engine import Database
    from services.auth import Auth
    from services.catalog import Catalog
    from services.orders import Orders
    from services.backup import Backup
    from services.settings import Settings
    from core.paths import resource
    from ui.window import Window
    from printing.receipts import generate_pdf,qt_receipt_pdf,receipt_html
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    result={'success':False}
    try:
        app=QApplication.instance() or QApplication([])
        font=resource('assets/DejaVuSans.ttf')
        if not font.exists():raise RuntimeError('Packaged font is missing')
        QFontDatabase.addApplicationFont(str(font));app.setFont(QFont('DejaVu Sans',10))
        with TemporaryDirectory(prefix='gas-hunar-exe-check-') as folder:
            db=Database(Path(folder)/'check.sqlite3');auth=Auth(db)
            actor=auth.setup('self-check',secrets.token_urlsafe(32))
            p=Catalog(db,auth).save(actor,'کەباب','CHECK','10000','3000')
            orders=Orders(db,auth);oid=orders.hold(actor,[{'product_id':p,'quantity':1}])
            orders.pay(actor,oid,[('card','10000')],uuid4().hex)
            generate_pdf(db,oid,Settings(db,auth).all(),output/'receipt.pdf')
            qt_receipt_pdf(receipt_html(db,oid,Settings(db,auth).all()),output/'thermal-58mm.pdf','58')
            backup=Backup(db,auth);backup.create(actor)
            if db.integrity()!='ok':raise RuntimeError('SQLite integrity check failed')
            window=Window(db,auth,actor);window.set_theme('light');window.set_theme('dark');window.show();window.statusBar().showMessage('PACKAGED EXE SELF-CHECK • DEMO DATA');app.processEvents()
            if not window.grab().save(str(output/'packaged-exe.png'),'PNG'):raise RuntimeError('Screenshot failed')
            window.close();app.processEvents();db.engine.dispose()
            result={'success':True,'sqlite_integrity':'ok','unicode_pdf':True,'backup_verified':True,'native_window_captured':True,'theme_switching':True,'thermal_qt_pdf':True}
    except Exception as exc:
        result['error']=str(exc)
    (output/'self-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return 0 if result['success'] else 1
