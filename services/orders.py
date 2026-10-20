from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4
from sqlalchemy import select, func, delete
from core.money import units, percentage, decimal
from models.schema import (Order, OrderItem, Product, Recipe, Ingredient, StockMovement, Payment,
                           Invoice, Refund, CashSession, Setting, AuditLog, RestaurantTable, Customer,
                           Modifier, OrderItemModifier, ProductVariant, now)


def rounded(value):
    return int(Decimal(value).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


class Orders:
    def __init__(self, db, auth):
        self.db, self.auth = db, auth

    def _audit(self, s, actor, action, detail):
        s.add(AuditLog(user_id=actor, action=action, detail=str(detail)))

    def _order(self, s, order_id):
        order = s.get(Order, order_id)
        if not order:
            raise ValueError('Order not found')
        return order

    def _session(self, s, actor):
        session = s.scalar(select(CashSession).where(CashSession.user_id == actor, CashSession.closed_at.is_(None)))
        if not session:
            raise ValueError('Open a cash drawer session first')
        return session

    def hold(self, actor, lines, kind='takeaway', table_id=None, customer_id=None, notes='', token=None,
             discount='0', percent=False, order_id=None):
        self.auth.require(actor, 'pos')
        if kind not in ('dine-in', 'takeaway', 'delivery') or not lines:
            raise ValueError('Select order type and at least one item')
        token = token or str(uuid4())
        with self.db.write() as s:
            existing = s.scalar(select(Order).where(Order.token == token))
            if existing and not order_id:
                return existing.id
            if customer_id and not s.get(Customer, customer_id):
                raise ValueError('Customer not found')
            if kind == 'dine-in' and not table_id:
                raise ValueError('Select a table for dine-in')
            if table_id:
                if not s.get(RestaurantTable, table_id):
                    raise ValueError('Table not found')
                occupied = select(Order).where(Order.table_id == table_id, Order.status.in_(['held', 'confirmed']))
                if order_id:
                    occupied = occupied.where(Order.id != order_id)
                if s.scalar(occupied):
                    raise ValueError('Table already occupied')
            order = self._order(s, order_id) if order_id else Order(token=token, user_id=actor)
            if order_id:
                if order.status != 'held' or order.user_id != actor:
                    raise ValueError('Only your held orders can be edited')
                item_ids = select(OrderItem.id).where(OrderItem.order_id == order.id)
                s.execute(delete(OrderItemModifier).where(OrderItemModifier.item_id.in_(item_ids)))
                s.execute(delete(OrderItem).where(OrderItem.order_id == order.id))
            order.kind, order.table_id, order.customer_id, order.notes = kind, table_id, customer_id, notes
            s.add(order)
            s.flush()
            subtotal = cogs = 0
            for line in lines:
                p = s.get(Product, int(line['product_id']))
                qty = int(line['quantity'])
                if decimal(line['quantity']) != qty or not 1 <= qty <= 10000:
                    raise ValueError('Quantity must be a whole number between 1 and 10,000')
                if not p or not p.active:
                    raise ValueError('Product unavailable')
                name, price = p.name, p.price
                if line.get('variant_id'):
                    variant = s.get(ProductVariant, line['variant_id'])
                    if not variant or variant.product_id != p.id:
                        raise ValueError('Invalid variant')
                    name += ' / ' + variant.name
                    price = variant.price
                modifiers = []
                for mid in set(line.get('modifiers', [])):
                    modifier = s.get(Modifier, mid)
                    if not modifier:
                        raise ValueError('Invalid modifier')
                    modifiers.append(modifier)
                    price += modifier.price
                recipes = list(s.scalars(select(Recipe).where(Recipe.product_id == p.id)))
                cost = sum(rounded(Decimal(r.quantity) * s.get(Ingredient, r.ingredient_id).cost / 1000) for r in recipes) if recipes else p.cost
                item = OrderItem(order_id=order.id, product_id=p.id, name=name, quantity=qty, price=price, cost=cost, notes=line.get('notes', ''))
                s.add(item)
                s.flush()
                for modifier in modifiers:
                    s.add(OrderItemModifier(item_id=item.id, modifier_id=modifier.id, name=modifier.name, price=modifier.price))
                subtotal += price * qty
                cogs += cost * qty
            discount_value = percentage(subtotal, discount) if percent else units(discount)
            if not 0 <= discount_value <= subtotal:
                raise ValueError('Discount cannot exceed the subtotal')
            settings = {x.key: x.value for x in s.scalars(select(Setting))}
            order.subtotal, order.discount, order.cogs = subtotal, discount_value, cogs
            order.tax = percentage(subtotal - discount_value, settings['tax_rate'])
            order.service = percentage(subtotal - discount_value, settings['service_rate'])
            order.total = subtotal - discount_value + order.tax + order.service
            self._audit(s, actor, 'order.held', order.id)
            return order.id

    def _confirm(self, s, actor, order):
        if order.status != 'held':
            return
        prevent = s.get(Setting, 'prevent_negative_stock').value == 'true'
        order.cogs = 0
        for item in s.scalars(select(OrderItem).where(OrderItem.order_id == order.id)):
            recipes = list(s.scalars(select(Recipe).where(Recipe.product_id == item.product_id)))
            item.cost = sum(rounded(Decimal(r.quantity) * s.get(Ingredient, r.ingredient_id).cost / 1000) for r in recipes) if recipes else s.get(Product, item.product_id).cost
            order.cogs += item.cost * item.quantity
            for recipe in recipes:
                ingredient = s.get(Ingredient, recipe.ingredient_id)
                quantity = recipe.quantity * item.quantity
                if prevent and ingredient.quantity < quantity:
                    raise ValueError('Insufficient stock: ' + ingredient.name)
                ingredient.quantity -= quantity
                s.add(StockMovement(ingredient_id=ingredient.id, order_id=order.id, quantity=-quantity, reason='sale'))
        order.status, order.confirmed_at = 'confirmed', now()
        invoice = Invoice(order_id=order.id, number='pending-' + uuid4().hex)
        s.add(invoice)
        s.flush()
        invoice.number = s.get(Setting, 'invoice_prefix').value + f'{invoice.id:08d}'
        self._audit(s, actor, 'order.confirmed', order.id)

    def confirm(self, actor, order_id):
        self.auth.require(actor, 'pos')
        with self.db.write() as s:
            order = self._order(s, order_id)
            if order.status not in ('held', 'confirmed', 'completed'):
                raise ValueError('Order cannot be confirmed')
            self._confirm(s, actor, order)

    def pay(self, actor, order_id, payments, token):
        self.auth.require(actor, 'pos')
        if not payments or not token:
            raise ValueError('Payment and transaction key required')
        with self.db.write() as s:
            prior = s.scalar(select(Payment).where(Payment.token == token + ':0'))
            if prior:
                if prior.order_id != order_id:
                    raise ValueError('Transaction key already used')
                return
            order = self._order(s, order_id)
            if order.status not in ('held', 'confirmed'):
                raise ValueError('Order is not payable')
            converted = [(method, units(value)) for method, value in payments]
            if any(m not in ('cash', 'card') or v <= 0 for m, v in converted):
                raise ValueError('Payments must be positive cash or card amounts')
            paid = s.scalar(select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.order_id == order_id))
            if sum(v for _, v in converted) > order.total - paid:
                raise ValueError('Payment exceeds outstanding balance; enter amount applied, excluding change')
            self._confirm(s, actor, order)
            for index, (method, value) in enumerate(converted):
                session_id = self._session(s, actor).id if method == 'cash' else None
                s.add(Payment(order_id=order_id, token=f'{token}:{index}', method=method, amount=value, session_id=session_id))
            if paid + sum(v for _, v in converted) == order.total:
                order.status = 'completed'
            self._audit(s, actor, 'order.payment', order_id)

    def cancel_held(self, actor, order_id):
        self.auth.require(actor, 'pos')
        with self.db.write() as s:
            order = self._order(s, order_id)
            if order.status != 'held':
                raise ValueError('Confirmed orders must be refunded')
            order.status = 'cancelled'
            self._audit(s, actor, 'order.cancelled', order.id)

    def refund(self, actor, order_id, reason, method='cash', restock=False, token=None):
        self.auth.require(actor, 'refunds')
        if not reason.strip() or method not in ('cash', 'card'):
            raise ValueError('Refund reason and valid payment method required')
        with self.db.write() as s:
            order = self._order(s, order_id)
            existing = s.scalar(select(Refund).where(Refund.order_id == order_id))
            if existing:
                return existing.id
            if order.status not in ('completed', 'confirmed'):
                raise ValueError('Only confirmed sales can be refunded')
            paid = s.scalar(select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.order_id == order_id))
            session_id = self._session(s, actor).id if paid and method == 'cash' else None
            if restock:
                # Reverse original movements rather than today's recipe.
                for movement in list(s.scalars(select(StockMovement).where(StockMovement.order_id == order_id, StockMovement.reason == 'sale'))):
                    s.get(Ingredient, movement.ingredient_id).quantity -= movement.quantity
                    s.add(StockMovement(ingredient_id=movement.ingredient_id, order_id=order_id, quantity=-movement.quantity, reason='refund'))
            refund = Refund(order_id=order_id, user_id=actor, token=token or uuid4().hex, amount=paid,
                            revenue=order.subtotal-order.discount+order.service, cogs_reversal=order.cogs if restock else 0,
                            method=method, reason=reason, session_id=session_id)
            s.add(refund)
            s.flush()
            order.status = 'refunded'
            order.kitchen_status = 'completed'
            self._audit(s, actor, 'order.refunded', f'{order_id}: {reason}; restock={restock}')
            return refund.id

    def kitchen(self, actor, order_id, status):
        self.auth.require(actor, 'kitchen')
        next_status = {'new': 'preparing', 'preparing': 'ready', 'ready': 'completed'}
        with self.db.write() as s:
            order = self._order(s, order_id)
            if not order.confirmed_at or order.status == 'refunded' or next_status.get(order.kitchen_status) != status:
                raise ValueError('Invalid kitchen transition')
            order.kitchen_status, order.kitchen_updated_at = status, now()
            self._audit(s, actor, 'kitchen.' + status, order_id)

    def transfer(self, actor, order_id, table_id):
        self.auth.require(actor, 'tables')
        with self.db.write() as s:
            order = self._order(s, order_id)
            if order.status not in ('held', 'confirmed') or not s.get(RestaurantTable, table_id):
                raise ValueError('Select an open order and a valid table')
            if s.scalar(select(Order).where(Order.table_id == table_id, Order.status.in_(['held', 'confirmed']))):
                raise ValueError('Destination table occupied')
            order.table_id = table_id
            self._audit(s, actor, 'table.transfer', order_id)

    def open_drawer(self, actor, opening):
        self.auth.require(actor, 'pos')
        opening = units(opening)
        if opening < 0:
            raise ValueError('Opening cash cannot be negative')
        with self.db.write() as s:
            if s.scalar(select(CashSession).where(CashSession.user_id == actor, CashSession.closed_at.is_(None))):
                raise ValueError('A drawer is already open')
            drawer = CashSession(user_id=actor, opening=opening)
            s.add(drawer)
            self._audit(s, actor, 'drawer.open', opening)

    def close_drawer(self, actor, counted):
        from models.schema import Expense
        self.auth.require(actor, 'pos')
        counted = units(counted)
        if counted < 0:
            raise ValueError('Counted cash cannot be negative')
        with self.db.write() as s:
            drawer = self._session(s, actor)
            total = lambda cls: s.scalar(select(func.coalesce(func.sum(cls.amount), 0)).where(cls.session_id == drawer.id))
            drawer.expected = drawer.opening + total(Payment) - total(Refund) - total(Expense)
            drawer.counted, drawer.closed_at = counted, now()
            self._audit(s, actor, 'drawer.close', f'expected={drawer.expected}, counted={counted}')
            return counted - drawer.expected
