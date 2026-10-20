from datetime import date,timedelta
from decimal import Decimal
from uuid import uuid4
import sqlite3
import pytest
from sqlalchemy import select,func
from models.schema import *
from core.money import units
from database.engine import Database
from printing.receipts import receipt_html,generate_pdf


def hold(x,p,quantity=1,**kwargs):
    return x['orders'].hold(x['admin'],[{'product_id':p,'quantity':quantity}],**kwargs)


def test_first_run_login_and_argon(system):
    x=system
    assert not x['auth'].needs_setup()
    assert x['auth'].login('admin','a-secure-test-passphrase')==x['admin']
    with pytest.raises(PermissionError):x['auth'].login('admin','wrong')
    with pytest.raises(ValueError):x['auth'].setup('other','a-secure-test-passphrase')
    with x['db'].read() as s:assert s.get(User,x['admin']).password_hash.startswith('$argon2id$')


def test_permissions_enforced(system):
    x=system;k=x['auth'].create_user(x['admin'],'chef','a-secure-test-passphrase','kitchen')
    with pytest.raises(PermissionError):x['catalog'].save(k,'Tea','T','1000')
    with pytest.raises(PermissionError):x['finance'].summary(k)
    with pytest.raises(PermissionError):x['settings'].save(k,{'tax_rate':'5'})


def test_login_lockout(system):
    x=system
    for _ in range(5):
        with pytest.raises(PermissionError):x['auth'].login('admin','incorrect')
    with pytest.raises(PermissionError):x['auth'].login('admin','a-secure-test-passphrase')


def test_product_unicode_search_archive(system):
    x=system;p=x['catalog'].save(x['admin'],'شاورمە','SHA','5000','1500',barcode='00123')
    assert x['catalog'].list(x['admin'],'00123')[0].name=='شاورمە'
    x['catalog'].archive(x['admin'],p)
    assert x['catalog'].list(x['admin'])==[]


def test_discounts_taxes_and_split_payment(system,menu):
    x=system;p,i=menu;a=x['admin'];x['settings'].save(a,{'tax_rate':'5','service_rate':'10'})
    oid=hold(x,p,2,discount='10',percent=True)
    with x['db'].read() as s:
        order=s.get(Order,oid);assert (order.subtotal,order.discount,order.tax,order.service,order.total)==tuple(units(v) for v in ['20000','2000','900','1800','20700'])
    token=uuid4().hex;x['orders'].pay(a,oid,[('cash','10000'),('card','10700')],token);x['orders'].pay(a,oid,[('cash','10000'),('card','10700')],token)
    with x['db'].read() as s:
        assert s.get(Order,oid).status=='completed';assert s.get(Ingredient,i).quantity==units('600')
        assert s.scalar(select(func.count(Payment.id)))==2
        assert s.scalar(select(func.count(Invoice.id)))==1
    assert x['db'].integrity()=='ok'


def test_rollback_prevents_partial_stock_and_payment(system,menu):
    x=system;p,i=menu;a=x['admin'];oid=hold(x,p,6)
    with pytest.raises(ValueError):x['orders'].pay(a,oid,[('cash','60000')],uuid4().hex)
    with x['db'].read() as s:
        assert s.get(Ingredient,i).quantity==units('1000');assert s.get(Order,oid).status=='held'
        assert s.scalar(select(func.count(Payment.id)))==0
        assert s.scalar(select(func.count(Invoice.id)))==0


def test_partial_payments_and_overpayment(system,menu):
    x=system;p,_=menu;a=x['admin'];oid=hold(x,p)
    x['orders'].pay(a,oid,[('cash','4000')],uuid4().hex)
    with pytest.raises(ValueError):x['orders'].pay(a,oid,[('card','7000')],uuid4().hex)
    x['orders'].pay(a,oid,[('card','6000')],uuid4().hex)
    with x['db'].read() as s:assert s.get(Order,oid).status=='completed'


def test_refund_is_idempotent_and_reverses_original_recipe(system,menu):
    x=system;p,i=menu;a=x['admin'];oid=hold(x,p)
    x['orders'].pay(a,oid,[('cash','10000')],uuid4().hex)
    x['ops'].recipe(a,p,i,'500')
    x['orders'].refund(a,oid,'Customer returned item',restock=True)
    x['orders'].refund(a,oid,'Retry',restock=True)
    with x['db'].read() as s:
        assert s.get(Ingredient,i).quantity==units('1000');assert s.scalar(select(func.count(Refund.id)))==1
    assert x['finance'].summary(a)['net_profit']==0


def test_wasted_refund_keeps_cogs(system,menu):
    x=system;p,i=menu;a=x['admin'];oid=hold(x,p);x['orders'].pay(a,oid,[('cash','10000')],uuid4().hex)
    x['orders'].refund(a,oid,'Not restockable',restock=False)
    result=x['finance'].summary(a);assert result['net_sales']==0;assert result['cogs']==units('2000');assert result['net_profit']==units('-2000')


def test_stock_adjustment_and_purchase_not_expense(system,menu):
    x=system;p,i=menu;a=x['admin'];supplier=x['ops'].supplier(a,'Local supplier')
    x['ops'].purchase(a,supplier,[(i,'100','10')],paid='1000',token='purchase-1')
    x['ops'].purchase(a,supplier,[(i,'100','10')],paid='1000',token='purchase-1')
    with x['db'].read() as s:assert s.get(Ingredient,i).quantity==units('1100')
    assert x['finance'].summary(a)['expenses']==0
    with pytest.raises(ValueError):x['ops'].adjust_stock(a,i,'-2000','waste')


def test_expense_profit_cash_reconciliation(system,menu):
    x=system;p,_=menu;a=x['admin'];oid=hold(x,p);x['orders'].pay(a,oid,[('cash','10000')],uuid4().hex)
    with x['db'].read() as s:category=s.scalar(select(ExpenseCategory.id))
    x['ops'].expense(a,category,'1000','Electricity',date.today().isoformat())
    result=x['finance'].summary(a)
    assert result['net_sales']==units('10000');assert result['gross_profit']==units('8000');assert result['net_profit']==units('7000')
    assert x['orders'].close_drawer(a,'59000')==0


def test_hold_resume_and_no_stock_until_confirmed(system,menu):
    x=system;p,i=menu;a=x['admin'];oid=hold(x,p)
    x['orders'].hold(a,[{'product_id':p,'quantity':2}],order_id=oid)
    with x['db'].read() as s:assert s.get(Ingredient,i).quantity==units('1000')
    x['orders'].confirm(a,oid);x['orders'].confirm(a,oid)
    with x['db'].read() as s:assert s.get(Ingredient,i).quantity==units('600')
    with pytest.raises(ValueError):x['orders'].hold(a,[{'product_id':p,'quantity':3}],order_id=oid)


def test_receipt_unicode_pdf(system,menu,tmp_path):
    x=system;p,_=menu;a=x['admin'];oid=hold(x,p);x['orders'].pay(a,oid,[('cash','10000')],uuid4().hex)
    settings=x['settings'].all();html=receipt_html(x['db'],oid,settings)
    assert 'کەباب' in html and 'rtl' in html and 'GH-' in html
    target=generate_pdf(x['db'],oid,settings,tmp_path/'receipt.pdf');assert target.read_bytes().startswith(b'%PDF')


def test_backup_restore_and_integrity(system,menu,tmp_path):
    x=system;p,_=menu;a=x['admin'];path=x['backup'].create(a,tmp_path/'usb');assert x['backup'].verify(path)
    x['ops'].customer(a,'After backup');x['backup'].stage_restore(a,path)
    x['db'].engine.dispose();assert x['backup'].apply_pending(x['db'].path)
    restored=Database(x['db'].path)
    with restored.read() as s:assert s.scalar(select(func.count(Customer.id)))==0
    assert restored.integrity()=='ok';restored.engine.dispose()


def test_migration_reopen_and_reject_newer(system,tmp_path):
    x=system;db=Database(x['db'].path);assert db.integrity()=='ok';db.engine.dispose()
    path=tmp_path/'future.sqlite3'
    with sqlite3.connect(path) as c:c.execute('PRAGMA user_version=999')
    with pytest.raises(RuntimeError):Database(path)


def test_table_occupancy_kitchen(system,menu):
    x=system;p,_=menu;a=x['admin'];table=x['ops'].table(a,'A1',4)
    oid=hold(x,p,kind='dine-in',table_id=table)
    with pytest.raises(ValueError):hold(x,p,kind='dine-in',table_id=table)
    x['orders'].confirm(a,oid)
    for state in ['preparing','ready','completed']:x['orders'].kitchen(a,oid,state)
    with pytest.raises(ValueError):x['orders'].kitchen(a,oid,'preparing')


def test_import_atomicity(system,tmp_path):
    x=system;path=tmp_path/'import.csv';path.write_text('name,code,price,cost\nTea,T,1000,100\nBad,B,-10,0\n')
    with pytest.raises(ValueError):x['catalog'].import_csv(x['admin'],path)
    assert x['catalog'].list(x['admin'])==[]
