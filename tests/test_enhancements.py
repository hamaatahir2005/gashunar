import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from datetime import date,timedelta
from uuid import uuid4
from pathlib import Path
import pytest
from PIL import Image
from sqlalchemy import select,func
from sqlalchemy.exc import IntegrityError
from PySide6.QtWidgets import QApplication,QDialog
from PySide6.QtGui import QPageLayout
from core.dates import period_dates,utc_midnight,parse_date,business_today
from core.money import units,money
from models.schema import Order,Product,ProductImage,ExpenseCategory
from services.settings import Settings
from database.engine import Database
from printing.receipts import receipt_html,make_printer,qt_receipt_pdf


@pytest.fixture
def qt_app():
    return QApplication.instance() or QApplication([])


def test_calendar_periods_and_local_midnight():
    periods=period_dates('2024-02-29')
    assert periods['day']==(date(2024,2,29),date(2024,2,29))
    assert periods['week']==(date(2024,2,24),date(2024,3,1))
    assert periods['month']==(date(2024,2,1),date(2024,2,29))
    assert utc_midnight('2026-10-20')=='2026-10-19T21:00:00.000000+00:00'
    assert period_dates('2026-12-31')['month'][1]==date(2026,12,31)
    assert parse_date('٢٠/١٠/٢٠٢٦')==date(2026,10,20)


def test_period_profit_uses_actual_sale_refund_and_expense_dates(system):
    x=system;a=x['admin'];p=x['catalog'].save(a,'Meal','DATE','10000','2000')
    def sale(timestamp):
        oid=x['orders'].hold(a,[{'product_id':p,'quantity':1}]);x['orders'].pay(a,oid,[('card','10000')],uuid4().hex)
        with x['db'].write() as s:s.get(Order,oid).confirmed_at=timestamp
        return oid
    sale('2026-10-19T20:59:59.000000+00:00')  # preceding Iraq date
    sale('2026-10-19T21:00:00.000000+00:00')  # start of selected Iraq day
    sale('2026-10-20T20:59:59.000000+00:00')
    sale('2026-10-20T21:00:00.000000+00:00')  # next Iraq date
    with x['db'].read() as s:category=s.scalar(select(ExpenseCategory.id))
    x['ops'].expense(a,category,'1000','Expense on reference day','2026-10-20','card')
    result=x['finance'].range_summary(a,'20/10/2026','20/10/2026')
    assert result['net_sales']==units('20000');assert result['cogs']==units('4000');assert result['net_profit']==units('15000')
    periods=x['finance'].periods(a,'2026-10-20')
    assert periods['day']['net_profit']==units('15000')
    assert periods['week']['net_profit']==units('31000')
    assert periods['month']['net_profit']==units('31000')
    with pytest.raises(ValueError):x['finance'].range_summary(a,'2026-10-21','2026-10-20')


def test_theme_and_printer_preferences_persist_without_admin_access(system):
    x=system;a=x['admin'];cashier=x['auth'].create_user(a,'cashier-preference','a-secure-test-passphrase','cashier')
    x['settings'].save_preferences(cashier,{'theme':'light','paper_width':'58','printer_name':'Thermal receipt'})
    reopened=Database(x['db'].path)
    preferences=Settings(reopened,x['auth']).for_user(cashier)
    assert preferences['theme']=='light';assert preferences['paper_width']=='58';assert preferences['printer_name']=='Thermal receipt'
    assert x['settings'].for_user(a)['theme']=='dark'
    assert not any(k.startswith('user.') for k in x['settings'].all())
    with pytest.raises(ValueError):x['settings'].save_preferences(cashier,{'tax_rate':'0'})
    with pytest.raises(PermissionError):x['settings'].save(cashier,{'tax_rate':'0'})
    reopened.engine.dispose()


def test_atomic_product_and_local_image_upload(system,tmp_path):
    x=system;a=x['admin'];source=tmp_path/'camera.png';Image.new('RGB',(1600,1200),'orange').save(source)
    p=x['catalog'].save(a,'Food photo','PHOTO','5000',image_path=source)
    saved=x['catalog'].images(a,[p])[p]
    assert saved.is_file() and saved!=source
    with Image.open(saved) as image:assert max(image.size)<=1024
    before=set((x['db'].path.parent/'images').iterdir())
    with pytest.raises(IntegrityError):x['catalog'].save(a,'Duplicate','PHOTO','9000',image_path=source)
    assert set((x['db'].path.parent/'images').iterdir())==before
    broken=tmp_path/'bad.png';broken.write_text('not an image')
    with pytest.raises(ValueError):x['catalog'].save(a,'Broken','BROKEN','5000',image_path=broken)
    with x['db'].read() as s:assert s.scalar(select(func.count(Product.id)))==1


def test_product_form_upload_and_theme_controls(qt_app,system,tmp_path,monkeypatch):
    from ui.window import Window
    from ui.products import ProductDialog
    from PySide6.QtWidgets import QMessageBox
    monkeypatch.setattr(QMessageBox,'question',lambda *args:QMessageBox.StandardButton.No)
    x=system;w=Window(x['db'],x['auth'],x['admin']);w.show();qt_app.processEvents()
    w.set_theme('light');assert x['settings'].for_user(x['admin'])['theme']=='light'
    w.set_theme('dark');assert w.theme_picker.currentData()=='dark'
    source=tmp_path/'photo.png';Image.new('RGB',(160,120),'gold').save(source)
    dialog=ProductDialog(w);dialog.fields['name'].setText('خواردن');dialog.fields['code'].setText('UI-PHOTO');dialog.fields['price'].setText('5000');dialog.set_image(source);dialog.save()
    assert dialog.result()==QDialog.DialogCode.Accepted;assert x['catalog'].images(x['admin'],[dialog.product_id])
    w.navigate('Point of sale');before=len(w.catalog.list(w.user))
    w.catalog.save(w.user,'New category item','NEWCAT','2000',category='Fresh category')
    w.navigate('Products');w.navigate('Point of sale')
    assert w.pages['Point of sale'].category.findText('Fresh category')>=0
    dashboard=w.pages['Dashboard'];assert 'IQD' in dashboard.profits['month'][0].text()
    w.close();qt_app.processEvents();assert not w.isVisible()


@pytest.mark.parametrize('paper',['58','80','A4'])
def test_qt_thermal_geometry_and_pdf(qt_app,system,paper,tmp_path):
    x=system;a=x['admin'];p=x['catalog'].save(a,'کەباب و برنج','PRINT','5000')
    oid=x['orders'].hold(a,[{'product_id':p,'quantity':1,'notes':'بێ خوێ'}]);x['orders'].pay(a,oid,[('card','5000')],uuid4().hex)
    settings=x['settings'].all();settings['paper_width']=paper
    html=receipt_html(x['db'],oid,settings)
    printer,document=make_printer(html,paper)
    assert abs(printer.pageLayout().fullRect(QPageLayout.Unit.Millimeter).width()-(210 if paper=='A4' else int(paper)))<1
    target=qt_receipt_pdf(html,tmp_path/f'receipt-{paper}.pdf',paper)
    assert target.read_bytes().startswith(b'%PDF') and target.stat().st_size>1000
    assert 'کەباب و برنج' in html and 'بێ خوێ' in html and 'rtl' in html
