import csv
from core.money import amount


def csv_report(path, summary):
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['Metric', 'Value', 'Unit'])
        counts = {'orders','customers','completed','open_tables','pending_kitchen','low_stock'}
        for key, value in summary.items():
            writer.writerow([key, value if key in counts else amount(value), 'count' if key in counts else 'IQD'])


def pdf_report(path, summary, title, period=""):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from core.paths import resource
    import arabic_reshaper
    from bidi.algorithm import get_display
    pdfmetrics.registerFont(TTFont('GHUnicode', str(resource('assets/DejaVuSans.ttf'))))
    c = canvas.Canvas(str(path), pagesize=A4)
    c.setFont('GHUnicode',16)
    c.drawString(40,800,get_display(arabic_reshaper.reshape(title)))
    c.setFont('GHUnicode',11)
    if period:
        c.setFont("GHUnicode",9)
        c.drawString(40,778,get_display(arabic_reshaper.reshape(period)))
        c.setFont("GHUnicode",11)
    y=750
    counts = {'orders','customers','completed','open_tables','pending_kitchen','low_stock'}
    for key,value in summary.items():
        c.drawString(40,y,key.replace('_',' ').title())
        c.drawRightString(550,y,str(value) if key in counts else f'{amount(value):,.3f} IQD')
        y-=24
    c.save()
