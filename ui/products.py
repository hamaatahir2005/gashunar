from pathlib import Path
from PIL import Image
from sqlalchemy import select
from PySide6.QtCore import Qt,QSize
from PySide6.QtGui import QPixmap,QIcon
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QFormLayout,QLabel,QLineEdit,QTextEdit,
    QComboBox,QPushButton,QDialogButtonBox,QFileDialog,QFrame)
from core.money import amount,money
from models.schema import Product,Category
from ui.common import GridPage


class ProductDialog(QDialog):
    def __init__(self,window,product_id=None):
        super().__init__(window);self.w,self.product_id,self.image_path=window,product_id,None
        self.setWindowTitle(window.t('Edit product' if product_id else 'Add product'));self.setMinimumWidth(720)
        self.setObjectName('productDialog');layout=QVBoxLayout(self)
        heading=QLabel(window.t('Edit product' if product_id else 'Add product'));heading.setObjectName('heading');layout.addWidget(heading)
        content=QHBoxLayout();layout.addLayout(content)
        image_box=QFrame();image_box.setObjectName('card');image_layout=QVBoxLayout(image_box)
        self.preview=QLabel(window.t('Product photo'));self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter);self.preview.setFixedSize(220,190);self.preview.setWordWrap(True);image_layout.addWidget(self.preview)
        upload=QPushButton(window.t('Upload image'));upload.clicked.connect(self.choose_image);image_layout.addWidget(upload)
        hint=QLabel(window.t('Local PNG / JPEG / WebP · up to 15 MB'));hint.setObjectName('muted');hint.setWordWrap(True);image_layout.addWidget(hint);image_layout.addStretch();content.addWidget(image_box)
        form=QFormLayout();content.addLayout(form,1);self.fields={}
        product=None
        with window.db.read() as s:
            product=s.get(Product,product_id) if product_id else None
            if product_id and not product:raise ValueError('Product not found')
            category=s.get(Category,product.category_id).name if product and product.category_id else ''
            categories=[c.name for c in s.scalars(select(Category).order_by(Category.name))]
        for key,label,initial in [('name','Name',product.name if product else ''),('code','Code',product.code if product else ''),('price','Price',str(amount(product.price)) if product else ''),('cost','Cost',str(amount(product.cost)) if product else '0'),('barcode','Barcode',product.barcode or '' if product else '')]:
            edit=QLineEdit(initial);edit.setObjectName('product_'+key);self.fields[key]=edit;form.addRow(window.t(label),edit)
        self.category=QComboBox();self.category.setEditable(True);self.category.addItem('');self.category.addItems(categories);self.category.setCurrentText(category);form.addRow(window.t('Category'),self.category)
        self.description=QTextEdit(product.description if product else '');self.description.setMaximumHeight(90);form.addRow(window.t('Description'),self.description)
        self.error=QLabel();self.error.setObjectName('error');self.error.setWordWrap(True);layout.addWidget(self.error)
        buttons=QDialogButtonBox();save=buttons.addButton(window.t('Save product'),QDialogButtonBox.ButtonRole.AcceptRole);save.setObjectName('primary');buttons.addButton(window.t('Cancel'),QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.save);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
        if product:
            images=window.catalog.images(window.user,[product.id])
            if product.id in images:self.show_image(images[product.id])
    def show_image(self,path):
        path=Path(path)
        if not path.is_file() or path.stat().st_size>15*1024*1024:raise ValueError('Choose an image smaller than 15 MB')
        with Image.open(path) as image:
            if image.width*image.height>30_000_000:raise ValueError('Image resolution too large')
        pixmap=QPixmap(str(path))
        if pixmap.isNull():raise ValueError('Cannot load this image')
        self.preview.setPixmap(pixmap.scaled(212,180,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
    def choose_image(self):
        path,_=QFileDialog.getOpenFileName(self,self.w.t('Upload image'),'','Images (*.png *.jpg *.jpeg *.webp)')
        if not path:return
        self.set_image(path)
    def set_image(self,path):
        try:self.show_image(path);self.image_path=str(path);self.error.clear()
        except Exception as exc:self.error.setText(str(exc))
    def save(self):
        try:
            values={key:edit.text() for key,edit in self.fields.items()}
            values.update(category=self.category.currentText(),description=self.description.toPlainText(),product_id=self.product_id,image_path=self.image_path)
            self.product_id=self.w.catalog.save(self.w.user,**values)
            self.accept()
        except Exception as exc:self.error.setText(str(exc))


class ProductsPage(GridPage):
    def __init__(self,window):
        self.images={}
        super().__init__(window,'Products',['ID','Image','Name','Code','Price','Cost','Barcode','Status'],self.load)
        self.table.setIconSize(QSize(56,48));self.table.verticalHeader().setDefaultSectionSize(64)
        self.button('Add product',self.add).setObjectName('primary');self.button('Edit',self.edit)
        self.button('Upload image',self.upload);self.button('Archive',self.archive)
        self.button('Export CSV',self.export_csv);self.button('Import CSV',self.import_csv)
        self.table.itemDoubleClicked.connect(lambda _:window.safe(self.edit))
    def load(self):
        products=self.window.catalog.list(self.window.user,limit=500,archived=True)
        self.images=self.window.catalog.images(self.window.user,[p.id for p in products])
        return [(p.id,'',p.name,p.code,money(p.price),money(p.cost),p.barcode or '',self.window.t('Available' if p.active else 'Archived')) for p in products]
    def reload(self):
        super().reload()
        for row in range(self.table.rowCount()):
            path=self.images.get(int(self.table.item(row,0).text()))
            if path:self.table.item(row,1).setIcon(QIcon(str(path)))
        self.table.setColumnWidth(1,76)
    def dialog(self,product_id=None):
        dialog=ProductDialog(self.window,product_id)
        if dialog.exec()==QDialog.DialogCode.Accepted:self.reload()
    def add(self):self.dialog()
    def edit(self):self.dialog(self.selected())
    def upload(self):
        product_id=self.selected();path,_=QFileDialog.getOpenFileName(self,self.window.t('Upload image'),'','Images (*.png *.jpg *.jpeg *.webp)')
        if path:self.window.catalog.image(self.window.user,product_id,path);self.reload()
    def archive(self):
        product_id=self.selected()
        if self.window.confirm(self.window.t('Archive selected product?')):self.window.catalog.archive(self.window.user,product_id);self.reload()
    def export_csv(self):
        path,_=QFileDialog.getSaveFileName(self.window,'CSV','products.csv','CSV (*.csv)')
        if path:self.window.catalog.export_csv(self.window.user,path)
    def import_csv(self):
        path,_=QFileDialog.getOpenFileName(self.window,'CSV','','CSV (*.csv)')
        if path:self.window.catalog.import_csv(self.window.user,path);self.reload()
