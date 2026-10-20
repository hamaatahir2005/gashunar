"""Coherent native Qt styling for both day and night service."""
PALETTES = {
    'dark': {'bg':'#0c1422','panel':'#142033','raised':'#1a2940','text':'#f0f4f9','muted':'#a2b1c7','border':'#273951','gold':'#e0bb70','selected':'#2a3c52','positive':'#58d2ae'},
    'light': {'bg':'#f1f4f8','panel':'#ffffff','raised':'#f7f9fc','text':'#192b43','muted':'#617189','border':'#dce3ed','gold':'#8b631f','selected':'#f8edda','positive':'#157d62'},
}


def stylesheet(theme):
    p = PALETTES.get(theme, PALETTES['dark'])
    return f'''
    QWidget {{ background:{p['bg']}; color:{p['text']}; font-family:"DejaVu Sans","Segoe UI"; font-size:12px; }}
    QMainWindow {{background:{p['bg']};}}
    QLabel {{background:transparent;}}
    QLabel#heading {{font-size:23px;font-weight:700;padding:8px 0;}}
    QLabel#brand {{font-size:19px;color:{p['gold']};font-weight:700;padding:9px 2px;}}
    QLabel#muted {{color:{p['muted']};font-size:11px;}}
    QLabel#eyebrow {{color:{p['gold']};font-weight:700;letter-spacing:2px;}}
    QLabel#offline {{color:{p['positive']};border:1px solid {p['border']};border-radius:12px;padding:6px 12px;}}
    QFrame#sidebar {{background:{p['panel']};border:0;}}
    QFrame#topbar {{background:{p['panel']};border-bottom:1px solid {p['border']};}}
    QFrame#card,QGroupBox {{background:{p['panel']};border:1px solid {p['border']};border-radius:12px;}}
    QFrame#profitCard {{background:{p['panel']};border:1px solid {p['border']};border-top:3px solid {p['gold']};border-radius:12px;}}
    QGroupBox {{margin-top:14px;padding:12px;}}
    QFrame#card QLabel,QFrame#profitCard QLabel {{border:0;background:transparent;}}
    QPushButton {{background:{p['panel']};border:1px solid {p['border']};border-radius:8px;padding:8px 13px;min-height:22px;}}
    QPushButton:hover {{background:{p['raised']};border-color:{p['gold']};}}
    QPushButton:pressed {{background:{p['selected']};}}
    QPushButton:disabled {{color:{p['muted']};border-color:{p['border']};}}
    QPushButton#primary {{background:#d9b46b;color:#142033;font-weight:700;border:1px solid #d9b46b;}}
    QPushButton#nav {{background:transparent;text-align:left;border:0;border-radius:7px;padding:9px 12px;}}
    QPushButton#nav:checked {{background:{p['selected']};color:{p['gold']};font-weight:700;}}
    QPushButton#productTile {{background:{p['panel']};text-align:center;border-radius:12px;padding:12px;}}
    QLineEdit,QComboBox,QSpinBox,QTextEdit,QDateEdit {{background:{p['panel']};border:1px solid {p['border']};border-radius:7px;padding:7px;min-height:22px;selection-background-color:{p['selected']};}}
    QLineEdit:focus,QComboBox:focus,QDateEdit:focus {{border-color:{p['gold']};}}
    QComboBox QAbstractItemView {{background:{p['panel']};selection-background-color:{p['selected']};}}
    QTableWidget {{background:{p['panel']};alternate-background-color:{p['raised']};border:1px solid {p['border']};border-radius:10px;gridline-color:{p['border']};selection-background-color:{p['selected']};selection-color:{p['text']};}}
    QTableWidget::item {{padding:8px;border-bottom:1px solid {p['border']};}}
    QHeaderView::section {{background:{p['raised']};color:{p['muted']};border:0;padding:11px;font-weight:600;}}
    QScrollArea {{border:0;background:transparent;}}
    QScrollBar:vertical {{background:{p['bg']};width:8px;}}
    QScrollBar::handle:vertical {{background:{p['border']};border-radius:4px;min-height:30px;}}
    QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {{height:0;}}
    QLabel#metric {{font-size:21px;font-weight:700;color:{p['gold']};padding:3px 0;}}
    QLabel#profit {{font-size:26px;font-weight:700;color:{p['positive']};padding:6px 0;}}
    QLabel#profit[negative="true"] {{color:#e16972;}}
    QLabel#error {{color:#e16972;}}
    QStatusBar {{color:{p['muted']};background:{p['panel']};}}
    QToolTip {{background:{p['panel']};color:{p['text']};border:1px solid {p['border']};padding:6px;}}
    '''
