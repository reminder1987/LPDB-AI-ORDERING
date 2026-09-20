import os
import re
from collections.abc import Mapping


SECRET_REFERENCE_PATTERN = re.compile(
    r"^[A-Z][A-Z0-9_]*$"
)


class IntegrationSecretError(ValueError):
    pass


class IntegrationSecretNotFoundError(
    IntegrationSecretError
):
    pass


class InvalidIntegrationSecretReferenceError(
    IntegrationSecretError
):
    pass


class IntegrationSecretService:
    def __init__(
        self,
        environment: Mapping[str, str] | None = None,
    ) -> None:
        self._environment = (
            environment
            if environment is not None
            else os.environ
        )

    def resolve(
        self,
        reference: str,
    ) -> str:
        normalized_reference = (
            self._normalize_reference(reference)
        )

        value = self._environment.get(
            normalized_reference
        )

        if value is None:
            raise IntegrationSecretNotFoundError(
                "Integration secret was not found."
            )

        normalized_value = value.strip()

        if not normalized_value:
            raise IntegrationSecretNotFoundError(
                "Integration secret was not found."
            )

        return normalized_value

    def resolve_credentials(
        self,
        credentials: Mapping[str, str],
    ) -> dict[str, str]:
        if not isinstance(credentials, Mapping):
            raise InvalidIntegrationSecretReferenceError(
                "Integration credentials must be a mapping."
            )

        resolved: dict[str, str] = {}

        for credential_name, reference in credentials.items():
            normalized_name = str(
                credential_name
            ).strip()

            if not normalized_name:
                raise InvalidIntegrationSecretReferenceError(
                    "Credential name is required."
                )

            resolved[normalized_name] = self.resolve(
                reference
            )

        return resolved

    @staticmethod
    def _normalize_reference(
        reference: str,
    ) -> str:
        if not isinstance(reference, str):
            raise InvalidIntegrationSecretReferenceError(
                "Integration secret reference must be a string."
            )

        normalized = reference.strip()

        if not normalized:
            raise InvalidIntegrationSecretReferenceError(
                "Integration secret reference is required."
            )

        if not SECRET_REFERENCE_PATTERN.fullmatch(
            normalized
        ):
            raise InvalidIntegrationSecretReferenceError(
                "Invalid integration secret reference."
            )

        return normalized


integration_secret_service = IntegrationSecretService()


__all__ = [
    "IntegrationSecretError",
    "IntegrationSecretNotFoundError",
    "InvalidIntegrationSecretReferenceError",
    "IntegrationSecretService",
    "integration_secret_service",
]