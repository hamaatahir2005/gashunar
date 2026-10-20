from datetime import datetime, timezone
from sqlalchemy import (Boolean, CheckConstraint, ForeignKey, Index, Integer, String, Text, UniqueConstraint)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds')


class Base(DeclarativeBase):
    pass


class Role(Base):
    __tablename__ = 'roles'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)


class Permission(Base):
    __tablename__ = 'permissions'
    id: Mapped[int] = mapped_column(primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey('roles.id'))
    action: Mapped[str]
    __table_args__ = (UniqueConstraint('role_id', 'action'),)


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]
    role_id: Mapped[int] = mapped_column(ForeignKey('roles.id'))
    active: Mapped[bool] = mapped_column(default=True)
    failed_logins: Mapped[int] = mapped_column(default=0)
    locked_until: Mapped[str] = mapped_column(default='')


class Employee(Base):
    __tablename__ = 'employees'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), unique=True)
    name: Mapped[str]
    phone: Mapped[str] = mapped_column(default='')
    salary: Mapped[int] = mapped_column(default=0)


class Shift(Base):
    __tablename__ = 'shifts'
    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey('employees.id'))
    started_at: Mapped[str] = mapped_column(default=now)
    ended_at: Mapped[str | None]


class Customer(Base):
    __tablename__ = 'customers'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    phone: Mapped[str] = mapped_column(default='', index=True)
    address: Mapped[str] = mapped_column(default='')
    notes: Mapped[str] = mapped_column(default='')


class Category(Base):
    __tablename__ = 'categories'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    sort: Mapped[int] = mapped_column(default=0)


class Product(Base):
    __tablename__ = 'products'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    code: Mapped[str] = mapped_column(unique=True)
    barcode: Mapped[str | None] = mapped_column(unique=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey('categories.id'))
    description: Mapped[str] = mapped_column(default='')
    price: Mapped[int]
    cost: Mapped[int] = mapped_column(default=0)
    active: Mapped[bool] = mapped_column(default=True)
    preparation_minutes: Mapped[int] = mapped_column(default=10)
    sort: Mapped[int] = mapped_column(default=0)
    __table_args__ = (CheckConstraint('price >= 0 AND cost >= 0'), Index('ix_product_active_name', 'active', 'name'))


class ProductImage(Base):
    __tablename__ = 'product_images'
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    path: Mapped[str]


class ProductVariant(Base):
    __tablename__ = 'product_variants'
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    name: Mapped[str]
    price: Mapped[int]


class Modifier(Base):
    __tablename__ = 'modifiers'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    price: Mapped[int]


class RestaurantTable(Base):
    __tablename__ = 'restaurant_tables'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    section: Mapped[str] = mapped_column(default='Main')
    capacity: Mapped[int] = mapped_column(default=4)
    x: Mapped[int] = mapped_column(default=0)
    y: Mapped[int] = mapped_column(default=0)


class Reservation(Base):
    __tablename__ = 'reservations'
    id: Mapped[int] = mapped_column(primary_key=True)
    table_id: Mapped[int] = mapped_column(ForeignKey('restaurant_tables.id'))
    customer_id: Mapped[int] = mapped_column(ForeignKey('customers.id'))
    starts_at: Mapped[str]
    ends_at: Mapped[str]
    guests: Mapped[int] = mapped_column(default=1)
    status: Mapped[str] = mapped_column(default='reserved')


class Order(Base):
    __tablename__ = 'orders'
    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    customer_id: Mapped[int | None] = mapped_column(ForeignKey('customers.id'))
    table_id: Mapped[int | None] = mapped_column(ForeignKey('restaurant_tables.id'))
    kind: Mapped[str] = mapped_column(default='takeaway')
    status: Mapped[str] = mapped_column(default='held', index=True)
    kitchen_status: Mapped[str] = mapped_column(default='new')
    priority: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[str] = mapped_column(default=now, index=True)
    confirmed_at: Mapped[str | None] = mapped_column(index=True)
    kitchen_updated_at: Mapped[str] = mapped_column(default=now)
    notes: Mapped[str] = mapped_column(default='')
    subtotal: Mapped[int] = mapped_column(default=0)
    discount: Mapped[int] = mapped_column(default=0)
    tax: Mapped[int] = mapped_column(default=0)
    service: Mapped[int] = mapped_column(default=0)
    total: Mapped[int] = mapped_column(default=0)
    cogs: Mapped[int] = mapped_column(default=0)


class OrderItem(Base):
    __tablename__ = 'order_items'
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id'), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    name: Mapped[str]
    quantity: Mapped[int]
    price: Mapped[int]
    cost: Mapped[int]
    notes: Mapped[str] = mapped_column(default='')
    __table_args__ = (CheckConstraint('quantity > 0 AND price >= 0 AND cost >= 0'),)


class OrderItemModifier(Base):
    __tablename__ = 'order_item_modifiers'
    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey('order_items.id'))
    modifier_id: Mapped[int] = mapped_column(ForeignKey('modifiers.id'))
    name: Mapped[str]
    price: Mapped[int]


class CashSession(Base):
    __tablename__ = 'cash_drawer_sessions'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    opened_at: Mapped[str] = mapped_column(default=now)
    closed_at: Mapped[str | None]
    opening: Mapped[int] = mapped_column(default=0)
    counted: Mapped[int | None]
    expected: Mapped[int | None]


class Payment(Base):
    __tablename__ = 'payments'
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id'), index=True)
    session_id: Mapped[int | None] = mapped_column(ForeignKey('cash_drawer_sessions.id'))
    token: Mapped[str] = mapped_column(unique=True)
    method: Mapped[str]
    amount: Mapped[int]
    created_at: Mapped[str] = mapped_column(default=now, index=True)
    __table_args__ = (CheckConstraint('amount > 0'),)


class Refund(Base):
    __tablename__ = 'refunds'
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id'), unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    session_id: Mapped[int | None] = mapped_column(ForeignKey('cash_drawer_sessions.id'))
    token: Mapped[str] = mapped_column(unique=True)
    amount: Mapped[int]
    revenue: Mapped[int]
    cogs_reversal: Mapped[int]
    method: Mapped[str]
    reason: Mapped[str]
    created_at: Mapped[str] = mapped_column(default=now, index=True)


class Invoice(Base):
    __tablename__ = 'invoices'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id'), unique=True)
    number: Mapped[str] = mapped_column(unique=True)
    __table_args__ = {'sqlite_autoincrement': True}


class Ingredient(Base):
    __tablename__ = 'ingredients'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    unit: Mapped[str] = mapped_column(default='g')
    quantity: Mapped[int] = mapped_column(default=0)  # thousandths of unit
    cost: Mapped[int] = mapped_column(default=0)  # money per unit
    minimum: Mapped[int] = mapped_column(default=0)


class Recipe(Base):
    __tablename__ = 'recipes'
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    ingredient_id: Mapped[int] = mapped_column(ForeignKey('ingredients.id'))
    quantity: Mapped[int]
    __table_args__ = (UniqueConstraint('product_id', 'ingredient_id'), CheckConstraint('quantity > 0'))


class StockMovement(Base):
    __tablename__ = 'stock_movements'
    id: Mapped[int] = mapped_column(primary_key=True)
    ingredient_id: Mapped[int] = mapped_column(ForeignKey('ingredients.id'), index=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey('orders.id'))
    purchase_id: Mapped[int | None] = mapped_column(ForeignKey('purchases.id'))
    quantity: Mapped[int]
    reason: Mapped[str]
    created_at: Mapped[str] = mapped_column(default=now)


class Supplier(Base):
    __tablename__ = 'suppliers'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    phone: Mapped[str] = mapped_column(default='')


class Purchase(Base):
    __tablename__ = 'purchases'
    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey('suppliers.id'))
    token: Mapped[str] = mapped_column(unique=True)
    total: Mapped[int]
    paid: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[str] = mapped_column(default=now)


class PurchaseItem(Base):
    __tablename__ = 'purchase_items'
    id: Mapped[int] = mapped_column(primary_key=True)
    purchase_id: Mapped[int] = mapped_column(ForeignKey('purchases.id'))
    ingredient_id: Mapped[int] = mapped_column(ForeignKey('ingredients.id'))
    quantity: Mapped[int]
    unit_cost: Mapped[int]


class ExpenseCategory(Base):
    __tablename__ = 'expense_categories'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)


class Expense(Base):
    __tablename__ = 'expenses'
    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey('expense_categories.id'))
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    session_id: Mapped[int | None] = mapped_column(ForeignKey('cash_drawer_sessions.id'))
    amount: Mapped[int]
    description: Mapped[str]
    method: Mapped[str] = mapped_column(default='cash')
    date: Mapped[str] = mapped_column(index=True)
    receipt: Mapped[str] = mapped_column(default='')
    __table_args__ = (CheckConstraint('amount > 0'),)


class LoyaltyTransaction(Base):
    __tablename__ = 'loyalty_transactions'
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey('customers.id'))
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id'))
    points: Mapped[int]
    __table_args__ = (UniqueConstraint('order_id'),)


class Setting(Base):
    __tablename__ = 'settings'
    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[str]


class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'))
    action: Mapped[str]
    detail: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(default=now)


class BackupHistory(Base):
    __tablename__ = 'backup_history'
    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str]
    sha256: Mapped[str]
    created_at: Mapped[str] = mapped_column(default=now)
