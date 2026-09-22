from decimal import Decimal
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.core.database import SessionLocal
from app.core.payment_status import (
    PAYMENT_STATUS_PENDING,
    PAYMENT_STATUS_PROCESSING,
    is_valid_payment_status,
    transition_payment_status,
)
from app.models.order_db import OrderDB
from app.models.payment_db import PaymentDB
from app.models.tenant_db import TenantDB
from app.services.price_service import money


class PaymentNotFoundError(ValueError):
    pass


class PaymentTenantMismatchError(ValueError):
    pass


class PaymentOrderNotFoundError(ValueError):
    pass


class PaymentOrderPricingUnavailableError(ValueError):
    pass


class PaymentDuplicateError(ValueError):
    pass


class PaymentService:
    """
    Servicio interno para administrar pagos.

    Todas las operaciones estÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡n aisladas por tenant.

    El monto de un pago siempre se obtiene del snapshot
    monetario persistido en la orden.

    Este servicio no contiene lÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â³gica especÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â­fica de Stripe,
    Wompi u otro proveedor externo.
    """

    def create_payment(
        self,
        *,
        tenant_id: int,
        order_id: int,
        provider: str,
        currency: str = "USD",
        external_id: str | None = None,
        status: str = PAYMENT_STATUS_PENDING,
    ) -> PaymentDB:
        normalized_provider = self._normalize_provider(
            provider,
        )

        normalized_currency = self._normalize_currency(
            currency,
        )

        normalized_external_id = self._normalize_optional_external_id(
            external_id,
        )

        if not is_valid_payment_status(status):
            raise ValueError(
                f"Estado de pago no vÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡lido: {status}"
            )

        db = SessionLocal()

        try:
            tenant = db.get(
                TenantDB,
                tenant_id,
            )

            if tenant is None or not tenant.active:
                raise ValueError(
                    "Tenant no encontrado o inactivo."
                )

            order = db.scalar(
                select(OrderDB).where(
                    OrderDB.id == order_id,
                    OrderDB.tenant_id == tenant_id,
                )
            )

            if order is None:
                raise PaymentOrderNotFoundError(
                    "La orden no existe para este tenant."
                )

            if order.total is None:
                raise PaymentOrderPricingUnavailableError(
                    "La orden no tiene un snapshot monetario "
                    "persistido y no puede generar un pago."
                )

            normalized_amount = money(
                Decimal(str(order.total))
            )

            if normalized_amount <= Decimal("0.00"):
                raise PaymentOrderPricingUnavailableError(
                    "El snapshot monetario de la orden "
                    "debe ser mayor que cero."
                )

            if normalized_external_id is not None:
                existing_payment = db.scalar(
                    select(PaymentDB).where(
                        PaymentDB.tenant_id == tenant_id,
                        PaymentDB.provider
                        == normalized_provider,
                        PaymentDB.external_id
                        == normalized_external_id,
                    )
                )

                if existing_payment is not None:
                    raise PaymentDuplicateError(
                        "El identificador externo de pago "
                        "ya estÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡ registrado para este tenant "
                        "y proveedor."
                    )

            payment = PaymentDB(
                tenant_id=tenant_id,
                order_id=order_id,
                provider=normalized_provider,
                external_id=normalized_external_id,
                amount=normalized_amount,
                currency=normalized_currency,
                status=status,
            )

            db.add(payment)

            try:
                db.commit()

            except IntegrityError as exc:
                db.rollback()

                raise PaymentDuplicateError(
                    "No fue posible crear el pago porque "
                    "la identidad externa ya existe."
                ) from exc

            db.refresh(payment)
            db.expunge(payment)

            return payment

        finally:
            db.close()

    def get_payment(
        self,
        *,
        tenant_id: int,
        payment_id: int,
    ) -> PaymentDB:
        db = SessionLocal()

        try:
            payment = db.scalar(
                select(PaymentDB).where(
                    PaymentDB.id == payment_id,
                    PaymentDB.tenant_id == tenant_id,
                )
            )

            if payment is None:
                raise PaymentNotFoundError(
                    "Pago no encontrado."
                )

            db.expunge(payment)

            return payment

        finally:
            db.close()

    def get_payment_by_external_id(
        self,
        *,
        tenant_id: int,
        provider: str,
        external_id: str,
    ) -> PaymentDB:
        normalized_provider = self._normalize_provider(
            provider,
        )

        normalized_external_id = self._normalize_required_external_id(
            external_id,
        )

        db = SessionLocal()

        try:
            payment = db.scalar(
                select(PaymentDB).where(
                    PaymentDB.tenant_id == tenant_id,
                    PaymentDB.provider
                    == normalized_provider,
                    PaymentDB.external_id
                    == normalized_external_id,
                )
            )

            if payment is None:
                raise PaymentNotFoundError(
                    "Pago no encontrado."
                )

            db.expunge(payment)

            return payment

        finally:
            db.close()

    def claim_for_processing(
        self,
        *,
        tenant_id: int,
        payment_id: int,
    ) -> bool:
        """
        Reclama atomicamente un pago pendiente para procesamiento.

        Devuelve True solo para el worker que logra cambiar
        pending -> processing.

        Devuelve False cuando el pago existe pero ya no esta
        pendiente.

        Esto evita que dos workers procesen simultaneamente
        el mismo payment_id.
        """
        db = SessionLocal()

        try:
            payment_exists = db.scalar(
                select(PaymentDB.id).where(
                    PaymentDB.id == payment_id,
                    PaymentDB.tenant_id == tenant_id,
                )
            )

            if payment_exists is None:
                raise PaymentNotFoundError(
                    "Pago no encontrado."
                )

            result = db.execute(
                update(PaymentDB)
                .where(
                    PaymentDB.id == payment_id,
                    PaymentDB.tenant_id == tenant_id,
                    PaymentDB.status == PAYMENT_STATUS_PENDING,
                )
                .values(
                    status=PAYMENT_STATUS_PROCESSING,
                )
            )

            claimed = result.rowcount == 1

            db.commit()

            return claimed

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

    def update_status(
        self,
        *,
        tenant_id: int,
        payment_id: int,
        new_status: str,
    ) -> PaymentDB:
        db = SessionLocal()

        try:
            payment = db.scalar(
                select(PaymentDB).where(
                    PaymentDB.id == payment_id,
                    PaymentDB.tenant_id == tenant_id,
                )
            )

            if payment is None:
                raise PaymentNotFoundError(
                    "Pago no encontrado."
                )

            payment.status = transition_payment_status(
                payment.status,
                new_status,
            )

            db.commit()
            db.refresh(payment)
            db.expunge(payment)

            return payment

        finally:
            db.close()

    def attach_external_id(
        self,
        *,
        tenant_id: int,
        payment_id: int,
        external_id: str,
    ) -> PaymentDB:
        normalized_external_id = self._normalize_required_external_id(
            external_id,
        )

        db = SessionLocal()

        try:
            payment = db.scalar(
                select(PaymentDB).where(
                    PaymentDB.id == payment_id,
                    PaymentDB.tenant_id == tenant_id,
                )
            )

            if payment is None:
                raise PaymentNotFoundError(
                    "Pago no encontrado."
                )

            existing_payment = db.scalar(
                select(PaymentDB).where(
                    PaymentDB.tenant_id == tenant_id,
                    PaymentDB.provider == payment.provider,
                    PaymentDB.external_id
                    == normalized_external_id,
                    PaymentDB.id != payment.id,
                )
            )

            if existing_payment is not None:
                raise PaymentDuplicateError(
                    "El identificador externo de pago "
                    "ya estÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¡ registrado para este tenant "
                    "y proveedor."
                )

            payment.external_id = normalized_external_id

            try:
                db.commit()

            except IntegrityError as exc:
                db.rollback()

                raise PaymentDuplicateError(
                    "No fue posible asociar el identificador "
                    "externo porque ya existe."
                ) from exc

            db.refresh(payment)
            db.expunge(payment)

            return payment

        finally:
            db.close()

    @staticmethod
    def _normalize_provider(
        value: Any,
    ) -> str:
        if not isinstance(value, str):
            raise ValueError(
                "provider es obligatorio."
            )

        normalized = value.strip().lower()

        if not normalized:
            raise ValueError(
                "provider es obligatorio."
            )

        return normalized

    @staticmethod
    def _normalize_required_external_id(
        value: Any,
    ) -> str:
        if not isinstance(value, str):
            raise ValueError(
                "external_id es obligatorio."
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "external_id es obligatorio."
            )

        return normalized

    @staticmethod
    def _normalize_optional_external_id(
        value: Any,
    ) -> str | None:
        if value is None:
            return None

        if not isinstance(value, str):
            raise ValueError(
                "external_id debe ser texto."
            )

        normalized = value.strip()

        return normalized or None

    @staticmethod
    def _normalize_currency(
        currency: Any,
    ) -> str:
        if not isinstance(currency, str):
            raise ValueError(
                "currency es obligatorio."
            )

        normalized = currency.strip().upper()

        if len(normalized) != 3:
            raise ValueError(
                "currency debe ser un cÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â³digo de tres letras."
            )

        return normalized


payment_service = PaymentService()


__all__ = [
    "PaymentDuplicateError",
    "PaymentNotFoundError",
    "PaymentOrderNotFoundError",
    "PaymentOrderPricingUnavailableError",
    "PaymentService",
    "PaymentTenantMismatchError",
    "payment_service",
]
