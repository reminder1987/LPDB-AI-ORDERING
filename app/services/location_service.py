import re
import unicodedata

from app.core.database import SessionLocal
from app.models.location_db import LocationDB


class LocationService:

    def get_all_active_locations(
        self,
        tenant_id: int,
    ):
        db = SessionLocal()

        try:
            return (
                db.query(LocationDB)
                .filter(
                    LocationDB.tenant_id == tenant_id,
                    LocationDB.active.is_(True),
                )
                .order_by(LocationDB.customer_name)
                .all()
            )

        finally:
            db.close()

    def get_location_by_id(
        self,
        location_id: int,
        tenant_id: int,
    ):
        db = SessionLocal()

        try:
            return (
                db.query(LocationDB)
                .filter(
                    LocationDB.id == location_id,
                    LocationDB.tenant_id == tenant_id,
                    LocationDB.active.is_(True),
                )
                .first()
            )

        finally:
            db.close()

    def find_locations(
        self,
        query: str,
        tenant_id: int,
    ):
        normalized_query = self._normalize_text(
            query,
        )

        if not normalized_query:
            return []

        db = SessionLocal()

        try:
            locations = (
                db.query(LocationDB)
                .filter(
                    LocationDB.tenant_id == tenant_id,
                    LocationDB.active.is_(True),
                )
                .order_by(LocationDB.customer_name)
                .all()
            )

            matches = []

            for location in locations:

                if self._location_matches_query(
                    location,
                    normalized_query,
                ):
                    matches.append(location)

            return matches

        finally:
            db.close()

    def _location_matches_query(
        self,
        location: LocationDB,
        normalized_query: str,
    ) -> bool:

        query_tokens = set(
            normalized_query.split()
        )

        # ---------------------------------------------------------
        # 1. Nombre comercial de la sede.
        #
        # Ejemplo:
        #
        # "Quiero un Perro del Barrio en Dirty Rabbit"
        #
        # contiene:
        #
        # dirty + rabbit
        #
        # por lo tanto coincide con:
        #
        # DIRTY RABBIT
        # ---------------------------------------------------------

        customer_name = self._normalize_text(
            location.customer_name or "",
        )

        if customer_name:

            customer_tokens = set(
                customer_name.split()
            )

            if customer_tokens.issubset(
                query_tokens,
            ):
                return True

        # ---------------------------------------------------------
        # 2. Nombre interno de Toast.
        #
        # Esto permite que posteriormente también podamos resolver
        # una sede si alguien utiliza el nombre interno conocido.
        # ---------------------------------------------------------

        toast_name = self._normalize_text(
            location.toast_name or "",
        )

        if toast_name:

            toast_tokens = set(
                toast_name.split()
            )

            if toast_tokens.issubset(
                query_tokens,
            ):
                return True

        # ---------------------------------------------------------
        # 3. Ciudad.
        #
        # Se utiliza solamente como coincidencia adicional.
        # No se considera suficiente una ciudad genérica si varias
        # sedes comparten la misma.
        # ---------------------------------------------------------

        city = self._normalize_text(
            location.city or "",
        )

        if city:

            city_tokens = set(
                city.split()
            )

            if (
                len(city_tokens) > 1
                and city_tokens.issubset(query_tokens)
            ):
                return True

        # ---------------------------------------------------------
        # 4. Dirección.
        #
        # Permite reconocer una sede si el usuario proporciona
        # parte de su dirección.
        # ---------------------------------------------------------

        address = self._normalize_text(
            location.address or "",
        )

        if address:

            address_tokens = set(
                address.split()
            )

            meaningful_address_tokens = {
                token
                for token in address_tokens
                if len(token) >= 3
            }

            matched_address_tokens = (
                meaningful_address_tokens
                & query_tokens
            )

            if (
                len(matched_address_tokens) >= 2
            ):
                return True

        return False

    @staticmethod
    def _normalize_text(
        value: str,
    ) -> str:

        value = value.strip().lower()

        value = unicodedata.normalize(
            "NFD",
            value,
        )

        value = "".join(
            character
            for character in value
            if unicodedata.category(character) != "Mn"
        )

        value = re.sub(
            r"[^a-z0-9\s]",
            " ",
            value,
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value.strip()


location_service = LocationService()