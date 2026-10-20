import pytest
from database.engine import Database
from services.auth import Auth
from services.catalog import Catalog
from services.orders import Orders
from services.operations import Operations
from services.finance import Finance
from services.settings import Settings
from services.backup import Backup


@pytest.fixture
def system(tmp_path):
    db=Database(tmp_path/'test.sqlite3');auth=Auth(db);admin=auth.setup('admin','a-secure-test-passphrase')
    result={'db':db,'auth':auth,'admin':admin,'catalog':Catalog(db,auth),'orders':Orders(db,auth),'ops':Operations(db,auth),'finance':Finance(db,auth),'settings':Settings(db,auth),'backup':Backup(db,auth)}
    yield result
    db.engine.dispose()


@pytest.fixture
def menu(system):
    x=system;a=x['admin']
    p=x['catalog'].save(a,'کەباب','KEB','10000','3000','Grill',barcode='123456789')
    i=x['ops'].ingredient(a,'Meat','g','10','100')
    x['ops'].adjust_stock(a,i,'1000','opening')
    x['ops'].recipe(a,p,i,'200')
    x['orders'].open_drawer(a,'50000')
    return p,i
