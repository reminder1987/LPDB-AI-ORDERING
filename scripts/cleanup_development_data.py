from __future__ import annotations

import argparse

from sqlalchemy import delete, select

from app.core.database import SessionLocal
from app.models.channel_integration_db import ChannelIntegrationDB
from app.models.conversation_session_db import ConversationSessionDB
from app.models.customer_db import CustomerDB
from app.models.customer_identity_db import CustomerIdentityDB
from app.models.external_mapping_db import ExternalMappingDB
from app.models.order_db import OrderDB
from app.models.order_item_combo_db import OrderItemComboDB
from app.models.order_item_db import OrderItemDB
from app.models.order_item_modification_db import OrderItemModificationDB


TENANT_ID = 1
KEEP_CHANNEL = ("whatsapp", "meta", "submission-e2e-business-001")


def collect_counts(db):
    orders = db.execute(
        select(OrderDB.id).where(OrderDB.tenant_id == TENANT_ID)
    ).scalars().all()

    customers = db.execute(
        select(CustomerDB.id).where(CustomerDB.tenant_id == TENANT_ID)
    ).scalars().all()

    sessions = db.execute(
        select(ConversationSessionDB.id).where(
            ConversationSessionDB.tenant_id == TENANT_ID
        )
    ).scalars().all()

    identities = db.execute(
        select(CustomerIdentityDB.id).where(
            CustomerIdentityDB.tenant_id == TENANT_ID
        )
    ).scalars().all()

    mappings = db.execute(
        select(ExternalMappingDB.id).where(
            ExternalMappingDB.tenant_id == TENANT_ID
        )
    ).scalars().all()

    return {
        "orders": len(orders),
        "customers": len(customers),
        "sessions": len(sessions),
        "identities": len(identities),
        "mappings": len(mappings),
    }


def dry_run():
    db = SessionLocal()

    try:
        counts = collect_counts(db)

        print("=== CLEANUP DRY RUN ===")
        print(f"Tenant: {TENANT_ID}")
        print()
        print("SE ELIMINARIAN:")
        print(f"  Orders:              {counts['orders']}")
        print(f"  Customers:           {counts['customers']}")
        print(f"  Conversations:       {counts['sessions']}")
        print(f"  Customer identities: {counts['identities']}")
        print(f"  External mappings:   {counts['mappings']}")
        print()
        print("SE CONSERVARAN:")
        print("  Tenant LPDB")
        print("  Productos")
        print("  Ingredientes")
        print("  Categorias")
        print("  Recetas")
        print("  Sedes")
        print("  Horarios")
        print("  Disponibilidad")
        print(f"  WhatsApp: {KEEP_CHANNEL}")
        print()
        print("NO SE HA BORRADO NADA.")

    finally:
        db.close()


def cleanup():
    db = SessionLocal()

    try:
        print("=== EXECUTING CLEANUP ===")

        order_ids = db.execute(
            select(OrderDB.id).where(OrderDB.tenant_id == TENANT_ID)
        ).scalars().all()

        customer_ids = db.execute(
            select(CustomerDB.id).where(CustomerDB.tenant_id == TENANT_ID)
        ).scalars().all()

        session_ids = db.execute(
            select(ConversationSessionDB.id).where(
                ConversationSessionDB.tenant_id == TENANT_ID
            )
        ).scalars().all()

        identity_ids = db.execute(
            select(CustomerIdentityDB.id).where(
                CustomerIdentityDB.tenant_id == TENANT_ID
            )
        ).scalars().all()

        print(f"Orders found: {len(order_ids)}")
        print(f"Customers found: {len(customer_ids)}")
        print(f"Sessions found: {len(session_ids)}")
        print(f"Identities found: {len(identity_ids)}")

        if order_ids:
            item_ids = db.execute(
                select(OrderItemDB.id).where(
                    OrderItemDB.order_id.in_(order_ids)
                )
            ).scalars().all()

            if item_ids:
                db.execute(
                    delete(OrderItemComboDB).where(
                        OrderItemComboDB.order_item_id.in_(item_ids)
                    )
                )

                db.execute(
                    delete(OrderItemModificationDB).where(
                        OrderItemModificationDB.order_item_id.in_(item_ids)
                    )
                )

                db.execute(
                    delete(OrderItemDB).where(
                        OrderItemDB.id.in_(item_ids)
                    )
                )

            db.execute(
                delete(OrderDB).where(
                    OrderDB.id.in_(order_ids)
                )
            )

        if session_ids:
            db.execute(
                delete(ConversationSessionDB).where(
                    ConversationSessionDB.id.in_(session_ids)
                )
            )

        if identity_ids:
            db.execute(
                delete(CustomerIdentityDB).where(
                    CustomerIdentityDB.id.in_(identity_ids)
                )
            )

        if customer_ids:
            db.execute(
                delete(CustomerDB).where(
                    CustomerDB.id.in_(customer_ids)
                )
            )

        db.execute(
            delete(ExternalMappingDB).where(
                ExternalMappingDB.tenant_id == TENANT_ID
            )
        )

        db.execute(
            delete(ChannelIntegrationDB).where(
                ChannelIntegrationDB.tenant_id == TENANT_ID,
                ChannelIntegrationDB.channel != KEEP_CHANNEL[0],
            )
        )

        db.commit()

        print()
        print("CLEANUP COMPLETED.")
        print("Transaction committed successfully.")

    except Exception:
        db.rollback()
        print()
        print("ERROR: rollback executed.")
        raise

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without modifying the database.",
    )

    args = parser.parse_args()

    if args.dry_run:
        dry_run()
    else:
        cleanup()


if __name__ == "__main__":
    main()