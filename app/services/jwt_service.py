from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings


def create_access_token(
    user_id: int,
) -> str:
    """
    Crea un JWT de acceso para un usuario autenticado.
    """

    now = datetime.now(timezone.utc)

    expires_at = (
        now
        + timedelta(
            minutes=settings.jwt_expire_minutes,
        )
    )

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(
    token: str,
) -> int:
    """
    Valida un JWT y devuelve el user_id contenido en el token.

    Lanza jwt.InvalidTokenError si el token no es válido
    o está expirado.
    """

    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[
            settings.jwt_algorithm,
        ],
    )

    subject = payload.get("sub")

    if subject is None:
        raise jwt.InvalidTokenError(
            "El token no contiene un subject válido."
        )

    try:
        return int(subject)
    except (TypeError, ValueError) as exc:
        raise jwt.InvalidTokenError(
            "El subject del token no es un user_id válido."
        ) from exc