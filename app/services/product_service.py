from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.product_db import ProductDB


def get_products(tenant_id: int):
    db = SessionLocal()

    try:
        products = db.execute(
            select(ProductDB)
            .where(ProductDB.tenant_id == tenant_id)
            .order_by(ProductDB.name)
        ).scalars().all()

        return products

    finally:
        db.close()


def search_products(query: str, tenant_id: int):
    db = SessionLocal()

    try:
        products = db.execute(
            select(ProductDB)
            .where(
                ProductDB.tenant_id == tenant_id,
                ProductDB.name.ilike(f"%{query}%"),
            )
            .order_by(ProductDB.name)
        ).scalars().all()

        return products

    finally:
        db.close()


def get_product_by_id(product_id: int, tenant_id: int):
    db = SessionLocal()

    try:
        return db.scalar(
            select(ProductDB).where(
                ProductDB.id == product_id,
                ProductDB.tenant_id == tenant_id,
            )
        )

    finally:
        db.close()
