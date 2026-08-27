from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

from app.core.database import database_url
from app.models.base import Base

# ============================================================
# MODELOS
# ============================================================

from app.models.category_db import (
    ProductCategoryDB,
    IngredientCategoryDB,
)

from app.models.conversation_session_db import (
    ConversationSessionDB,
)

from app.models.ingredient_db import IngredientDB
from app.models.order_db import OrderDB
from app.models.order_item_db import OrderItemDB
from app.models.order_item_combo_db import OrderItemComboDB
from app.models.order_item_modification_db import OrderItemModificationDB
from app.models.product_availability_db import ProductAvailabilityDB
from app.models.product_db import ProductDB
from app.models.recipe_db import (
    RecipeDB,
    RecipeIngredientDB,
)
from app.models.tenant_db import TenantDB


# ============================================================
# CONFIGURACIÓN ALEMBIC
# ============================================================

config = context.config


if config.config_file_name is not None:
    fileConfig(
        config.config_file_name,
    )


# ============================================================
# METADATA
# ============================================================

target_metadata = Base.metadata


# ============================================================
# MIGRACIÓN OFFLINE
# ============================================================

def run_migrations_offline() -> None:
    """Run migrations in offline mode."""

    url = database_url.render_as_string(
        hide_password=False,
    )

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
    )

    with context.begin_transaction():
        context.run_migrations()


# ============================================================
# MIGRACIÓN ONLINE
# ============================================================

def run_migrations_online() -> None:
    """Run migrations in online mode."""

    connectable = engine_from_config(
        {
            "sqlalchemy.url": (
                database_url.render_as_string(
                    hide_password=False,
                )
            )
        },
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# ============================================================
# ENTRY POINT
# ============================================================

if context.is_offline_mode():

    run_migrations_offline()

else:

    run_migrations_online()
