from uuid import uuid4
from sqlalchemy import select, func
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (QWidget,QHBoxLayout,QVBoxLayout,QGridLayout,QScrollArea,QPushButton,
    QLineEdit,QComboBox,QTableWidget,QTableWidgetItem,QLabel,QSpinBox,QHeaderView)
from models.schema import Product, ProductImage, Category, RestaurantTable, Customer, Order, OrderItem, Payment
from core.money import amount, money
from ui.common import Form


class POS(QWidget):
    def __init__(self, window):
        super().__init__()
        self.w, self.cart, self.order_id = window, [], None
        self.token = uuid4().hex
        layout=QHBoxLayout(self)
        left=QVBoxLayout(); right=QVBoxLayout()
        layout.addLayout(left,3); layout.addLayout(right,2)
        title=QLabel(window.t('Point of sale')); title.setObjectName('heading'); left.addWidget(title)
        bar=QHBoxLayout(); self.search=QLineEdit(); self.search.setPlaceholderText(window.t('Search')+' / Barcode (F2)')
        self.search.textChanged.connect(self.reload_products); self.search.returnPressed.connect(self.barcode)
        self.category=QComboBox(); self.category.addItem('—',None)
        with window.db.read() as s:
            for c in s.scalars(select(Category).order_by(Category.sort,Category.name)):
                self.category.addItem(c.name,c.id)
        self.category.currentIndexChanged.connect(self.reload_products)
        bar.addWidget(self.search);bar.addWidget(self.category);left.addLayout(bar)
        scroll=QScrollArea();scroll.setWidgetResizable(True);self.products=QWidget();self.grid=QGridLayout(self.products);self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.products);left.addWidget(scroll)
        self.kind=QComboBox()
        for text in ('takeaway','dine-in','delivery'): self.kind.addItem(text,text)
        self.table=QComboBox();self.customer=QComboBox()
        self.table.addItem(window.t('Table')+' —',None);self.customer.addItem(window.t('Customer')+' —',None)
        with window.db.read() as s:
            for t in s.scalars(select(RestaurantTable)):self.table.addItem(t.name,t.id)
            for c in s.scalars(select(Customer)):self.customer.addItem(c.name,c.id)
        right.addWidget(self.kind);right.addWidget(self.table);right.addWidget(self.customer)
        self.cart_table=QTableWidget(0,3);self.cart_table.setHorizontalHeaderLabels([window.t(x) for x in ['Name','Quantity','Total']])
        self.cart_table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
        self.cart_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);right.addWidget(self.cart_table)
        self.notes=QLineEdit();self.notes.setPlaceholderText(window.t('Notes'));right.addWidget(self.notes)
        discountrow=QHBoxLayout();self.discount=QLineEdit('0');self.discount.setPlaceholderText(window.t('Discount'));self.discount_type=QComboBox();self.discount_type.addItems(['IQD','%'])
        discountrow.addWidget(QLabel(window.t('Discount')));discountrow.addWidget(self.discount);discountrow.addWidget(self.discount_type);right.addLayout(discountrow)
        self.total=QLabel(money(0));self.total.setObjectName('metric');right.addWidget(self.total)
        actions=QGridLayout();right.addLayout(actions)
        for index,(name,fn) in enumerate([('Remove',self.remove),('Notes',self.item_notes),('Hold order',self.hold),('Pay',self.pay),('Cancel',self.clear),('Full screen',self.fullscreen)]):
            b=QPushButton(window.t(name));b.clicked.connect(lambda _,f=fn:window.safe(f));actions.addWidget(b,index//2,index%2)
            if name=='Pay':b.setObjectName('primary')
        QShortcut(QKeySequence('F2'),self,activated=self.search.setFocus)
        QShortcut(QKeySequence('F8'),self,activated=lambda:window.safe(self.hold))
        QShortcut(QKeySequence('F9'),self,activated=lambda:window.safe(self.pay))
        self.reload_products()

    def reload_products(self):
        while self.grid.count():
            item=self.grid.takeAt(0)
            if item.widget():item.widget().deleteLater()
        products=self.w.catalog.list(self.w.user,self.search.text(),self.category.currentData(),limit=150)
        with self.w.db.read() as s:
            for index,p in enumerate(products):
                b=QPushButton(f'{p.name}\n{money(p.price)}');b.setMinimumSize(140,100)
                image=s.scalar(select(ProductImage).where(ProductImage.product_id==p.id).order_by(ProductImage.id.desc()))
                if image:
                    from PySide6.QtCore import QSize
                    b.setIcon(QIcon(str(self.w.db.path.parent/image.path)));b.setIconSize(QSize(64,54))
                b.clicked.connect(lambda _,product=p:self.w.safe(lambda:self.add(product)));self.grid.addWidget(b,index//3,index%3)

    def barcode(self):
        matches=self.w.catalog.list(self.w.user,self.search.text())
        exact=[p for p in matches if p.barcode==self.search.text() or p.code==self.search.text()]
        if len(exact)==1:self.add(exact[0]);self.search.clear()

    def add(self,p):
        if self.order_id:
            with self.w.db.read() as s:
                if s.get(Order,self.order_id).status!='held':raise ValueError('Confirmed orders cannot be edited')
        for line in self.cart:
            if line['product_id']==p.id:line['quantity']+=1;break
        else:self.cart.append({'product_id':p.id,'quantity':1,'notes':'','name':p.name,'price':p.price})
        self.render()

    def render(self):
        self.cart_table.setRowCount(len(self.cart))
        for i,line in enumerate(self.cart):
            self.cart_table.setItem(i,0,QTableWidgetItem(line['name']+ (' • '+line['notes'] if line['notes'] else '')))
            quantity=QSpinBox();quantity.setRange(1,10000);quantity.setValue(line['quantity']);quantity.valueChanged.connect(lambda v,row=i:self.change_qty(row,v));self.cart_table.setCellWidget(i,1,quantity)
            self.cart_table.setItem(i,2,QTableWidgetItem(money(line['price']*line['quantity'])))
        self.total.setText(money(sum(l['price']*l['quantity'] for l in self.cart))+' • '+self.w.t('Tax')+'/'+self.w.t('Discount')+' → '+self.w.t('Pay'))

    def change_qty(self,row,value):self.cart[row]['quantity']=value;self.cart_table.item(row,2).setText(money(self.cart[row]['price']*value));self.total.setText(money(sum(l['price']*l['quantity'] for l in self.cart)))

    def remove(self):
        row=self.cart_table.currentRow()
        if row>=0:self.cart.pop(row);self.render()

    def item_notes(self):
        row=self.cart_table.currentRow()
        if row<0:raise ValueError('Select an item')
        values=self.w.form('Notes',[('notes','Notes',self.cart[row]['notes'])])
        if values:self.cart[row]['notes']=values['notes'];self.render()

    def hold(self):
        if not self.cart:raise ValueError('Empty cart')
        self.order_id=self.w.orders.hold(self.w.user,self.cart,kind=self.kind.currentData(),table_id=self.table.currentData(),customer_id=self.customer.currentData(),notes=self.notes.text(),token=self.token,discount=self.discount.text(),percent=self.discount_type.currentText()=='%',order_id=self.order_id)
        return self.order_id

    def pay(self):
        if not self.cart:raise ValueError('Empty cart')
        if self.order_id:
            with self.w.db.read() as s:held=s.get(Order,self.order_id).status=='held'
        else:held=True
        if held:self.hold()
        with self.w.db.read() as s:
            order=s.get(Order,self.order_id)
            paid=s.scalar(select(func.coalesce(func.sum(Payment.amount),0)).where(Payment.order_id==order.id))
            balance=order.total-paid
        values=self.w.form('Payment',[('cash','Cash','0'),('card','Card',str(amount(balance)))])
        if not values:return
        from core.money import units
        payments=[(k,v) for k,v in values.items() if units(v)>0]
        self.w.orders.pay(self.w.user,self.order_id,payments,uuid4().hex)
        self.w.message('Success',money(sum(units(v) for _,v in payments)))
        with self.w.db.read() as s:done=s.get(Order,self.order_id).status=='completed'
        if done:
            self.w.receipt(self.order_id)
            self.clear()

    def resume(self,order_id):
        with self.w.db.read() as s:
            order=s.get(Order,order_id)
            if not order or order.status not in ('held','confirmed'):raise ValueError('Order is not open')
            self.cart=[dict(product_id=i.product_id,quantity=i.quantity,notes=i.notes,name=i.name,price=i.price) for i in s.scalars(select(OrderItem).where(OrderItem.order_id==order_id))]
            self.order_id,self.token=order.id,order.token
            self.kind.setCurrentIndex(self.kind.findData(order.kind));self.table.setCurrentIndex(max(self.table.findData(order.table_id),0));self.customer.setCurrentIndex(max(self.customer.findData(order.customer_id),0))
            self.discount.setText(str(amount(order.discount)));self.discount_type.setCurrentIndex(0);self.notes.setText(order.notes)
        self.render()

    def clear(self):
        self.cart=[];self.order_id=None;self.token=uuid4().hex;self.discount.setText('0');self.notes.clear();self.render()

    def fullscreen(self):
        self.w.showNormal() if self.w.isFullScreen() else self.w.showFullScreen()
