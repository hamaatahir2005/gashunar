from datetime import date, timedelta
from core.dates import business_today, parse_date, utc_midnight, period_dates
from sqlalchemy import select, func
from models.schema import Order, Payment, Refund, Expense, Ingredient, OrderItem, Customer, Purchase, RestaurantTable


class Finance:
    def __init__(self, db, auth):
        self.db, self.auth = db, auth

    def summary(self, actor, start=None, end=None):
        self.auth.require(actor, 'reports')
        start_date = parse_date(start) if start is not None else business_today()
        end_date = parse_date(end) if end is not None else start_date + timedelta(days=1)
        if start_date >= end_date:
            raise ValueError('End date must be after start (end is exclusive)')
        start, end = utc_midnight(start_date), utc_midnight(end_date)
        with self.db.read() as s:
            sales = list(s.scalars(select(Order).where(Order.confirmed_at >= start, Order.confirmed_at < end)))
            refunds = list(s.scalars(select(Refund).where(Refund.created_at >= start, Refund.created_at < end)))
            payments = list(s.scalars(select(Payment).where(Payment.created_at >= start, Payment.created_at < end)))
            expenses = list(s.scalars(select(Expense).where(Expense.date >= start_date.isoformat(), Expense.date < end_date.isoformat())))
            purchases = list(s.scalars(select(Purchase).where(Purchase.created_at >= start, Purchase.created_at < end)))
            gross_sales = sum(o.subtotal for o in sales)
            discounts = sum(o.discount for o in sales)
            revenue = sum(o.subtotal - o.discount + o.service for o in sales) - sum(r.revenue for r in refunds)
            cogs = sum(o.cogs for o in sales) - sum(r.cogs_reversal for r in refunds)
            expense = sum(e.amount for e in expenses)
            cash = sum(p.amount for p in payments if p.method == 'cash') - sum(r.amount for r in refunds if r.method == 'cash') - sum(e.amount for e in expenses if e.method == 'cash')
            return {'gross_sales': gross_sales, 'discounts': discounts, 'net_sales': revenue,
                    'tax_collected': sum(o.tax for o in sales) - sum(s.get(Order, r.order_id).tax for r in refunds), 'cogs': cogs, 'gross_profit': revenue-cogs,
                    'expenses': expense, 'net_profit': revenue-cogs-expense,
                    'cash_movement': cash, 'receipts': sum(p.amount for p in payments),
                    'refunds': sum(r.amount for r in refunds), 'inventory_purchases_paid': sum(p.paid for p in purchases),
                    'orders': len(sales), 'customers': len({o.customer_id for o in sales if o.customer_id}),
                    'completed': sum(o.status == 'completed' for o in sales),
                    'open_tables': len(set(s.scalars(select(Order.table_id).where(Order.table_id.is_not(None), Order.status.in_(['held', 'confirmed']))))),
                    'pending_kitchen': s.scalar(select(func.count(Order.id)).where(Order.confirmed_at.is_not(None), Order.status != 'refunded', Order.kitchen_status != 'completed')),
                    'low_stock': s.scalar(select(func.count(Ingredient.id)).where(Ingredient.quantity <= Ingredient.minimum))}

    def range_summary(self, actor, start, end):
        first, last = parse_date(start), parse_date(end)
        if first > last:
            raise ValueError('Start date must be before or equal to end date')
        return self.summary(actor, first, last + timedelta(days=1))

    def periods(self, actor, reference=None):
        self.auth.require(actor, 'reports')
        return {key: {'start': first.isoformat(), 'end': last.isoformat(),
                      **self.range_summary(actor, first, last)}
                for key, (first, last) in period_dates(reference).items()}

    def daily(self, actor, days=14, end=None, metric='net_sales'):
        self.auth.require(actor, 'reports')
        if not 1 <= days <= 31 or metric not in ('net_sales', 'net_profit'):
            raise ValueError('Invalid chart range or metric')
        last = parse_date(end) if end is not None else business_today()
        return [(str(last-timedelta(days=i)),
                 self.range_summary(actor, last-timedelta(days=i), last-timedelta(days=i))[metric])
                for i in reversed(range(days))]

    def best_sellers(self, actor):
        self.auth.require(actor, 'reports')
        with self.db.read() as s:
            return s.execute(select(OrderItem.name, func.sum(OrderItem.quantity)).join(Order, Order.id == OrderItem.order_id).where(Order.status.in_(['confirmed', 'completed'])).group_by(OrderItem.name).order_by(func.sum(OrderItem.quantity).desc()).limit(10)).all()

    def balances(self, actor):
        self.auth.require(actor, 'reports')
        with self.db.read() as s:
            result = []
            for customer in s.scalars(select(Customer)):
                orders = list(s.scalars(select(Order).where(Order.customer_id == customer.id, Order.status == 'confirmed')))
                ids = [o.id for o in orders]
                paid = s.scalar(select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.order_id.in_(ids))) if ids else 0
                result.append((customer.name, sum(o.total for o in orders)-paid))
            return result
