from types import SimpleNamespace

from app.services.toast_authentication_service import (
    ToastAuthenticationService,
)


class FakeResponse:
    def __init__(
        self,
        status_code: int,
        payload: dict,
    ) -> None:
        self.status_code = status_code
        self.payload = payload

    def json(self) -> dict:
        return self.payload


class FakeHttpClient:
    def __init__(
        self,
        responses: list[FakeResponse],
    ) -> None:
        self.responses = list(responses)
        self.calls = []

    def post(
        self,
        url,
        headers=None,
        json=None,
        timeout=None,
    ):
        self.calls.append(
            {
                "url": url,
                "headers": headers,
                "json": json,
                "timeout": timeout,
            }
        )

        return self.responses.pop(0)


def build_configuration():
    return SimpleNamespace(
        base_url="https://toast.test",
        client_id="test-client-id",
        client_secret="test-client-secret",
        timeout=15,
    )


def test_authentication_returns_access_token():
    http_client = FakeHttpClient(
        responses=[
            FakeResponse(
                status_code=200,
                payload={
                    "token": {
                        "accessToken": "toast-token-123",
                        "expiresIn": 3600,
                    }
                },
            )
        ]
    )

    service = ToastAuthenticationService(
        configuration=build_configuration(),
        http_client=http_client,
    )

    token = service.get_access_token()

    assert token == "toast-token-123"

    assert len(http_client.calls) == 1

    call = http_client.calls[0]

    assert call["url"] == (
        "https://toast.test"
        "/authentication/v1/authentication/login"
    )

    assert call["json"] == {
        "clientId": "test-client-id",
        "clientSecret": "test-client-secret",
        "userAccessType": "TOAST_MACHINE_CLIENT",
    }

    assert call["timeout"] == 15


def test_authentication_reuses_cached_token():
    http_client = FakeHttpClient(
        responses=[
            FakeResponse(
                status_code=200,
                payload={
                    "token": {
                        "accessToken": "cached-token",
                        "expiresIn": 3600,
                    }
                },
            )
        ]
    )

    service = ToastAuthenticationService(
        configuration=build_configuration(),
        http_client=http_client,
    )

    first_token = service.get_access_token()
    second_token = service.get_access_token()

    assert first_token == "cached-token"
    assert second_token == "cached-token"

    assert len(http_client.calls) == 1


def test_authentication_refreshes_expired_token():
    http_client = FakeHttpClient(
        responses=[
            FakeResponse(
                status_code=200,
                payload={
                    "token": {
                        "accessToken": "first-token",
                        "expiresIn": 0,
                    }
                },
            ),
            FakeResponse(
                status_code=200,
                payload={
                    "token": {
                        "accessToken": "second-token",
                        "expiresIn": 3600,
                    }
                },
            ),
        ]
    )

    service = ToastAuthenticationService(
        configuration=build_configuration(),
        http_client=http_client,
    )

    first_token = service.get_access_token()
    second_token = service.get_access_token()

    assert first_token == "first-token"
    assert second_token == "second-token"

    assert len(http_client.calls) == 2


def test_authentication_rejects_failed_request():
    http_client = FakeHttpClient(
        responses=[
            FakeResponse(
                status_code=401,
                payload={
                    "message": "Unauthorized",
                },
            )
        ]
    )

    service = ToastAuthenticationService(
        configuration=build_configuration(),
        http_client=http_client,
    )

    try:
        service.get_access_token()
    except RuntimeError as exc:
        assert str(exc) == (
            "Toast authentication failed."
        )
    else:
        raise AssertionError(
            "RuntimeError was not raised."
        )


def test_authentication_rejects_missing_token():
    http_client = FakeHttpClient(
        responses=[
            FakeResponse(
                status_code=200,
                payload={
                    "token": {
                        "expiresIn": 3600,
                    }
                },
            )
        ]
    )

    service = ToastAuthenticationService(
        configuration=build_configuration(),
        http_client=http_client,
    )

    try:
        service.get_access_token()
    except RuntimeError as exc:
        assert str(exc) == (
            "Toast authentication response "
            "did not contain an access token."
        )
    else:
        raise AssertionError(
            "RuntimeError was not raised."
        )