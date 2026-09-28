from datetime import time

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.location_db import (
    LocationDB,
    LocationHourDB,
)


class LocationAdministrationNotFoundError(ValueError):
    """La sede solicitada no existe para el tenant."""


class LocationAdministrationDuplicateError(ValueError):
    """La identidad externa de la sede ya esta registrada."""


class LocationAdministrationValidationError(ValueError):
    """Los datos administrativos de la sede no son validos."""


class LocationAdministrationService:
    def list_locations(
        self,
        session: Session,
        *,
        tenant_id: int,
    ) -> list[LocationDB]:
        return list(
            session.scalars(
                select(LocationDB)
                .where(
                    LocationDB.tenant_id == tenant_id,
                )
                .order_by(
                    LocationDB.customer_name,
                    LocationDB.id,
                )
            ).all()
        )

    def get_location(
        self,
        session: Session,
        *,
        tenant_id: int,
        location_id: int,
    ) -> LocationDB:
        location = session.scalar(
            select(LocationDB).where(
                LocationDB.id == location_id,
                LocationDB.tenant_id == tenant_id,
            )
        )

        if location is None:
            raise LocationAdministrationNotFoundError(
                f"Sede no encontrada: {location_id}"
            )

        return location

    def create_location(
        self,
        session: Session,
        *,
        tenant_id: int,
        customer_name: str,
        toast_name: str,
        toast_restaurant_guid: str | None = None,
        city: str | None = None,
        address: str | None = None,
        active: bool = True,
    ) -> LocationDB:
        normalized_customer_name = self._required_text(
            customer_name,
            field_name="nombre comercial",
            max_length=100,
        )

        normalized_toast_name = self._required_text(
            toast_name,
            field_name="nombre Toast",
            max_length=150,
        )

        location = LocationDB(
            tenant_id=tenant_id,
            customer_name=normalized_customer_name,
            toast_name=normalized_toast_name,
            toast_restaurant_guid=self._optional_text(
                toast_restaurant_guid,
                max_length=100,
            ),
            city=self._optional_text(
                city,
                max_length=100,
            ),
            address=self._optional_text(
                address,
                max_length=200,
            ),
            active=active,
        )

        session.add(location)

        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            raise LocationAdministrationDuplicateError(
                "El toast_restaurant_guid ya esta registrado."
            ) from exc

        session.refresh(location)

        return location

    def update_location(
        self,
        session: Session,
        *,
        tenant_id: int,
        location_id: int,
        customer_name: str | None = None,
        toast_name: str | None = None,
        toast_restaurant_guid: str | None = None,
        city: str | None = None,
        address: str | None = None,
        active: bool | None = None,
        update_customer_name: bool = False,
        update_toast_name: bool = False,
        update_toast_restaurant_guid: bool = False,
        update_city: bool = False,
        update_address: bool = False,
        update_active: bool = False,
    ) -> LocationDB:
        location = self.get_location(
            session,
            tenant_id=tenant_id,
            location_id=location_id,
        )

        if update_customer_name:
            location.customer_name = self._required_text(
                customer_name,
                field_name="nombre comercial",
                max_length=100,
            )

        if update_toast_name:
            location.toast_name = self._required_text(
                toast_name,
                field_name="nombre Toast",
                max_length=150,
            )

        if update_toast_restaurant_guid:
            location.toast_restaurant_guid = self._optional_text(
                toast_restaurant_guid,
                max_length=100,
            )

        if update_city:
            location.city = self._optional_text(
                city,
                max_length=100,
            )

        if update_address:
            location.address = self._optional_text(
                address,
                max_length=200,
            )

        if update_active:
            if active is None:
                raise LocationAdministrationValidationError(
                    "El estado activo no puede ser nulo."
                )

            location.active = active

        session.add(location)

        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            raise LocationAdministrationDuplicateError(
                "El toast_restaurant_guid ya esta registrado."
            ) from exc

        session.refresh(location)

        return location

    def get_location_hours(
        self,
        session: Session,
        *,
        tenant_id: int,
        location_id: int,
    ) -> list[LocationHourDB]:
        self.get_location(
            session,
            tenant_id=tenant_id,
            location_id=location_id,
        )

        return list(
            session.scalars(
                select(LocationHourDB)
                .where(
                    LocationHourDB.location_id == location_id,
                )
                .order_by(
                    LocationHourDB.day_of_week,
                    LocationHourDB.id,
                )
            ).all()
        )

    def replace_location_hours(
        self,
        session: Session,
        *,
        tenant_id: int,
        location_id: int,
        hours: list[tuple[int, time, time]],
    ) -> list[LocationHourDB]:
        self.get_location(
            session,
            tenant_id=tenant_id,
            location_id=location_id,
        )

        normalized_hours = self._validate_hours(hours)

        try:
            session.execute(
                delete(LocationHourDB).where(
                    LocationHourDB.location_id == location_id,
                )
            )

            for day_of_week, opens_at, closes_at in normalized_hours:
                session.add(
                    LocationHourDB(
                        location_id=location_id,
                        day_of_week=day_of_week,
                        opens_at=opens_at,
                        closes_at=closes_at,
                    )
                )

            session.commit()

        except Exception:
            session.rollback()
            raise

        return self.get_location_hours(
            session,
            tenant_id=tenant_id,
            location_id=location_id,
        )

    @staticmethod
    def _validate_hours(
        hours: list[tuple[int, time, time]],
    ) -> list[tuple[int, time, time]]:
        seen_days: set[int] = set()
        normalized: list[tuple[int, time, time]] = []

        for day_of_week, opens_at, closes_at in hours:
            if day_of_week < 0 or day_of_week > 6:
                raise LocationAdministrationValidationError(
                    "day_of_week debe estar entre 0 y 6."
                )

            if day_of_week in seen_days:
                raise LocationAdministrationValidationError(
                    f"El dia {day_of_week} esta duplicado."
                )

            seen_days.add(day_of_week)

            normalized.append(
                (
                    day_of_week,
                    opens_at,
                    closes_at,
                )
            )

        normalized.sort(key=lambda item: item[0])

        return normalized

    @staticmethod
    def _required_text(
        value: str | None,
        *,
        field_name: str,
        max_length: int,
    ) -> str:
        normalized = (value or "").strip()

        if not normalized:
            raise LocationAdministrationValidationError(
                f"El {field_name} es obligatorio."
            )

        if len(normalized) > max_length:
            raise LocationAdministrationValidationError(
                f"El {field_name} no puede superar "
                f"{max_length} caracteres."
            )

        return normalized

    @staticmethod
    def _optional_text(
        value: str | None,
        *,
        max_length: int,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        if not normalized:
            return None

        if len(normalized) > max_length:
            raise LocationAdministrationValidationError(
                f"El valor no puede superar {max_length} caracteres."
            )

        return normalized


location_administration_service = LocationAdministrationService()


__all__ = [
    "LocationAdministrationDuplicateError",
    "LocationAdministrationNotFoundError",
    "LocationAdministrationService",
    "LocationAdministrationValidationError",
    "location_administration_service",
]
