from datetime import date,timedelta,datetime
from decimal import Decimal
from pathlib import Path
import logging
from sqlalchemy import select,func
from PySide6.QtCore import Qt,QTimer,QEvent,QThreadPool
from PySide6.QtGui import QIcon,QPainter,QColor,QFont,QPixmap
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,
    QFrame,QPushButton,QLabel,QStackedWidget,QDialog,QMessageBox,QFileDialog,QComboBox,QLineEdit,
    QFormLayout,QScrollArea,QGroupBox,QStyle)
from core.paths import resource
from core.money import money,amount
from localization.strings import tr
from ui.common import Form,GridPage,Worker
from ui.theme import stylesheet
from ui.pos import POS
from ui.financial import FinancialOverview
from ui.products import ProductsPage
from ui.receipt import ReceiptDialog
from models.schema import *
from services.auth import Auth
from services.catalog import Catalog
from services.orders import Orders
from services.operations import Operations
from services.finance import Finance
from services.settings import Settings
from services.backup import Backup
from printing.receipts import receipt_html,generate_pdf,print_preview


class SalesChart(QWidget):
    def __init__(self,data):
        super().__init__();self.data=data;self.setMinimumHeight(180)
    def paintEvent(self,event):
        painter=QPainter(self);painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        maximum=max([max(v,0) for _,v in self.data]+[1]);width=max(self.width()-40,1)/max(len(self.data),1)
        for i,(day,value) in enumerate(self.data):
            height=int(max(value,0)/maximum*(self.height()-45));x=int(20+i*width)
            painter.setBrush(QColor('#d7b66f'));painter.setPen(Qt.PenStyle.NoPen);painter.drawRoundedRect(x,self.height()-30-height,int(width-8),height,3,3)
            painter.setPen(QColor('#8898af'));painter.drawText(x,self.height()-10,day[5:])


class Window(QMainWindow):
    def __init__(self,db,auth,user):
        super().__init__();self.db,self.auth,self.user=db,auth,user
        self.settings=Settings(db,auth);self.config=self.settings.for_user(user);self.language=self.config['language']
        self.catalog=Catalog(db,auth);self.orders=Orders(db,auth);self.ops=Operations(db,auth);self.finance=Finance(db,auth);self.backup=Backup(db,auth)
        self.workers=[];self.pages={};self.last_activity=datetime.now();self.locked=False;self.closing=False
        self.setWindowTitle('GAS HUNAR — گەس هونەر');self.setWindowIcon(QIcon(str(resource('assets/gas-hunar.ico'))));self.resize(1366,768);self.setMinimumSize(1100,680)
        app=QApplication.instance();app.setLayoutDirection(Qt.LayoutDirection.RightToLeft if self.language in ('ckb','ar') else Qt.LayoutDirection.LeftToRight);app.setStyleSheet(stylesheet(self.config['theme']));app.installEventFilter(self)
        root=QWidget();self.setCentralWidget(root);layout=QHBoxLayout(root);layout.setContentsMargins(0,0,0,0)
        sidebar=QFrame();sidebar.setObjectName('sidebar');sidebar.setFixedWidth(206);nav=QVBoxLayout(sidebar)
        brand=QLabel('GAS HUNAR\nگەس هونەر');brand.setObjectName('brand');nav.addWidget(brand)
        self.stack=QStackedWidget();nav_scroll=QScrollArea();nav_scroll.setWidgetResizable(True);nav_scroll.setWidget(sidebar);nav_scroll.setFixedWidth(224);layout.addWidget(nav_scroll)
        content=QWidget();content_layout=QVBoxLayout(content);content_layout.setContentsMargins(0,0,0,0);content_layout.setSpacing(0)
        topbar=QFrame();topbar.setObjectName('topbar');top=QHBoxLayout(topbar);top.setContentsMargins(22,12,22,12)
        self.page_heading=QLabel(self.t('Workspace'));self.page_heading.setObjectName('eyebrow');top.addWidget(self.page_heading);top.addStretch()
        offline=QLabel('● '+self.t('Offline'));offline.setObjectName('offline');top.addWidget(offline)
        top.addWidget(QLabel(self.t('Appearance')));self.theme_picker=QComboBox();self.theme_picker.setMinimumWidth(120)
        self.theme_picker.addItem(self.t('Dark'),'dark');self.theme_picker.addItem(self.t('Light'),'light');self.theme_picker.setCurrentIndex(max(self.theme_picker.findData(self.config['theme']),0))
        self.theme_picker.currentIndexChanged.connect(lambda:self.safe(lambda:self.set_theme(self.theme_picker.currentData())));top.addWidget(self.theme_picker)
        content_layout.addWidget(topbar);content_layout.addWidget(self.stack,1);layout.addWidget(content,1)
        actions=auth.actions(user)
        entries=[('Dashboard','reports',self.dashboard),('Point of sale','pos',lambda:POS(self)),('Orders','pos',self.order_page),('Products','products',self.product_page),('Tables','tables',self.table_page),('Kitchen','kitchen',self.kitchen_page),('Inventory','inventory',self.inventory_page),('Purchases','inventory',self.purchase_page),('Expenses','expenses',self.expense_page),('Customers','customers',self.customer_page),('Employees','employees',self.employee_page),('Reports','reports',self.report_page),('Settings','settings',self.settings_page),('Backups','backup',self.backup_page)]
        self.factories={};self.nav_buttons={}
        nav_icons={'Dashboard':'SP_ComputerIcon','Point of sale':'SP_DialogApplyButton','Orders':'SP_FileDialogDetailedView','Products':'SP_DirIcon','Tables':'SP_FileDialogContentsView','Kitchen':'SP_DialogYesButton','Inventory':'SP_DriveHDIcon','Purchases':'SP_DialogOpenButton','Expenses':'SP_FileIcon','Customers':'SP_DirHomeIcon','Employees':'SP_FileDialogInfoView','Reports':'SP_FileDialogListView','Settings':'SP_FileDialogDetailedView','Backups':'SP_DialogSaveButton'}
        for title,permission,factory in entries:
            if '*' not in actions and permission not in actions:continue
            self.factories[title]=factory
            b=QPushButton(self.t(title));b.setObjectName('nav');b.setCheckable(True);self.nav_buttons[title]=b;b.setIcon(self.style().standardIcon(getattr(QStyle.StandardPixmap,nav_icons[title],QStyle.StandardPixmap.SP_FileIcon)));b.clicked.connect(lambda _,name=title:self.safe(lambda:self.navigate(name)));nav.addWidget(b)
        nav.addStretch()
        for label,fn in [('Open drawer',self.open_drawer),('Close drawer',self.close_drawer),('Change password',self.change_password),('Logout',self.logout)]:
            if label in ('Open drawer','Close drawer') and '*' not in actions and 'pos' not in actions:continue
            b=QPushButton(self.t(label));b.clicked.connect(lambda _,f=fn:self.safe(f));nav.addWidget(b)
        self.statusBar().showMessage('OFFLINE • SQLite • IQD')
        self.navigate(next(iter(self.factories)))
        self.timer=QTimer(self);self.timer.timeout.connect(self.tick);self.timer.start(5000)
        self.backup_timer=QTimer(self);self.backup_timer.timeout.connect(self.auto_backup);self.backup_timer.start(int(self.config['backup_minutes'])*60000)

    def t(self,key):return tr(key,self.language)
    def safe(self,fn):
        try:return fn()
        except (ValueError,PermissionError) as exc:self.message('Error',str(exc),True)
        except Exception as exc:
            logging.exception('Operation failed');self.message('Error','Operation failed. No partial transaction was saved.\n'+str(exc),True)
    def message(self,title,text,error=False):
        (QMessageBox.warning if error else QMessageBox.information)(self,self.t(title),text)
    def form(self,title,fields):
        dialog=Form(self,title,fields,self.language)
        return dialog.values() if dialog.exec()==QDialog.DialogCode.Accepted else None
    def confirm(self,text):
        return QMessageBox.question(self,'GAS HUNAR',text,QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)==QMessageBox.StandardButton.Yes
    def rows(self,model,columns,where=None):
        with self.db.read() as s:
            query=select(model).order_by(model.id.desc()).limit(500)
            if where is not None:query=query.where(where)
            return [tuple(getattr(obj,c) for c in columns) for obj in s.scalars(query)]
    def choices(self,model):
        with self.db.read() as s:return [(obj.name,obj.id) for obj in s.scalars(select(model).order_by(model.id).limit(2000))]
    def page(self,title,columns,loader):return GridPage(self,title,columns,loader)
    def navigate(self,title):
        if title not in self.pages:
            page=self.factories[title]();self.pages[title]=page;self.stack.addWidget(page)
        page=self.pages[title]
        if hasattr(page,'reload'):page.reload()
        self.stack.setCurrentWidget(page)
        self.page_heading.setText(self.t('Workspace')+' / '+self.t(title))
        for name,button in self.nav_buttons.items():button.setChecked(name==title)
    def refresh(self,page):page.reload()
    def background(self,fn,callback):
        worker=Worker(fn);self.workers.append(worker)
        worker.signals.done.connect(callback);worker.signals.failed.connect(lambda msg:self.message('Error',msg,True))
        worker.signals.done.connect(lambda _:self.workers.remove(worker) if worker in self.workers else None)
        worker.signals.failed.connect(lambda _:self.workers.remove(worker) if worker in self.workers else None)
        QThreadPool.globalInstance().start(worker)

    def set_theme(self,theme):
        self.settings.save_preferences(self.user,{'theme':theme})
        self.config['theme']=theme
        self.theme_picker.blockSignals(True);self.theme_picker.setCurrentIndex(self.theme_picker.findData(theme));self.theme_picker.blockSignals(False)
        QApplication.instance().setStyleSheet(stylesheet(theme))
        for page in self.pages.values():page.update()

    def dashboard(self):
        return FinancialOverview(self)

    def product_page(self):
        return ProductsPage(self)

    def order_page(self):
        def load():
            with self.db.read() as s:
                result=[]
                for o in s.scalars(select(Order).order_by(Order.id.desc()).limit(500)):
                    paid=s.scalar(select(func.coalesce(func.sum(Payment.amount),0)).where(Payment.order_id==o.id))
                    result.append((o.id,o.created_at[:19],o.kind,o.status,money(o.total),money(paid),o.kitchen_status,o.table_id))
                return result
        page=self.page('Orders',['ID','Date','Order type','Status','Total','Payment','Kitchen','Table'],load)
        def resume():
            oid=page.selected();self.navigate('Point of sale');self.pages['Point of sale'].resume(oid)
        page.button('Resume',resume);page.button('Receipt',lambda:self.receipt(page.selected()))
        page.button('Confirm',lambda:(self.orders.confirm(self.user,page.selected()),page.reload()))
        page.button('Cancel',lambda:(self.orders.cancel_held(self.user,page.selected()),page.reload()) if self.confirm('Cancel held order?') else None)
        if '*' in self.auth.actions(self.user) or 'refunds' in self.auth.actions(self.user):
            def refund():
                oid=page.selected();v=self.form('Refund',[('reason','Description',''),('method','Method',[('Cash','cash'),('Card','card')]),('restock','Return ingredients to stock',[('No',False),('Yes',True)])])
                if v and self.confirm('Reverse the entire sale and refund all payments?'):
                    self.orders.refund(self.user,oid,v['reason'],v['method'],v['restock']);page.reload()
            page.button('Refund',refund)
        return page

    def receipt(self,order_id):
        self.auth.require(self.user,'pos')
        ReceiptDialog(self,order_id).exec()

    def table_page(self):
        def loader():
            with self.db.read() as s:
                result=[]
                for t in s.scalars(select(RestaurantTable)):
                    order=s.scalar(select(Order).where(Order.table_id==t.id,Order.status.in_(['held','confirmed'])))
                    reserved=s.scalar(select(Reservation).where(Reservation.table_id==t.id,Reservation.status=='reserved',Reservation.starts_at<=now(),Reservation.ends_at>now()))
                    status='Occupied' if order else ('Reserved' if reserved else 'Available')
                    result.append((t.id,t.name,t.section,t.capacity,self.t(status),order.id if order else ''))
                return result
        page=self.page('Tables',['ID','Name','Section','Capacity','Status','Orders'],loader)
        def add():
            v=self.form('Add',[('name','Name',''),('capacity','Capacity','4'),('section','Section','Main')])
            if v:self.ops.table(self.user,**v);page.reload()
        def transfer():
            v=self.form('Tables',[('order_id','Orders',''),('table_id','Table',self.choices(RestaurantTable))])
            if v:self.orders.transfer(self.user,int(v['order_id']),v['table_id']);page.reload()
        def reserve():
            v=self.form('Reserved',[('table_id','Table',self.choices(RestaurantTable)),('customer_id','Customer',self.choices(Customer)),('starts_at','Start ISO time',datetime.now().astimezone().isoformat()),('ends_at','End ISO time',(datetime.now().astimezone()+timedelta(hours=1)).isoformat()),('guests','Capacity','2')])
            if v:v['guests']=int(v['guests']);self.ops.reserve(self.user,**v);page.reload()
        page.button('Add',add);page.button('Transfer',transfer);page.button('Reserved',reserve);return page

    def kitchen_page(self):
        def loader():
            with self.db.read() as s:
                rows=[]
                for o in s.scalars(select(Order).where(Order.confirmed_at.is_not(None),Order.status!='refunded',Order.kitchen_status!='completed').order_by(Order.priority.desc(),Order.confirmed_at)):
                    items=list(s.scalars(select(OrderItem).where(OrderItem.order_id==o.id)))
                    text=' | '.join(f'{i.quantity}× {i.name} {i.notes}' for i in items)
                    rows.append((o.id,o.table_id or o.kind,self.t(o.kitchen_status.title()),o.confirmed_at[:19],text,o.notes))
                return rows
        page=self.page('Kitchen',['ID','Table','Status','Date','Products','Notes'],loader)
        def advance():
            oid=page.selected()
            with self.db.read() as s:status=s.get(Order,oid).kitchen_status
            self.orders.kitchen(self.user,oid,{'new':'preparing','preparing':'ready','ready':'completed'}[status]);page.reload()
        page.button('Next status',advance);return page

    def inventory_page(self):
        def loader():
            self.auth.require(self.user,'inventory')
            with self.db.read() as s:return [(i.id,i.name,i.unit,amount(i.quantity),money(i.cost),amount(i.minimum),self.t('Low stock') if i.quantity<=i.minimum else '') for i in s.scalars(select(Ingredient))]
        page=self.page('Inventory',['ID','Name','Unit','Quantity','Cost','Minimum','Status'],loader)
        def add():
            v=self.form('Add ingredient',[('name','Name',''),('unit','Unit','g'),('cost','Cost','0'),('minimum','Minimum','0')])
            if v:self.ops.ingredient(self.user,**v);page.reload()
        def adjust():
            iid=page.selected();v=self.form('Adjust stock',[('quantity','Quantity','0'),('reason','Description','')])
            if v:self.ops.adjust_stock(self.user,iid,**v);page.reload()
        def recipe():
            v=self.form('Recipe',[('product_id','Products',self.choices(Product)),('ingredient_id','Inventory',self.choices(Ingredient)),('quantity','Quantity','1')])
            if v:self.ops.recipe(self.user,**v)
        page.button('Add ingredient',add);page.button('Adjust stock',adjust);page.button('Recipe',recipe);return page

    def purchase_page(self):
        page=self.page('Purchases',['ID','Supplier','Total','Payment','Date'],lambda:[(i,s,money(t),money(p),d[:19]) for i,s,t,p,d in self.rows(Purchase,['id','supplier_id','total','paid','created_at'])])
        def supplier():
            v=self.form('Add supplier',[('name','Name',''),('phone','Phone','')])
            if v:self.ops.supplier(self.user,**v)
        def purchase():
            v=self.form('Purchase',[('supplier_id','Supplier',self.choices(Supplier)),('ingredient_id','Inventory',self.choices(Ingredient)),('quantity','Quantity','1'),('unit_cost','Cost','0'),('paid','Payment','0')])
            if v:self.ops.purchase(self.user,v['supplier_id'],[(v['ingredient_id'],v['quantity'],v['unit_cost'])],paid=v['paid']);page.reload()
        page.button('Add supplier',supplier);page.button('Purchase',purchase);return page

    def expense_page(self):
        page=self.page('Expenses',['ID','Category','Amount','Description','Date','Method'],lambda:[(i,c,money(a),d,dt,m) for i,c,a,d,dt,m in self.rows(Expense,['id','category_id','amount','description','date','method'])])
        def edit(existing=False):
            obj=None
            if existing:
                with self.db.read() as s:obj=s.get(Expense,page.selected())
            v=self.form('Expenses',[('category_id','Category',self.choices(ExpenseCategory)),('amount','Amount',amount(obj.amount) if obj else '0'),('description','Description',obj.description if obj else ''),('date','Date',obj.date if obj else date.today().isoformat()),('method','Method',[('Cash','cash'),('Card','card')])])
            if v:self.ops.expense(self.user,**v,expense_id=obj.id if obj else None);page.reload()
        page.button('Add',lambda:edit());page.button('Edit',lambda:edit(True));return page

    def customer_page(self):
        page=self.page('Customers',['ID','Name','Phone','Address','Notes'],lambda:self.rows(Customer,['id','name','phone','address','notes']))
        def edit(existing=False):
            obj=None
            if existing:
                with self.db.read() as s:obj=s.get(Customer,page.selected())
            v=self.form('Customers',[(k,k.title(),getattr(obj,k) if obj else '') for k in ['name','phone','address','notes']])
            if v:self.ops.customer(self.user,**v,customer_id=obj.id if obj else None);page.reload()
        page.button('Add',lambda:edit());page.button('Edit',lambda:edit(True));return page

    def employee_page(self):
        page=self.page('Employees',['ID','Name','Phone','Salary','User'],lambda:[(i,n,p,money(s),u) for i,n,p,s,u in self.rows(Employee,['id','name','phone','salary','user_id'])])
        def create():
            v=self.form('Add',[('username','Username',''),('password','Password',''),('role_name','Role',[(n,n) for n in ['manager','cashier','waiter','kitchen']])])
            if v:self.auth.create_user(self.user,**v);page.reload()
        page.button('Add',create);page.button('Attendance',lambda:self.ops.attendance(self.user,page.selected()));return page

    def report_page(self):
        return FinancialOverview(self,reports=True)

    def settings_page(self):
        scroll=QScrollArea();scroll.setWidgetResizable(True);w=QWidget();scroll.setWidget(w);layout=QFormLayout(w);fields={}
        choices={'language':[('کوردی','ckb'),('العربية','ar'),('English','en')],'theme':[(self.t('Dark'),'dark'),(self.t('Light'),'light')],'paper_width':[('58 mm','58'),('80 mm','80'),('A4','A4')],'prevent_negative_stock':[('Yes','true'),('No','false')]}
        for key,value in self.settings.all().items():
            if key in choices:
                widget=QComboBox()
                for label,data in choices[key]:widget.addItem(label,data)
                widget.setCurrentIndex(max(widget.findData(value),0))
            else:widget=QLineEdit(value)
            fields[key]=widget;layout.addRow(self.t(key.replace('_',' ').title()),widget)
        button=QPushButton(self.t('Save'));layout.addRow(button)
        def save():
            values={k:(w.currentData() if isinstance(w,QComboBox) else w.text()) for k,w in fields.items()};self.settings.save(self.user,values);self.config=self.settings.for_user(self.user);self.set_theme(values['theme']);self.backup_timer.setInterval(int(self.config['backup_minutes'])*60000);self.message('Success',self.t('Settings saved')+' • Restart to apply language changes.')
        button.clicked.connect(lambda:self.safe(save));return scroll

    def backup_page(self):
        page=self.page('Backups',['ID','Path','SHA-256','Date'],lambda:self.rows(BackupHistory,['id','path','sha256','created_at']))
        def create():
            folder=QFileDialog.getExistingDirectory(self,'Backup folder / USB')
            if folder:self.background(lambda:self.backup.create(self.user,folder),lambda p:(self.message('Success',str(p)),page.reload()))
        def restore():
            path,_=QFileDialog.getOpenFileName(self,'Restore','','SQLite (*.sqlite3)')
            if path and self.confirm('Replace the database at next startup? Current database will be backed up. Exit and restart after staging the restore.'):
                self.background(lambda:self.backup.stage_restore(self.user,path),lambda _:self.message('Success','Restore staged. Close and restart GAS HUNAR.'))
        page.button('Create backup',create);page.button('Restore backup',restore);return page

    def open_drawer(self):
        v=self.form('Open drawer',[('opening','Amount','0')])
        if v:self.orders.open_drawer(self.user,v['opening']);self.message('Success',self.t('Open drawer'))
    def close_drawer(self):
        v=self.form('Close drawer',[('counted','Amount','0')])
        if v and self.confirm('Close drawer with this counted amount?'):self.message('Success','Variance: '+money(self.orders.close_drawer(self.user,v['counted'])))
    def change_password(self):
        v=self.form('Change password',[('old_password','Current password',''),('new_password','New password','')])
        if v:self.auth.change_password(self.user,v['old_password'],v['new_password']);self.message('Success',self.t('Change password'))
    def logout(self):
        from ui.login import Login
        dialog=Login(self.auth,self.language,self)
        self.locked=True
        if dialog.exec()==QDialog.DialogCode.Accepted:
            self.locked=False;self.last_activity=datetime.now()
            if dialog.user!=self.user:
                self.message('Login','Restart the application to switch users safely.');self.close()
        else:self.close()
    def eventFilter(self,obj,event):
        if event.type() in (QEvent.Type.MouseButtonPress,QEvent.Type.KeyPress):self.last_activity=datetime.now()
        return super().eventFilter(obj,event)
    def tick(self):
        if self.locked or self.closing:return
        if (datetime.now()-self.last_activity).total_seconds()>int(self.config['lock_minutes'])*60:self.logout();return
        page=self.stack.currentWidget()
        if page in [self.pages.get('Dashboard'),self.pages.get('Kitchen'),self.pages.get('Tables')]:self.safe(page.reload)
    def auto_backup(self):
        if self.workers or self.closing:return
        self.background(lambda:self.backup.create(self.user,self.config.get('backup_location') or None,int(self.config['backup_retention']),automatic=True),lambda _:self.statusBar().showMessage('OFFLINE • Automatic backup verified'))
    def closeEvent(self,event):
        if self.workers:
            self.message('Backups','An operation is running. Please wait for it to finish.');event.ignore();return
        self.closing=True;self.timer.stop();self.backup_timer.stop()
        try:self.backup.create(self.user,self.config.get('backup_location') or None,int(self.config['backup_retention']),automatic=True)
        except Exception as exc:
            logging.exception('Exit backup failed')
            if not self.confirm('Exit backup failed: '+str(exc)+'\nExit anyway?'):self.closing=False;self.timer.start();self.backup_timer.start();event.ignore();return
        QApplication.instance().removeEventFilter(self);event.accept()
