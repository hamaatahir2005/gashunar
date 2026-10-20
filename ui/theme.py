def stylesheet(theme):
    dark = theme == 'dark'
    bg, panel, text, muted, border = ('#101827','#172338','#f3f5f8','#a4b2c5','#2b3b52') if dark else ('#f3f5f9','#ffffff','#142036','#57677c','#d9e0ea')
    return f'''
    QWidget {{ background:{bg}; color:{text}; font-family:"DejaVu Sans","Segoe UI"; font-size:13px; }}
    QMainWindow {{background:{bg};}} QLabel#heading {{font-size:25px; font-weight:700; padding:12px 0;}}
    QLabel#brand {{font-size:21px; color:#d7b66f; font-weight:700; padding:18px 8px;}}
    QFrame#sidebar, QFrame#sidebar * {{ background:{panel}; }}
    QPushButton {{background:{panel}; border:1px solid {border}; border-radius:7px; padding:10px 15px; min-height:22px;}}
    QPushButton:hover {{border-color:#d7b66f;}} QPushButton:pressed {{background:#8a6b32;}}
    QPushButton#primary {{background:#d7b66f; color:#142036; font-weight:700;}}
    QPushButton#nav {{text-align:left; border:0; padding:10px;}} QPushButton#nav:checked {{background:#34425a; color:#efd18e;}}
    QLineEdit,QComboBox,QSpinBox,QTextEdit,QDateEdit {{background:{panel}; border:1px solid {border}; border-radius:6px; padding:9px; min-height:21px;}}
    QTableWidget {{background:{panel}; alternate-background-color:{bg}; border:1px solid {border}; gridline-color:{border}; selection-background-color:#66552f;}}
    QHeaderView::section {{background:{panel}; color:{muted}; border:0; padding:10px;}}
    QScrollArea {{border:0;}} QGroupBox {{border:1px solid {border}; border-radius:8px; margin-top:12px; padding-top:12px;}}
    QLabel#metric {{font-size:23px; font-weight:700; color:#d7b66f; padding:8px;}}
    QStatusBar {{color:{muted};}} QToolTip {{background:{panel};color:{text};border:1px solid {border};}}
    '''
