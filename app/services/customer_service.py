from sqlalchemy import select

from app.core import database as database_module
from app.models.customer_db import CustomerDB
from app.models.customer_identity_db import CustomerIdentityDB


class CustomerService:

    # ========================================================
    # BUSCAR CLIENTE POR IDENTIDAD EXTERNA
    # ========================================================

    def get_customer_by_identity(
        self,
        tenant_id: int,
        channel: str,
        external_id: str,
    ) -> CustomerDB | None:

        normalized_channel = (
            channel.strip().lower()
        )

        normalized_external_id = (
            external_id.strip()
        )

        if not normalized_channel:
            return None

        if not normalized_external_id:
            return None

        db = database_module.SessionLocal()

        try:

            identity = db.scalar(
                select(CustomerIdentityDB)
                .where(
                    CustomerIdentityDB.tenant_id
                    == tenant_id,
                    CustomerIdentityDB.channel
                    == normalized_channel,
                    CustomerIdentityDB.external_id
                    == normalized_external_id,
                )
            )

            if identity is None:
                return None

            return db.scalar(
                select(CustomerDB)
                .where(
                    CustomerDB.id
                    == identity.customer_id,
                    CustomerDB.tenant_id
                    == tenant_id,
                    CustomerDB.active.is_(True),
                )
            )

        finally:

            db.close()

    # ========================================================
    # CREAR CLIENTE
    # ========================================================

    def create_customer(
        self,
        tenant_id: int,
        name: str,
        phone: str | None = None,
        email: str | None = None,
    ) -> CustomerDB:

        normalized_name = name.strip()

        if not normalized_name:

            raise ValueError(
                "El nombre del cliente es obligatorio."
            )

        db = database_module.SessionLocal()

        try:

            customer = CustomerDB(
                tenant_id=tenant_id,
                name=normalized_name,
                phone=(
                    phone.strip()
                    if phone
                    else None
                ),
                email=(
                    email.strip().lower()
                    if email
                    else None
                ),
                active=True,
            )

            db.add(customer)

            db.commit()

            db.refresh(customer)

            return customer

        except Exception:

            db.rollback()

            raise

        finally:

            db.close()

    # ========================================================
    # CREAR O VINCULAR IDENTIDAD
    # ========================================================

    def create_identity(
        self,
        tenant_id: int,
        customer_id: int,
        channel: str,
        external_id: str,
    ) -> CustomerIdentityDB:

        normalized_channel = (
            channel.strip().lower()
        )

        normalized_external_id = (
            external_id.strip()
        )

        if not normalized_channel:

            raise ValueError(
                "El canal de identidad es obligatorio."
            )

        if not normalized_external_id:

            raise ValueError(
                "El identificador externo es obligatorio."
            )

        db = database_module.SessionLocal()

        try:

            customer = db.scalar(
                select(CustomerDB)
                .where(
                    CustomerDB.id
                    == customer_id,
                    CustomerDB.tenant_id
                    == tenant_id,
                )
            )

            if customer is None:

                raise ValueError(
                    "El cliente no existe "
                    "dentro del tenant."
                )

            existing_identity = db.scalar(
                select(CustomerIdentityDB)
                .where(
                    CustomerIdentityDB.tenant_id
                    == tenant_id,
                    CustomerIdentityDB.channel
                    == normalized_channel,
                    CustomerIdentityDB.external_id
                    == normalized_external_id,
                )
            )

            if existing_identity is not None:

                if (
                    existing_identity.customer_id
                    != customer_id
                ):

                    raise ValueError(
                        "La identidad ya está "
                        "vinculada a otro cliente."
                    )

                return existing_identity

            identity = CustomerIdentityDB(
                tenant_id=tenant_id,
                customer_id=customer_id,
                channel=normalized_channel,
                external_id=normalized_external_id,
            )

            db.add(identity)

            db.commit()

            db.refresh(identity)

            return identity

        except Exception:

            db.rollback()

            raise

        finally:

            db.close()

    # ========================================================
    # OBTENER O CREAR CLIENTE POR IDENTIDAD
    # ========================================================

    def get_or_create_customer(
        self,
        tenant_id: int,
        channel: str,
        external_id: str,
        name: str,
        phone: str | None = None,
        email: str | None = None,
    ) -> CustomerDB:

        existing_customer = (
            self.get_customer_by_identity(
                tenant_id=tenant_id,
                channel=channel,
                external_id=external_id,
            )
        )

        if existing_customer is not None:

            return existing_customer

        customer = self.create_customer(
            tenant_id=tenant_id,
            name=name,
            phone=phone,
            email=email,
        )

        try:

            self.create_identity(
                tenant_id=tenant_id,
                customer_id=customer.id,
                channel=channel,
                external_id=external_id,
            )

        except Exception:

            db = database_module.SessionLocal()

            try:

                existing_identity = db.scalar(
                    select(CustomerIdentityDB)
                    .where(
                        CustomerIdentityDB.tenant_id
                        == tenant_id,
                        CustomerIdentityDB.channel
                        == channel.strip().lower(),
                        CustomerIdentityDB.external_id
                        == external_id.strip(),
                    )
                )

                if existing_identity is not None:

                    if (
                        existing_identity.customer_id
                        != customer.id
                    ):

                        db.delete(customer)

                        db.commit()

                        raise ValueError(
                            "La identidad ya está "
                            "vinculada a otro cliente."
                        )

                    db.delete(customer)

                    db.commit()

                    existing_customer = db.scalar(
                        select(CustomerDB)
                        .where(
                            CustomerDB.id
                            == existing_identity.customer_id,
                            CustomerDB.tenant_id
                            == tenant_id,
                            CustomerDB.active.is_(True),
                        )
                    )

                    if existing_customer is not None:

                        return existing_customer

                db.rollback()

            finally:

                db.close()

            raise

        return customer


# ============================================================
# INSTANCIA GLOBAL
# ============================================================

customer_service = CustomerService()


__all__ = [
    "CustomerService",
    "customer_service",
]