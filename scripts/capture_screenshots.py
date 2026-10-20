"""Capture real Qt screens using a disposable, explicitly marked demo database.

python scripts/capture_screenshots.py --output dist/screenshots
Requires the same dependencies as the app. Never reads or modifies restaurant data.
"""
import argparse
import os
import secrets
import sys
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='dist/screenshots')
    args=parser.parse_args()
    output=Path(args.output).resolve();output.mkdir(parents=True,exist_ok=True)
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QFontDatabase,QFont
    from sqlalchemy import select
    from database.engine import Database
    from services.auth import Auth
    from services.catalog import Catalog
    from services.operations import Operations
    from services.orders import Orders
    from models.schema import ExpenseCategory
    from core.paths import resource
    from core.dates import business_today
    from ui.window import Window
    app=QApplication.instance() or QApplication([])
    app.setStyle('Fusion')
    QFontDatabase.addApplicationFont(str(resource('assets/DejaVuSans.ttf')))
    app.setFont(QFont('DejaVu Sans',10))
    with TemporaryDirectory(prefix='gas-hunar-screenshot-') as folder:
        db=Database(Path(folder)/'demo.sqlite3');auth=Auth(db)
        actor=auth.setup('screenshot-demo',secrets.token_urlsafe(32))
        catalog=Catalog(db,auth);ops=Operations(db,auth);orders=Orders(db,auth)
        products=[]
        for name,code,price,cost,cat in [('کەباب','KEB','10000','3000','برژاو'),('شاورمە','SHA','5000','1500','خێرا'),('چای','TEA','1000','100','خواردنەوە'),('ئاو','WAT','500','200','خواردنەوە'),('مریشکی برژاو','CHK','12000','4500','برژاو'),('برنج','RICE','3000','900','خواردن')]:
            products.append(catalog.save(actor,name,code,price,cost,cat))
        catalog.image(actor,products[0],resource('assets/gas-hunar.png'))
        meat=ops.ingredient(actor,'گۆشت','g','10','500')
        ops.adjust_stock(actor,meat,'10000','Demo opening stock');ops.recipe(actor,products[0],meat,'200')
        customer=ops.customer(actor,'کڕیاری نموونە','07500000000','هەولێر')
        tables=[ops.table(actor,f'A{i}',4,'Main') for i in range(1,7)]
        orders.open_drawer(actor,'50000')
        for product,qty,total in [(products[0],2,'20000'),(products[1],3,'15000'),(products[2],4,'4000')]:
            oid=orders.hold(actor,[{'product_id':product,'quantity':qty}],customer_id=customer)
            orders.pay(actor,oid,[('cash',total)],uuid4().hex)
        pending=orders.hold(actor,[{'product_id':products[4],'quantity':2,'notes':'بێ خوێ'}],kind='dine-in',table_id=tables[0],customer_id=customer)
        orders.confirm(actor,pending)
        with db.read() as s:category=s.scalar(select(ExpenseCategory.id))
        ops.expense(actor,category,'2500','خەرجی نموونە',business_today().isoformat())
        window=Window(db,auth,actor);window.resize(1366,800);window.show()
        try:
            for name,filename in [('Dashboard','01-dashboard.png'),('Point of sale','02-pos.png'),('Kitchen','03-kitchen.png'),('Inventory','04-inventory.png'),('Products','05-products.png'),('Reports','06-reports.png')]:
                window.navigate(name)
                if name=='Point of sale':
                    page=window.pages[name]
                    with db.read() as s:
                        from models.schema import Product
                        page.add(s.get(Product,products[0]));page.add(s.get(Product,products[2]))
                window.statusBar().showMessage('DEMO DATA / داتای نموونە • OFFLINE • GAS HUNAR')
                app.processEvents()
                target=output/filename
                if not window.grab().save(str(target),'PNG'):
                    raise RuntimeError('Screenshot save failed: '+str(target))
                print(target)
            window.navigate('Dashboard');window.set_theme('light');app.processEvents()
            window.grab().save(str(output/'07-dashboard-light.png'),'PNG')
            window.set_theme('dark');window.navigate('Products')
            from ui.products import ProductDialog
            dialog=ProductDialog(window,products[0]);dialog.show();app.processEvents();dialog.grab().save(str(output/'08-product-photo-form.png'),'PNG');dialog.reject()
            from ui.receipt import ReceiptDialog
            receipt=ReceiptDialog(window,oid);receipt.show();app.processEvents();receipt.grab().save(str(output/'09-thermal-receipt.png'),'PNG');receipt.reject()
        finally:
            window.close();app.processEvents();db.engine.dispose()
    return 0


if __name__=='__main__':
    raise SystemExit(main())
