"""Headless structural GUI smoke test; physical printers and Windows require manual validation."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from ui.window import Window


def test_all_native_screens_construct(system):
    app=QApplication.instance() or QApplication([])
    x=system;w=Window(x['db'],x['auth'],x['admin']);w.show();app.processEvents()
    for title in w.factories:
        w.navigate(title);app.processEvents()
        assert w.stack.currentWidget() is w.pages[title]
    assert w.language=='ckb'
    w.close();app.processEvents()
