from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.product_db import ProductDB


def get_products():
    db = SessionLocal()

    try:
        products = db.execute(
            select(ProductDB).order_by(ProductDB.name)
        ).scalars().all()

        return products

    finally:
        db.close()


def search_products(query: str):
    db = SessionLocal()

    try:
        products = db.execute(
            select(ProductDB)
            .where(ProductDB.name.ilike(f"%{query}%"))
            .order_by(ProductDB.name)
        ).scalars().all()

        return products

    finally:
        db.close()


def get_product_by_id(product_id: int):
    db = SessionLocal()

    try:
        return db.scalar(
            select(ProductDB).where(
                ProductDB.id == product_id
            )
        )

    finally:
        db.close()