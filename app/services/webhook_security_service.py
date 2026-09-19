import hashlib
import hmac
import secrets


SIGNATURE_PREFIX = "sha256="


def generate_webhook_secret() -> str:
    return secrets.token_urlsafe(32)


def build_webhook_signature(
    payload: bytes,
    secret: str,
) -> str:
    digest = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return f"{SIGNATURE_PREFIX}{digest}"


def verify_webhook_signature(
    payload: bytes,
    secret: str,
    signature: str,
) -> bool:
    expected_signature = build_webhook_signature(
        payload=payload,
        secret=secret,
    )

    return hmac.compare_digest(
        expected_signature,
        signature.strip(),
    )