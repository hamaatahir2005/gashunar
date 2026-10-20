from decimal import Decimal
from uuid import uuid4
from sqlalchemy import select, func
from core.money import units
from services.orders import rounded
from models.schema import (Ingredient, Recipe, Product, StockMovement, Purchase, PurchaseItem, Supplier,
                           Expense, ExpenseCategory, AuditLog, Setting, Customer, Employee, Shift,
                           RestaurantTable, Reservation, CashSession, now)


class Operations:
    def __init__(self, db, auth):
        self.db, self.auth = db, auth

    def ingredient(self, actor, name, unit, cost, minimum='0'):
        self.auth.require(actor, 'inventory')
        if not name.strip() or not unit.strip() or min(units(cost), units(minimum)) < 0:
            raise ValueError('Invalid ingredient')
        with self.db.write() as s:
            obj = Ingredient(name=name.strip(), unit=unit, cost=units(cost), minimum=units(minimum))
            s.add(obj)
            s.flush()
            return obj.id

    def adjust_stock(self, actor, ingredient_id, quantity, reason):
        self.auth.require(actor, 'inventory')
        qty = units(quantity)
        if not reason.strip() or qty == 0:
            raise ValueError('Non-zero quantity and reason required')
        with self.db.write() as s:
            obj = s.get(Ingredient, ingredient_id)
            if not obj:
                raise ValueError('Ingredient not found')
            if obj.quantity + qty < 0 and s.get(Setting, 'prevent_negative_stock').value == 'true':
                raise ValueError('Insufficient stock')
            obj.quantity += qty
            s.add(StockMovement(ingredient_id=obj.id, quantity=qty, reason=reason))
            s.add(AuditLog(user_id=actor, action='stock.adjustment', detail=f'{ingredient_id}: {qty}; {reason}'))

    def recipe(self, actor, product_id, ingredient_id, quantity):
        self.auth.require(actor, 'inventory')
        qty = units(quantity)
        if qty <= 0:
            raise ValueError('Recipe quantity must be positive')
        with self.db.write() as s:
            if not s.get(Product, product_id) or not s.get(Ingredient, ingredient_id):
                raise ValueError('Product or ingredient not found')
            recipe = s.scalar(select(Recipe).where(Recipe.product_id == product_id, Recipe.ingredient_id == ingredient_id))
            if recipe:
                recipe.quantity = qty
            else:
                s.add(Recipe(product_id=product_id, ingredient_id=ingredient_id, quantity=qty))

    def purchase(self, actor, supplier_id, lines, paid='0', token=None):
        self.auth.require(actor, 'inventory')
        if not lines:
            raise ValueError('Purchase requires items')
        token = token or uuid4().hex
        with self.db.write() as s:
            existing = s.scalar(select(Purchase).where(Purchase.token == token))
            if existing:
                return existing.id
            if not s.get(Supplier, supplier_id):
                raise ValueError('Supplier not found')
            prepared = []
            for ingredient_id, quantity, unit_cost in lines:
                ingredient = s.get(Ingredient, ingredient_id)
                qty, cost = units(quantity), units(unit_cost)
                if not ingredient or qty <= 0 or cost < 0:
                    raise ValueError('Invalid purchase item')
                prepared.append((ingredient, qty, cost))
            total = sum(rounded(Decimal(qty) * cost / 1000) for _, qty, cost in prepared)
            paid_value = units(paid)
            if not 0 <= paid_value <= total:
                raise ValueError('Paid amount must be between zero and total')
            purchase = Purchase(supplier_id=supplier_id, token=token, total=total, paid=paid_value)
            s.add(purchase)
            s.flush()
            for ingredient, qty, cost in prepared:
                old = ingredient.quantity
                ingredient.cost = rounded((Decimal(max(old, 0)) * ingredient.cost + Decimal(qty) * cost) / (max(old, 0) + qty))
                ingredient.quantity += qty
                s.add(PurchaseItem(purchase_id=purchase.id, ingredient_id=ingredient.id, quantity=qty, unit_cost=cost))
                s.add(StockMovement(ingredient_id=ingredient.id, purchase_id=purchase.id, quantity=qty, reason='purchase'))
            s.add(AuditLog(user_id=actor, action='purchase.created', detail=str(purchase.id)))
            return purchase.id

    def expense(self, actor, category_id, amount, description, date, method='cash', expense_id=None):
        from datetime import date as Date
        self.auth.require(actor, 'expenses')
        Date.fromisoformat(date)
        value = units(amount)
        if value <= 0 or not description.strip() or method not in ('cash', 'card'):
            raise ValueError('Positive amount, description and payment method required')
        with self.db.write() as s:
            if not s.get(ExpenseCategory, category_id):
                raise ValueError('Expense category not found')
            session_id = None
            if method == 'cash':
                drawer = s.scalar(select(CashSession).where(CashSession.user_id == actor, CashSession.closed_at.is_(None)))
                if not drawer:
                    raise ValueError('Open a drawer for cash expenses')
                session_id = drawer.id
            obj = s.get(Expense, expense_id) if expense_id else Expense(user_id=actor)
            if not obj:
                raise ValueError('Expense not found')
            if expense_id and obj.session_id:
                old_drawer = s.get(CashSession, obj.session_id)
                if old_drawer.closed_at:
                    raise ValueError('Cannot edit an expense in a closed drawer')
            obj.category_id, obj.amount, obj.description = category_id, value, description
            obj.date, obj.method, obj.session_id = date, method, session_id
            s.add(obj)
            s.flush()
            s.add(AuditLog(user_id=actor, action='expense.saved', detail=str(obj.id)))
            return obj.id

    def customer(self, actor, name, phone='', address='', notes='', customer_id=None):
        self.auth.require(actor, 'customers')
        if not name.strip():
            raise ValueError('Name required')
        with self.db.write() as s:
            obj = s.get(Customer, customer_id) if customer_id else Customer()
            if not obj:
                raise ValueError('Customer not found')
            obj.name, obj.phone, obj.address, obj.notes = name.strip(), phone, address, notes
            s.add(obj)
            s.flush()
            return obj.id

    def table(self, actor, name, capacity, section='Main', table_id=None):
        self.auth.require(actor, 'tables')
        if not name.strip() or not 1 <= int(capacity) <= 100:
            raise ValueError('Name and capacity between 1 and 100 required')
        with self.db.write() as s:
            obj = s.get(RestaurantTable, table_id) if table_id else RestaurantTable()
            if not obj:
                raise ValueError('Table not found')
            obj.name, obj.capacity, obj.section = name.strip(), int(capacity), section
            s.add(obj)
            s.flush()
            return obj.id

    def reserve(self, actor, table_id, customer_id, starts_at, ends_at, guests):
        from datetime import datetime
        self.auth.require(actor, 'tables')
        if datetime.fromisoformat(starts_at) >= datetime.fromisoformat(ends_at):
            raise ValueError('End must be after start')
        with self.db.write() as s:
            table = s.get(RestaurantTable, table_id)
            if not table or not s.get(Customer, customer_id) or not 1 <= guests <= table.capacity:
                raise ValueError('Invalid reservation or table capacity exceeded')
            if s.scalar(select(Reservation).where(Reservation.table_id == table_id, Reservation.status == 'reserved', Reservation.starts_at < ends_at, Reservation.ends_at > starts_at)):
                raise ValueError('Reservation overlaps an existing reservation')
            s.add(Reservation(table_id=table_id, customer_id=customer_id, starts_at=starts_at, ends_at=ends_at, guests=guests))

    def attendance(self, actor, employee_id):
        self.auth.require(actor, 'employees')
        with self.db.write() as s:
            if not s.get(Employee, employee_id):
                raise ValueError('Employee not found')
            shift = s.scalar(select(Shift).where(Shift.employee_id == employee_id, Shift.ended_at.is_(None)))
            if shift:
                shift.ended_at = now()
            else:
                s.add(Shift(employee_id=employee_id))

    def supplier(self, actor, name, phone=''):
        self.auth.require(actor, 'inventory')
        if not name.strip():
            raise ValueError('Supplier name required')
        with self.db.write() as s:
            supplier = Supplier(name=name.strip(), phone=phone)
            s.add(supplier)
            s.flush()
            return supplier.id
