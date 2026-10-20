from html import escape
from pathlib import Path
from sqlalchemy import select, func
from models.schema import Order, OrderItem, Invoice, Payment, OrderItemModifier
from core.money import money
from core.paths import resource
from localization.strings import tr


def receipt_data(db, order_id):
    with db.read() as s:
        order = s.get(Order, order_id)
        if not order:
            raise ValueError('Order not found')
        invoice = s.scalar(select(Invoice).where(Invoice.order_id == order_id))
        items = list(s.scalars(select(OrderItem).where(OrderItem.order_id == order_id)))
        modifiers = {i.id: list(s.scalars(select(OrderItemModifier).where(OrderItemModifier.item_id == i.id))) for i in items}
        paid = s.scalar(select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.order_id == order_id))
        return order, invoice, items, modifiers, paid


def receipt_html(db, order_id, settings):
    order, invoice, items, modifiers, paid = receipt_data(db, order_id)
    lang = settings.get('language', 'ckb')
    direction = 'rtl' if lang in ('ar', 'ckb') else 'ltr'
    rows = []
    for item in items:
        extras = ', '.join(m.name for m in modifiers[item.id])
        rows.append(f'<tr><td>{escape(item.name)}<br/><small>{escape(extras)} {escape(item.notes)}</small></td><td>{item.quantity}</td><td>{money(item.price*item.quantity)}</td></tr>')
    totals = [('Gross sales', order.subtotal), ('Discount', -order.discount), ('Tax', order.tax), ('Service', order.service), ('Total', order.total), ('Payment', paid)]
    return f'''<html><head><meta charset="utf-8"/></head><body dir="{direction}" style="font-family:DejaVu Sans;font-size:10pt;">
    <h2 align="center">{escape(settings['restaurant_name'])}</h2><p align="center">{escape(settings.get('address',''))}<br/>{escape(settings.get('phone',''))}<br/>{escape(settings.get('receipt_header',''))}</p>
    <p>{escape(invoice.number if invoice else 'DRAFT')} • {escape(order.created_at[:19])}<br/>{escape(order.status)} • {escape(order.kind)}</p>
    <table width="100%" cellspacing="4"><tr><th>{tr('Name',lang)}</th><th>{tr('Quantity',lang)}</th><th>{tr('Total',lang)}</th></tr>{''.join(rows)}</table><hr/>
    {''.join(f'<p>{tr(k,lang)}: {money(v)}</p>' for k,v in totals)}<p align="center">{escape(settings.get('receipt_footer',''))}</p></body></html>'''


def generate_pdf(db, order_id, settings, target):
    # ReportLab handles page layout; bundled Unicode font plus Arabic reshaping handles Sorani glyphs.
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.units import mm
    from reportlab.lib.utils import simpleSplit
    import arabic_reshaper
    from bidi.algorithm import get_display
    font = resource('assets/DejaVuSans.ttf')
    if not font.exists():
        raise RuntimeError('Bundled Unicode font is missing; run scripts/create_assets.py')
    pdfmetrics.registerFont(TTFont('GHUnicode', str(font)))
    width = 210*mm if settings.get('paper_width') == 'A4' else int(settings.get('paper_width', '80'))*mm
    order, invoice, items, modifiers, paid = receipt_data(db, order_id)
    logical = [settings['restaurant_name'], settings.get('address',''), settings.get('phone',''), settings.get('receipt_header',''), invoice.number if invoice else 'DRAFT', order.created_at[:19], order.status]
    for item in items:
        logical.extend([item.name, f'{item.quantity} × {money(item.price)} = {money(item.price*item.quantity)}', item.notes])
        logical.extend(m.name for m in modifiers[item.id])
    lang = settings.get('language', 'ckb')
    logical.extend(f'{tr(k,lang)}: {money(v)}' for k,v in [('Gross sales',order.subtotal),('Discount',-order.discount),('Tax',order.tax),('Service',order.service),('Total',order.total),('Payment',paid)])
    logical.append(settings.get('receipt_footer',''))
    lines = []
    for text in logical:
        visual = get_display(arabic_reshaper.reshape(str(text)))
        lines.extend(simpleSplit(visual, 'GHUnicode', 9, width-12*mm) or [''])
    height = max(100*mm, (len(lines)*14 + 40)) if settings.get('paper_width') != 'A4' else 297*mm
    c = canvas.Canvas(str(target), pagesize=(width, height))
    c.setTitle('GAS HUNAR ' + (invoice.number if invoice else str(order_id)))
    c.setFont('GHUnicode',9)
    y = height-20
    for line in lines:
        if y < 20:
            c.showPage(); c.setFont('GHUnicode',9); y=height-20
        if lang in ('ckb','ar'):
            c.drawRightString(width-6*mm,y,line)
        else:
            c.drawString(6*mm,y,line)
        y -= 14
    c.save()
    return Path(target)


def print_preview(parent, html, paper='80'):
    from PySide6.QtCore import QSizeF, QMarginsF
    from PySide6.QtGui import QTextDocument, QPageSize, QPageLayout
    from PySide6.QtPrintSupport import QPrinter, QPrintPreviewDialog
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    if paper == 'A4':
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    else:
        printer.setPageSize(QPageSize(QSizeF(int(paper), 250), QPageSize.Unit.Millimeter))
    printer.setPageMargins(QMarginsF(3,3,3,3), QPageLayout.Unit.Millimeter)
    document = QTextDocument()
    document.setHtml(html)
    dialog = QPrintPreviewDialog(printer, parent)
    dialog.paintRequested.connect(document.print_)
    dialog.exec()
