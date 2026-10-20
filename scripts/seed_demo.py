"""Opt-in sample restaurant records. Never creates credentials or modifies a nonempty menu."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from getpass import getpass
from sqlalchemy import select,func
from core.paths import data_dir
from database.engine import Database
from models.schema import Product
from services.auth import Auth
from services.catalog import Catalog
from services.operations import Operations


def main():
    db=Database(data_dir()/'gas-hunar.sqlite3');auth=Auth(db)
    user=auth.login(input('Administrator username: '),getpass('Password: '));auth.require(user,'settings')
    with db.read() as s:
        if s.scalar(select(func.count(Product.id))):raise ValueError('Demo import requires an empty menu')
    catalog=Catalog(db,auth);ops=Operations(db,auth)
    meat=ops.ingredient(user,'گۆشتی برژاو','g','15','500');ops.adjust_stock(user,meat,'10000','Demo opening stock')
    for name,code,price,cost,category in [('کەباب','KEB','10000','3000','برژاو'),('شاورمە','SHA','5000','1500','خێرا'),('چای','TEA','1000','100','خواردنەوە'),('ئاو','WAT','500','200','خواردنەوە')]:
        p=catalog.save(user,name,code,price,cost,category)
        if code=='KEB':ops.recipe(user,p,meat,'200')
    for i in range(1,7):ops.table(user,f'A{i}',4,'Main')
    ops.customer(user,'کڕیاری نموونە','07500000000','هەولێر');ops.supplier(user,'دابینکەری نموونە')
    print('Demo menu created. No fake sales or payments were inserted.')

if __name__=='__main__':main()
