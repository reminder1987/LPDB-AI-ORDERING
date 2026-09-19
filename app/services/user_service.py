from sqlalchemy.orm import Session

from app.models.user_db import UserDB
from app.services.password_service import (
    hash_password,
    verify_password,
)


class UserService:
    """
    Gestiona usuarios administrativos de la plataforma.

    Esta capa se encarga de la persistencia y verificación
    de credenciales. La autenticación HTTP se implementará
    en una capa posterior.
    """

    def get_by_email(
        self,
        db: Session,
        email: str,
    ) -> UserDB | None:
        normalized_email = email.strip().lower()

        return (
            db.query(UserDB)
            .filter(
                UserDB.email == normalized_email,
            )
            .first()
        )

    def create_user(
        self,
        db: Session,
        email: str,
        password: str,
    ) -> UserDB:
        normalized_email = email.strip().lower()

        user = UserDB(
            email=normalized_email,
            password_hash=hash_password(password),
            active=True,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    def verify_credentials(
        self,
        db: Session,
        email: str,
        password: str,
    ) -> UserDB | None:
        user = self.get_by_email(
            db,
            email,
        )

        if user is None:
            return None

        if not user.active:
            return None

        if not verify_password(
            password,
            user.password_hash,
        ):
            return None

        return user


user_service = UserService()