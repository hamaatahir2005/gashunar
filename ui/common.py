from PySide6.QtCore import Qt, QObject, Signal, QRunnable, QThreadPool
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel,
    QTableWidget, QTableWidgetItem, QDialog, QFormLayout, QDialogButtonBox, QComboBox, QMessageBox)
from localization.strings import tr


class Form(QDialog):
    def __init__(self, parent, title, fields, language='ckb'):
        super().__init__(parent)
        self.setWindowTitle(tr(title,language))
        self.setMinimumWidth(420)
        self.fields = {}
        layout = QFormLayout(self)
        for key, label, value in fields:
            if isinstance(value, list):
                widget = QComboBox()
                for text, data in value:
                    widget.addItem(str(text), data)
            else:
                widget = QLineEdit(str(value))
                if 'password' in key:
                    widget.setEchoMode(QLineEdit.EchoMode.Password)
            self.fields[key] = widget
            layout.addRow(tr(label,language),widget)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def values(self):
        return {k:(w.currentData() if isinstance(w,QComboBox) else w.text()) for k,w in self.fields.items()}


class GridPage(QWidget):
    def __init__(self, window, title, columns, loader):
        super().__init__()
        self.window, self.loader, self.columns = window, loader, columns
        self.layout = QVBoxLayout(self)
        heading = QLabel(window.t(title))
        heading.setObjectName('heading')
        self.layout.addWidget(heading)
        self.toolbar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText(window.t('Search'))
        self.search.textChanged.connect(self.filter)
        self.toolbar.addWidget(self.search)
        self.layout.addLayout(self.toolbar)
        self.table = QTableWidget(0,len(columns))
        self.table.setHorizontalHeaderLabels([window.t(c) for c in columns])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.layout.addWidget(self.table)
        self.button('Refresh', self.reload)

    def button(self,label,callback):
        button = QPushButton(self.window.t(label))
        button.clicked.connect(lambda: self.window.safe(callback))
        self.toolbar.addWidget(button)
        return button

    def reload(self):
        rows = self.loader()
        self.table.setRowCount(len(rows))
        for row_index,row in enumerate(rows):
            for col,value in enumerate(row):
                self.table.setItem(row_index,col,QTableWidgetItem(str(value if value is not None else '')))
        self.table.resizeColumnsToContents()
        self.filter()

    def filter(self):
        query = self.search.text().casefold()
        for row in range(self.table.rowCount()):
            self.table.setRowHidden(row,not any(query in self.table.item(row,col).text().casefold() for col in range(self.table.columnCount()) if self.table.item(row,col)))

    def selected(self):
        row = self.table.currentRow()
        if row < 0:
            raise ValueError('Select a row first')
        return int(self.table.item(row,0).text())


class WorkerSignals(QObject):
    done = Signal(object)
    failed = Signal(str)


class Worker(QRunnable):
    def __init__(self, fn):
        super().__init__()
        self.fn, self.signals = fn, WorkerSignals()

    def run(self):
        try:
            self.signals.done.emit(self.fn())
        except Exception as exc:
            self.signals.failed.emit(str(exc))
