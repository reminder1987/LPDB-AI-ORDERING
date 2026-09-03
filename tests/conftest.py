import pytest

from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core import database as database_module

from app.models.base import Base
from app.models.category_db import (
    IngredientCategoryDB,
    ProductCategoryDB,
)
from app.models.ingredient_db import IngredientDB
from app.models.location_db import LocationDB
from app.models.product_availability_db import (
    ProductAvailabilityDB,
)
from app.models.product_db import ProductDB
from app.models.recipe_db import (
    RecipeDB,
    RecipeIngredientDB,
)
from app.models.tenant_db import TenantDB

from app.services import conversation_service
from app.services import customer_service
from app.services import location_service
from app.services import order_service
from app.services import recipe_service
from app.services import tenant_service


TEST_DATABASE_URL = "sqlite:///./test_lpdb.sqlite"


engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
)


TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture(autouse=True)
def setup_test_database(monkeypatch):

    # --------------------------------------------------------
    # CREAR TODAS LAS TABLAS DE PRUEBA
    # --------------------------------------------------------

    Base.metadata.create_all(
        bind=engine,
    )

    # --------------------------------------------------------
    # USAR SQLITE DE PRUEBAS EN TODOS LOS SERVICIOS
    # --------------------------------------------------------

    monkeypatch.setattr(
        order_service,
        "SessionLocal",
        TestingSessionLocal,
    )

    monkeypatch.setattr(
        conversation_service,
        "SessionLocal",
        TestingSessionLocal,
    )

    monkeypatch.setattr(
        location_service,
        "SessionLocal",
        TestingSessionLocal,
    )

    monkeypatch.setattr(
        tenant_service,
        "SessionLocal",
        TestingSessionLocal,
    )

    monkeypatch.setattr(
        recipe_service,
        "SessionLocal",
        TestingSessionLocal,
    )

    # --------------------------------------------------------
    # CUSTOMER SERVICE
    #
    # customer_service importa SessionLocal desde
    # app.core.database.
    #
    # Por eso se parchea la fuente real.
    # --------------------------------------------------------

    monkeypatch.setattr(
        database_module,
        "SessionLocal",
        TestingSessionLocal,
    )

    # --------------------------------------------------------
    # DATOS BASE DE PRUEBA
    # --------------------------------------------------------

    db = TestingSessionLocal()

    try:

        # ====================================================
        # TENANT
        # ====================================================

        tenant = TenantDB(
            id=1,
            slug="lpdb",
            name="Los Perritos Del Barrio",
            active=True,
        )

        db.add(tenant)
        db.flush()

        # ====================================================
        # CATEGORÍAS DE PRODUCTO
        # ====================================================

        hot_dogs_category = ProductCategoryDB(
            id=1,
            tenant_id=tenant.id,
            name="HOT DOGS",
        )

        perros_category = ProductCategoryDB(
            id=2,
            tenant_id=tenant.id,
            name="PERROS",
        )

        hamburguesas_category = ProductCategoryDB(
            id=3,
            tenant_id=tenant.id,
            name="HAMBURGUESAS",
        )

        db.add_all(
            [
                hot_dogs_category,
                perros_category,
                hamburguesas_category,
            ]
        )

        db.flush()

        # ====================================================
        # CATEGORÍA DE INGREDIENTES
        # ====================================================

        toppings_category = IngredientCategoryDB(
            id=1,
            tenant_id=tenant.id,
            name="TOPPINGS",
        )

        db.add(
            toppings_category,
        )

        db.flush()

        # ====================================================
        # SEDES
        # ====================================================

        dirty_rabbit = LocationDB(
            id=1,
            tenant_id=tenant.id,
            customer_name="Dirty Rabbit",
            toast_name="Dirty Rabbit",
            city="Wynwood, Miami",
            address="Test Address 1",
            active=True,
        )

        wynwood_location = LocationDB(
            id=2,
            tenant_id=tenant.id,
            customer_name="Wynwood LPDB",
            toast_name="Wynwood LPDB",
            city="Wynwood, Miami",
            address="Test Address 2",
            active=True,
        )

        sunrise = LocationDB(
            id=3,
            tenant_id=tenant.id,
            customer_name="SUNRISE",
            toast_name="SUNRISE",
            city="Fort Lauderdale",
            address="Test Address 3",
            active=True,
        )

        db.add_all(
            [
                dirty_rabbit,
                wynwood_location,
                sunrise,
            ]
        )

        db.flush()

        # ====================================================
        # PRODUCTOS
        # ====================================================

        pizza = ProductDB(
            id=1,
            tenant_id=tenant.id,
            name="Pizza",
            category_id=hot_dogs_category.id,
            price=Decimal("9.99"),
        )

        perro_del_barrio = ProductDB(
            id=2,
            tenant_id=tenant.id,
            name="PERRO DEL BARRIO",
            category_id=perros_category.id,
            price=Decimal("9.99"),
        )

        hamburguesa = ProductDB(
            id=3,
            tenant_id=tenant.id,
            name="Hamburguesa",
            category_id=hamburguesas_category.id,
            price=Decimal("9.99"),
        )

        db.add_all(
            [
                pizza,
                perro_del_barrio,
                hamburguesa,
            ]
        )

        db.flush()

        # ====================================================
        # INGREDIENTE
        # ====================================================

        tocineta = IngredientDB(
            id=1,
            tenant_id=tenant.id,
            name="TOCINETA",
            category_id=toppings_category.id,
        )

        db.add(
            tocineta,
        )

        db.flush()

        # ====================================================
        # RECETA DE PERRO DEL BARRIO
        # ====================================================

        recipe = RecipeDB(
            id=1,
            product_id=perro_del_barrio.id,
        )

        db.add(
            recipe,
        )

        db.flush()

        recipe_tocineta = RecipeIngredientDB(
            recipe_id=recipe.id,
            ingredient_id=tocineta.id,
        )

        db.add(
            recipe_tocineta,
        )

        # ====================================================
        # DISPONIBILIDAD DE PRODUCTOS
        # ====================================================

        pizza_availability = ProductAvailabilityDB(
            product_id=pizza.id,
            location_id=dirty_rabbit.id,
            available=True,
            manual_override=False,
            source="LOCAL",
            reason=None,
        )

        perro_availability = ProductAvailabilityDB(
            product_id=perro_del_barrio.id,
            location_id=dirty_rabbit.id,
            available=True,
            manual_override=False,
            source="LOCAL",
            reason=None,
        )

        hamburguesa_availability = ProductAvailabilityDB(
            product_id=hamburguesa.id,
            location_id=dirty_rabbit.id,
            available=True,
            manual_override=False,
            source="LOCAL",
            reason=None,
        )

        db.add_all(
            [
                pizza_availability,
                perro_availability,
                hamburguesa_availability,
            ]
        )

        db.commit()

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()

    yield

    # --------------------------------------------------------
    # LIMPIAR DATOS DESPUÉS DE CADA TEST
    # --------------------------------------------------------

    Base.metadata.drop_all(
        bind=engine,
    )