from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QFormLayout,QLabel,QComboBox,
    QTextBrowser,QPushButton,QFileDialog)
from printing.receipts import receipt_html,print_preview,print_receipt,generate_pdf,printer_names


class ReceiptDialog(QDialog):
    def __init__(self,window,order_id):
        super().__init__(window);self.w,self.order_id=window,order_id
        self.setWindowTitle(window.t('Receipt'));self.resize(610,690)
        self.config=dict(window.config);layout=QVBoxLayout(self)
        heading=QLabel(window.t('Receipt'));heading.setObjectName('heading');layout.addWidget(heading)
        form=QFormLayout();self.printer=QComboBox();names=printer_names()
        for name in names:self.printer.addItem(name,name)
        if not names:self.printer.addItem(window.t('No printers installed'),'')
        self.printer.setCurrentIndex(max(self.printer.findData(self.config.get('printer_name','')),0))
        form.addRow(window.t('Receipt printer'),self.printer)
        self.width=QComboBox()
        for label,value in [('58 mm','58'),('80 mm','80'),('A4','A4')]:self.width.addItem(label,value)
        self.width.setCurrentIndex(max(self.width.findData(self.config.get('paper_width','80')),0))
        form.addRow(window.t('Paper width'),self.width);layout.addLayout(form)
        self.preview=QTextBrowser();self.preview.setStyleSheet('QTextBrowser { background:#fff; color:#000; padding:12px; border:1px solid #dce3ed; border-radius:8px; }')
        self.preview.setOpenExternalLinks(False);layout.addWidget(self.preview,1)
        self.hint=QLabel(window.t('Install a Windows printer to print. PDF export is still available.') if not names else '')
        self.hint.setObjectName('muted');self.hint.setWordWrap(True);layout.addWidget(self.hint)
        bar=QHBoxLayout();layout.addLayout(bar)
        for label,action in [('Print',self.print_now),('Print preview',self.print_preview),('Save PDF',self.pdf)]:
            b=QPushButton(window.t(label));b.clicked.connect(lambda _,fn=action:window.safe(fn));bar.addWidget(b)
            if label=='Print':b.setObjectName('primary');b.setEnabled(bool(names));self.print_button=b
        close=QPushButton(window.t('Cancel'));close.clicked.connect(self.reject);bar.addWidget(close)
        self.width.currentIndexChanged.connect(self.refresh);self.refresh()
    def refresh(self):
        self.config['paper_width']=self.width.currentData()
        self.preview.setHtml(receipt_html(self.w.db,self.order_id,self.config))
        width=350 if self.width.currentData()=='58' else (440 if self.width.currentData()=='80' else 560)
        self.preview.setMaximumWidth(width)
    def preferences(self):
        values={'printer_name':self.printer.currentData() or '', 'paper_width':self.width.currentData()}
        self.w.settings.save_preferences(self.w.user,values);self.w.config.update(values);self.config.update(values)
    def print_now(self):
        self.preferences()
        return print_receipt(self,receipt_html(self.w.db,self.order_id,self.config),self.width.currentData(),self.printer.currentData() or '')
    def print_preview(self):
        self.preferences()
        print_preview(self,receipt_html(self.w.db,self.order_id,self.config),self.width.currentData(),self.printer.currentData() or '')
    def pdf(self):
        path,_=QFileDialog.getSaveFileName(self,self.w.t('Save PDF'),f'gas-hunar-{self.order_id}.pdf','PDF (*.pdf)')
        if path:self.preferences();generate_pdf(self.w.db,self.order_id,self.config,path)
