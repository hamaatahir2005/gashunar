from datetime import timedelta
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QFrame,QLabel,
    QDateEdit,QPushButton,QScrollArea,QFileDialog)
from core.dates import business_today,period_dates
from core.money import money
from ui.theme import PALETTES


class DateRange(QWidget):
    def __init__(self, window, changed):
        super().__init__();self.w=window;layout=QHBoxLayout(self);layout.setContentsMargins(0,0,0,0)
        today=business_today()
        self.start,self.end=QDateEdit(),QDateEdit()
        for label,editor in [('From date',self.start),('To date',self.end)]:
            editor.setDisplayFormat('yyyy-MM-dd');editor.setCalendarPopup(True);editor.setKeyboardTracking(False)
            editor.setDate(QDate(today.year,today.month,today.day));editor.setMinimumWidth(130)
            layout.addWidget(QLabel(window.t(label)));layout.addWidget(editor)
        for label,key in [('Today','day'),('This week','week'),('This month','month')]:
            button=QPushButton(window.t(label));button.clicked.connect(lambda _,k=key:self.preset(k,changed));layout.addWidget(button)
        apply=QPushButton(window.t('Calculate'));apply.setObjectName('primary');apply.clicked.connect(lambda:window.safe(changed));layout.addWidget(apply)
    def dates(self):
        start,end=self.start.date().toPython(),self.end.date().toPython()
        if start>end:raise ValueError(self.w.t('Start date must not be after end date'))
        return start,end
    def preset(self,key,changed):
        first,last=period_dates()[key]
        self.start.setDate(QDate(first.year,first.month,first.day));self.end.setDate(QDate(last.year,last.month,last.day))
        self.w.safe(changed)


class ProfitChart(QWidget):
    def __init__(self,window):
        super().__init__();self.w,self.data=window,[];self.setMinimumHeight(155)
    def paintEvent(self,event):
        p=PALETTES[self.w.config['theme']];painter=QPainter(self);painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width=max(self.width()-32,1)/max(len(self.data),1)
        maximum=max([abs(v) for _,v in self.data]+[1]);baseline=self.height()-30
        has_negative=any(v<0 for _,v in self.data)
        if has_negative:baseline=int((self.height()-32)*0.63)
        space=(baseline-10) if not has_negative else min(baseline-10,self.height()-baseline-25)
        painter.setPen(QPen(QColor(p['border']),1));painter.drawLine(16,baseline,self.width()-16,baseline)
        for i,(day,value) in enumerate(self.data):
            h=int(abs(value)/maximum*space);x=int(16+i*width)
            painter.setPen(Qt.PenStyle.NoPen);painter.setBrush(QColor(p['positive'] if value>=0 else '#e16972'))
            painter.drawRoundedRect(x,baseline-h if value>=0 else baseline,max(int(width-7),3),max(h,1),3,3)
            if i%max(len(self.data)//7,1)==0:
                painter.setPen(QColor(p['muted']));painter.drawText(x,self.height()-7,day[5:])


def card(label,kind='card'):
    frame=QFrame();frame.setObjectName(kind);layout=QVBoxLayout(frame);layout.setContentsMargins(16,12,16,12)
    heading=QLabel(label);heading.setObjectName('muted');layout.addWidget(heading)
    value=QLabel('—');value.setObjectName('profit' if kind=='profitCard' else 'metric');value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse);layout.addWidget(value)
    caption=QLabel();caption.setObjectName('muted');layout.addWidget(caption)
    return frame,value,caption


class FinancialOverview(QScrollArea):
    """Shared dashboard/report view; typed local dates and inclusive range exports."""
    def __init__(self,window,reports=False):
        super().__init__();self.w,self.reports=window,reports;self.setWidgetResizable(True)
        body=QWidget();self.setWidget(body);layout=QVBoxLayout(body);layout.setContentsMargins(8,8,8,8);layout.setSpacing(14)
        eyebrow=QLabel('GAS HUNAR / '+window.t('Financial overview'));eyebrow.setObjectName('eyebrow');layout.addWidget(eyebrow)
        heading=QLabel(window.t('Your restaurant, at a glance'));heading.setObjectName('heading');layout.addWidget(heading)
        hint=QLabel(window.t('Profit = revenue − food cost − expenses'));hint.setObjectName('muted');layout.addWidget(hint)
        self.range=DateRange(window,self.reload);layout.addWidget(self.range)
        explanation=QLabel(window.t('Both dates included · Iraq time · Week starts Saturday'));explanation.setObjectName('muted');layout.addWidget(explanation)
        profits=QHBoxLayout();self.profits={}
        for key,label in [('day','Day profit'),('week','Week profit'),('month','Month profit')]:
            frame,value,caption=card(window.t(label),'profitCard');profits.addWidget(frame);self.profits[key]=(value,caption)
        layout.addLayout(profits)
        self.period_hint=QLabel(window.t('Period cards follow the selected end date'));self.period_hint.setObjectName('muted');layout.addWidget(self.period_hint)
        totals=QGridLayout();self.metrics={}
        keys=[('Net profit','net_profit'),('Net sales','net_sales'),('Cost of goods','cogs'),('Expenses','expenses'),('Gross profit','gross_profit'),('Cash movement','cash_movement'),('Order count','orders'),('Tax','tax_collected')]
        for i,(label,key) in enumerate(keys):
            frame,value,_=card(window.t(label));totals.addWidget(frame,i//4,i%4);self.metrics[key]=value
        layout.addLayout(totals)
        self.chart=ProfitChart(window);chart_frame=QFrame();chart_frame.setObjectName('card');chart_layout=QVBoxLayout(chart_frame)
        chart_layout.addWidget(QLabel(window.t('Daily net profit')));chart_layout.addWidget(self.chart);layout.addWidget(chart_frame)
        self.operations=QLabel();self.operations.setWordWrap(True);self.operations.setObjectName('muted');layout.addWidget(self.operations)
        self.best=QLabel();self.best.setWordWrap(True);layout.addWidget(self.best)
        export=QHBoxLayout();export.addStretch()
        for label,extension in [('Export CSV','csv'),('Export PDF','pdf')]:
            b=QPushButton(window.t(label));b.clicked.connect(lambda _,e=extension:window.safe(lambda:self.export(e)));export.addWidget(b)
        layout.addLayout(export);layout.addStretch()
    def reload(self):
        first,last=self.range.dates();self.summary=self.w.finance.range_summary(self.w.user,first,last)
        periods=self.w.finance.periods(self.w.user,last)
        precision=int(self.w.config.get('precision','0'))
        for key,(value,caption) in self.profits.items():
            result=periods[key];value.setText(money(result['net_profit'],precision));value.setProperty('negative',result['net_profit']<0)
            value.style().unpolish(value);value.style().polish(value);caption.setText(result['start']+' → '+result['end'])
        for key,value in self.metrics.items():value.setText(str(self.summary[key]) if key=='orders' else money(self.summary[key],precision))
        days=min((last-first).days+1,14)
        self.chart.data=self.w.finance.daily(self.w.user,days,last,'net_profit');self.chart.update()
        self.operations.setText('   •   '.join(self.w.t(k)+': '+str(self.summary[v]) for k,v in [('Open tables','open_tables'),('Pending kitchen','pending_kitchen'),('Low stock','low_stock')]))
        self.best.setText(self.w.t('Best sellers')+'   '+ '   •   '.join(f'{name}: {qty}' for name,qty in self.w.finance.best_sellers(self.w.user)))
    def export(self,extension):
        first,last=self.range.dates();data=self.w.finance.range_summary(self.w.user,first,last)
        path,_=QFileDialog.getSaveFileName(self,self.w.t('Reports'),f'gas-hunar-{first}-{last}.{extension}',f'{extension.upper()} (*.{extension})')
        if not path:return
        def work():
            if extension=='csv':
                from reports.export import csv_report
                csv_report(path,data)
            else:
                from reports.export import pdf_report
                pdf_report(path,data,self.w.config['restaurant_name'],f'{first} → {last} / Asia/Baghdad')
            return path
        self.w.background(work,lambda _:self.w.statusBar().showMessage(self.w.t('Export complete')))
