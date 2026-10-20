from html import escape
from pathlib import Path
from sqlalchemy import select, func
from models.schema import Order, OrderItem, Invoice, Payment, OrderItemModifier
from core.money import money
from core.paths import resource
from localization.strings import tr
from core.dates import BUSINESS_TZ
from datetime import datetime


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
    precision = int(settings.get('precision', '0'))
    fmt = lambda value: money(value, precision)
    local_time = datetime.fromisoformat(order.created_at).astimezone(BUSINESS_TZ).strftime('%Y-%m-%d %H:%M')
    rows = []
    for item in items:
        extras = ', '.join(m.name for m in modifiers[item.id])
        rows.append(f'<tr><td>{escape(item.name)}<br/><small>{escape(extras)} {escape(item.notes)}</small></td><td>{item.quantity}</td><td>{fmt(item.price*item.quantity)}</td></tr>')
    totals = [('Gross sales', order.subtotal), ('Discount', -order.discount), ('Tax', order.tax), ('Service', order.service), ('Total', order.total), ('Payment', paid), ('Balance due', max(order.total-paid,0))]
    return f'''<html><head><meta charset="utf-8"/></head><body dir="{direction}" style="font-family:DejaVu Sans;font-size:8pt;color:#000;background:#fff;">
    <h2 align="center">{escape(settings['restaurant_name'])}</h2><p align="center">{escape(settings.get('address',''))}<br/>{escape(settings.get('phone',''))}<br/>{escape(settings.get('receipt_header',''))}</p>
    <p>{escape(invoice.number if invoice else 'DRAFT')} • {escape(local_time)}<br/>{escape(tr(order.status,lang))} • {escape(tr(order.kind,lang))}</p>
    <table width="100%" cellspacing="4"><tr><th width="52%">{tr('Name',lang)}</th><th width="12%">{tr('Quantity',lang)}</th><th width="36%">{tr('Total',lang)}</th></tr>{''.join(rows)}</table><hr/>
    {''.join(f'<p>{tr(k,lang)}: {fmt(v)}</p>' for k,v in totals)}<p align="center">{escape(settings.get('receipt_footer',''))}</p></body></html>'''


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


def printer_names():
    from PySide6.QtPrintSupport import QPrinterInfo
    return list(QPrinterInfo.availablePrinterNames())


def make_printer(html, paper='80', printer_name='', pdf_path=None):
    """Common page geometry for real thermal printing, preview and Qt PDF tests."""
    from PySide6.QtCore import QSizeF, QMarginsF
    from PySide6.QtGui import QTextDocument, QPageSize, QPageLayout, QFont
    from PySide6.QtPrintSupport import QPrinter
    if paper not in ('58', '80', 'A4'):
        raise ValueError('Unsupported paper size')
    if printer_name and printer_name not in printer_names():
        raise ValueError('Selected printer is not installed')
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    if printer_name:
        printer.setPrinterName(printer_name)
    if pdf_path or not printer_name:
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        if pdf_path:
            printer.setOutputFileName(str(pdf_path))
    document = QTextDocument()
    document.setDefaultFont(QFont('DejaVu Sans', 8))
    document.setDocumentMargin(0)
    document.setHtml(html)
    if paper == 'A4':
        page = QPageSize(QPageSize.PageSizeId.A4)
        margins = QMarginsF(10,10,10,10)
    else:
        width = int(paper)
        # Measure wrapping at the printable width; use a continuous thermal page.
        document.setTextWidth((width-6)*96/25.4)
        height = max(65, min(3000, document.size().height()*25.4/96+18))
        page = QPageSize(QSizeF(width,height), QPageSize.Unit.Millimeter, 'GAS HUNAR '+paper+'mm', QPageSize.SizeMatchPolicy.ExactMatch)
        margins = QMarginsF(3,3,3,3)
    printer.setPageSize(page)
    printer.setPageMargins(margins, QPageLayout.Unit.Millimeter)
    return printer, document


def print_preview(parent, html, paper='80', printer_name=''):
    from PySide6.QtPrintSupport import QPrintPreviewDialog
    printer, document = make_printer(html, paper, printer_name)
    dialog = QPrintPreviewDialog(printer, parent)
    dialog.resize(850,650)
    dialog.paintRequested.connect(document.print_)
    dialog.exec()


def print_receipt(parent, html, paper='80', printer_name=''):
    from PySide6.QtWidgets import QDialog
    from PySide6.QtPrintSupport import QPrintDialog, QPrinter
    if not printer_names():
        raise ValueError('Install a Windows printer to print. PDF export is still available.')
    printer, document = make_printer(html, paper, printer_name)
    dialog = QPrintDialog(printer,parent)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return False
    document.print_(printer)
    if printer.printerState() == QPrinter.PrinterState.Error:
        raise RuntimeError('The printer reported an error. Check its connection and paper.')
    return True


def qt_receipt_pdf(html, target, paper='80'):
    from PySide6.QtPrintSupport import QPrinter
    printer, document = make_printer(html,paper,pdf_path=target)
    document.print_(printer)
    if printer.printerState() == QPrinter.PrinterState.Error or not Path(target).is_file():
        raise RuntimeError('Receipt PDF could not be written')
    return Path(target)
