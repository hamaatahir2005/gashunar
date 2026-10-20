import csv
import uuid
from pathlib import Path
from decimal import Decimal
from PIL import Image, ImageOps
from sqlalchemy import select, or_
from core.money import units
from models.schema import Product, Category, ProductImage, AuditLog


class Catalog:
    def __init__(self, db, auth):
        self.db, self.auth = db, auth

    def list(self, actor, query='', category=None, offset=0, limit=100, archived=False):
        self.auth.require(actor, 'pos' if 'products' not in self.auth.actions(actor) and '*' not in self.auth.actions(actor) else 'products')
        with self.db.read() as s:
            q = select(Product).where(or_(Product.name.contains(query), Product.code.contains(query), Product.barcode == query))
            if not archived:
                q = q.where(Product.active.is_(True))
            if category:
                q = q.where(Product.category_id == category)
            return list(s.scalars(q.order_by(Product.sort, Product.name).offset(max(offset, 0)).limit(min(limit, 500))))

    def _prepare_image(self, source):
        if not source:
            return None
        source = Path(source)
        if not source.is_file() or source.stat().st_size > 15 * 1024 * 1024:
            raise ValueError('Choose an image smaller than 15 MB')
        folder = self.db.path.parent / 'images'
        folder.mkdir(exist_ok=True)
        target = folder / f'{uuid.uuid4().hex}.png'
        try:
            with Image.open(source) as image:
                if image.width * image.height > 30_000_000:
                    raise ValueError('Image resolution too large')
                image = ImageOps.exif_transpose(image).convert('RGB')
                image.thumbnail((1024, 1024))
                image.save(target, 'PNG')
        except Exception as exc:
            target.unlink(missing_ok=True)
            raise ValueError('Cannot load this image. Choose a PNG, JPEG or WebP image.') from exc
        return target

    def save(self, actor, name, code, price, cost='0', category='', barcode='', description='', product_id=None, image_path=None):
        self.auth.require(actor, 'products')
        if not name.strip() or not code.strip():
            raise ValueError('Name and product code are required')
        price, cost = units(price), units(cost)
        if min(price, cost) < 0:
            raise ValueError('Prices cannot be negative')
        prepared = self._prepare_image(image_path)
        try:
            with self.db.write() as s:
                cat = s.scalar(select(Category).where(Category.name == category.strip())) if category.strip() else None
                if category.strip() and not cat:
                    cat = Category(name=category.strip())
                    s.add(cat)
                    s.flush()
                product = s.get(Product, product_id) if product_id else Product()
                if not product:
                    raise ValueError('Product not found')
                product.name, product.code, product.price, product.cost = name.strip(), code.strip(), price, cost
                product.category_id, product.barcode, product.description = cat.id if cat else None, barcode.strip() or None, description
                s.add(product)
                s.flush()
                if prepared:
                    s.add(ProductImage(product_id=product.id, path=prepared.relative_to(self.db.path.parent).as_posix()))
                s.add(AuditLog(user_id=actor, action='product.saved', detail=str(product.id)))
                product_id = product.id
        except Exception:
            if prepared:
                prepared.unlink(missing_ok=True)
            raise
        return product_id

    def images(self, actor, product_ids):
        self.auth.require(actor, 'pos' if not ({'*','products'} & self.auth.actions(actor)) else 'products')
        with self.db.read() as s:
            result = {}
            for image in s.scalars(select(ProductImage).where(ProductImage.product_id.in_(product_ids)).order_by(ProductImage.id)):
                path = (self.db.path.parent / image.path).resolve()
                if path.is_relative_to(self.db.path.parent) and path.is_file():
                    result[image.product_id] = path
            return result

    def archive(self, actor, product_id):
        self.auth.require(actor, 'products')
        with self.db.write() as s:
            product = s.get(Product, product_id)
            if not product:
                raise ValueError('Product not found')
            product.active = False
            s.add(AuditLog(user_id=actor, action='product.archived', detail=str(product_id)))

    def image(self, actor, product_id, source):
        self.auth.require(actor, 'products')
        target = self._prepare_image(source)
        if target is None:
            raise ValueError('Choose an image')
        try:
            with self.db.write() as s:
                if not s.get(Product, product_id):
                    raise ValueError('Product not found')
                s.add(ProductImage(product_id=product_id, path=target.relative_to(self.db.path.parent).as_posix()))
                s.add(AuditLog(user_id=actor, action='product.image', detail=str(product_id)))
        except Exception:
            target.unlink(missing_ok=True)
            raise
        return target

    def export_csv(self, actor, path):
        self.auth.require(actor, 'products')
        with self.db.read() as s, open(path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'code', 'price', 'cost', 'barcode', 'description'])
            for p in s.scalars(select(Product).order_by(Product.id)):
                # Prefix spreadsheet formulas; values remain readable when importing.
                safe = lambda v: "'" + v if v.startswith(('=', '+', '-', '@')) else v
                writer.writerow([safe(p.name), safe(p.code), str(Decimal(p.price) / 1000), str(Decimal(p.cost) / 1000), safe(p.barcode or ''), safe(p.description)])

    def import_csv(self, actor, path):
        self.auth.require(actor, 'products')
        with open(path, encoding='utf-8-sig', newline='') as f:
            rows = list(csv.DictReader(f))
        if len(rows) > 10000:
            raise ValueError('Maximum 10,000 products per import')
        with self.db.write() as s:
            for row in rows:
                name, code = row['name'].strip(), row['code'].strip()
                price, cost = units(row['price']), units(row.get('cost') or '0')
                if not name or not code or min(price, cost) < 0:
                    raise ValueError('Invalid product import row')
                s.add(Product(name=name, code=code, price=price, cost=cost, barcode=row.get('barcode') or None, description=row.get('description') or ''))
            s.add(AuditLog(user_id=actor, action='products.import', detail=str(len(rows))))
        return len(rows)
