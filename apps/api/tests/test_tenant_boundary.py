import base64
from collections.abc import Mapping
import hashlib
import hmac
import json

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
import pytest

import app.auth.tenant_boundary as tenant_boundary
from app.auth.tenant_boundary import tenant_boundary_middleware
from app.main import app

TEST_TENANT_ID = "tenant_test"
AUTH_HEADERS = {"X-Tenant-Id": TEST_TENANT_ID, "Authorization": "Bearer test-token"}
SERVICE_SECRET = "test-service-secret"
SERVICE_ISSUER = "cdi-tests"
SERVICE_AUDIENCE = "cdi-api"


def configure_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CDI_TENANT_ID", TEST_TENANT_ID)
    monkeypatch.setenv("CDI_AUTH_TOKEN", "test-token")


def configure_service_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CDI_TENANT_ID", TEST_TENANT_ID)
    monkeypatch.setenv("CDI_AUTH_TOKEN", "static-token")
    monkeypatch.setenv("CDI_SERVICE_TOKEN_HMAC_SECRET", SERVICE_SECRET)
    monkeypatch.setenv("CDI_SERVICE_TOKEN_ISSUER", SERVICE_ISSUER)
    monkeypatch.setenv("CDI_SERVICE_TOKEN_AUDIENCE", SERVICE_AUDIENCE)


def base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def noncanonical_base64url(value: str) -> str:
    decoded = base64.urlsafe_b64decode(value + ("=" * (-len(value) % 4)))
    for candidate in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_":
        variant = f"{value[:-1]}{candidate}"
        if variant != value and base64.urlsafe_b64decode(variant + ("=" * (-len(variant) % 4))) == decoded:
            return variant
    raise AssertionError("test fixture has no non-canonical base64url variant")


def service_token(payload: Mapping[str, str | int]) -> str:
    payload_segment = base64url(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    signature = hmac.new(SERVICE_SECRET.encode(), payload_segment.encode(), hashlib.sha256).digest()
    return f"service.{payload_segment}.{base64url(signature)}"


def service_token_payload(exp: int = 4_102_444_800, tenant_id: str = TEST_TENANT_ID) -> dict[str, str | int]:
    return {
        "tenant_id": tenant_id,
        "iss": SERVICE_ISSUER,
        "aud": SERVICE_AUDIENCE,
        "exp": exp,
    }


def tenant_boundary_client() -> TestClient:
    tenant_app = FastAPI()
    tenant_app.middleware("http")(tenant_boundary_middleware)

    @tenant_app.get("/deals/auth-check")
    async def auth_check(request: Request) -> dict[str, str]:
        return {"tenant_id": request.state.tenant_id}

    return TestClient(tenant_app)


def test_protected_routes_require_configured_auth() -> None:
    client = TestClient(app)

    response = client.get(
        "/intelligence/deal/deal_northstar_expansion",
        params={"tenant_id": TEST_TENANT_ID},
    )

    assert response.status_code == 503


def test_protected_routes_require_configured_auth_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CDI_TENANT_ID", TEST_TENANT_ID)
    monkeypatch.delenv("CDI_AUTH_TOKEN", raising=False)
    client = TestClient(app)

    response = client.get(
        "/intelligence/deal/deal_northstar_expansion",
        params={"tenant_id": TEST_TENANT_ID},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Missing required configuration: CDI_AUTH_TOKEN"


def test_protected_routes_reject_missing_authorization(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    client = TestClient(app)

    response = client.get(
        "/intelligence/deal/deal_northstar_expansion",
        headers={"X-Tenant-Id": TEST_TENANT_ID},
        params={"tenant_id": TEST_TENANT_ID},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing authorization"


def test_protected_routes_reject_bad_bearer(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    client = TestClient(app)

    response = client.get(
        "/intelligence/deal/deal_northstar_expansion",
        headers={"X-Tenant-Id": TEST_TENANT_ID, "Authorization": "Bearer bad"},
        params={"tenant_id": TEST_TENANT_ID},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid authorization"


def test_protected_routes_require_tenant_header(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    client = TestClient(app)

    response = client.get(
        "/intelligence/deal/deal_northstar_expansion",
        headers={"Authorization": "Bearer test-token"},
        params={"tenant_id": TEST_TENANT_ID},
    )

    assert response.status_code == 401


def test_query_tenant_must_match_verified_tenant(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    client = TestClient(app)

    response = client.get(
        "/intelligence/deal/deal_northstar_expansion",
        headers=AUTH_HEADERS,
        params={"tenant_id": "tenant_other"},
    )

    assert response.status_code == 403


def test_signed_service_token_allows_verified_tenant(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_service_auth(monkeypatch)
    token = service_token(service_token_payload())

    response = tenant_boundary_client().get(
        "/deals/auth-check",
        headers={"X-Tenant-Id": TEST_TENANT_ID, "Authorization": f"Bearer {token}"},
        params={"tenant_id": TEST_TENANT_ID},
    )

    assert response.status_code == 200
    assert response.json() == {"tenant_id": TEST_TENANT_ID}


def test_service_token_mode_requires_issuer_and_audience_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CDI_TENANT_ID", TEST_TENANT_ID)
    monkeypatch.delenv("CDI_AUTH_TOKEN", raising=False)
    monkeypatch.setenv("CDI_SERVICE_TOKEN_HMAC_SECRET", SERVICE_SECRET)
    monkeypatch.delenv("CDI_SERVICE_TOKEN_ISSUER", raising=False)
    monkeypatch.delenv("CDI_SERVICE_TOKEN_AUDIENCE", raising=False)
    token = service_token({"tenant_id": TEST_TENANT_ID, "exp": 4_102_444_800})

    response = tenant_boundary_client().get(
        "/deals/auth-check",
        headers={"X-Tenant-Id": TEST_TENANT_ID, "Authorization": f"Bearer {token}"},
        params={"tenant_id": TEST_TENANT_ID},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Missing required configuration: CDI_SERVICE_TOKEN_ISSUER"


def test_expired_or_tampered_service_token_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_service_auth(monkeypatch)
    expired = service_token(service_token_payload(exp=1))
    valid = service_token(service_token_payload())
    tampered = f"{valid[:-1]}{'A' if valid[-1] != 'A' else 'B'}"

    for token in (expired, tampered):
        response = tenant_boundary_client().get(
            "/deals/auth-check",
            headers={"X-Tenant-Id": TEST_TENANT_ID, "Authorization": f"Bearer {token}"},
            params={"tenant_id": TEST_TENANT_ID},
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "Invalid authorization"


def test_noncanonical_service_token_segments_are_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_service_auth(monkeypatch)
    payload = service_token_payload() | {"pad": "x"}
    _, payload_segment, signature_segment = service_token(payload).split(".")
    noncanonical_signature = f"service.{payload_segment}.{noncanonical_base64url(signature_segment)}"
    payload_variant = noncanonical_base64url(payload_segment)
    payload_variant_signature = base64url(
        hmac.new(SERVICE_SECRET.encode(), payload_variant.encode(), hashlib.sha256).digest(),
    )
    noncanonical_payload = f"service.{payload_variant}.{payload_variant_signature}"

    for token in (noncanonical_signature, noncanonical_payload):
        response = tenant_boundary_client().get(
            "/deals/auth-check",
            headers={"X-Tenant-Id": TEST_TENANT_ID, "Authorization": f"Bearer {token}"},
            params={"tenant_id": TEST_TENANT_ID},
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "Invalid authorization"


def test_auth_error_and_redaction_helper_do_not_echo_raw_token(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_service_auth(monkeypatch)
    token = service_token(service_token_payload())
    invalid_token = f"{token}tampered"

    response = tenant_boundary_client().get(
        "/deals/auth-check",
        headers={"X-Tenant-Id": TEST_TENANT_ID, "Authorization": f"Bearer {invalid_token}"},
        params={"tenant_id": TEST_TENANT_ID},
    )

    assert response.status_code == 403
    assert invalid_token not in response.text
    assert invalid_token not in tenant_boundary.redact_auth_value(f"Bearer {invalid_token}")


def test_body_tenant_must_match_verified_tenant(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    client = TestClient(app)

    response = client.post(
        "/calls/ingest",
        headers=AUTH_HEADERS,
        json={
            "tenant_id": "tenant_other",
            "deal_id": "deal_northstar_expansion",
            "call_id": "call_ns_006",
            "timestamp": "2026-03-04T15:00:00.000Z",
            "duration_seconds": 1800,
            "transcript": "Marcus paused new spend until the logistics migration clears.",
        },
    )

    assert response.status_code == 403


def test_unknown_tenant_header_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    client = TestClient(app)

    response = client.get(
        "/deals/deal_northstar_expansion/timeline",
        headers={"X-Tenant-Id": "tenant_other", "Authorization": "Bearer test-token"},
        params={"tenant_id": "tenant_other"},
    )

    assert response.status_code == 403
