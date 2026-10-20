"""Headless structural GUI smoke test; physical printers and Windows require manual validation."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication, QMessageBox
from ui.window import Window


def test_all_native_screens_construct(system, monkeypatch):
    prompts=[]
    def reject_unexpected_dialog(*args,**kwargs):
        prompts.append(args[2] if len(args)>2 else str(args))
        return QMessageBox.StandardButton.No
    monkeypatch.setattr(QMessageBox,"question",reject_unexpected_dialog)
    app=QApplication.instance() or QApplication([])
    x=system;w=Window(x['db'],x['auth'],x['admin']);w.show();app.processEvents()
    for title in w.factories:
        w.navigate(title);app.processEvents()
        assert w.stack.currentWidget() is w.pages[title]
    assert w.language=='ckb'
    w.close();app.processEvents()
    assert not prompts, prompts
    assert not w.isVisible()
