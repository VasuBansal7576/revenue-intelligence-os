import base64
import binascii
from dataclasses import dataclass
import hashlib
import hmac
import json
import time
from typing import Final

from fastapi import HTTPException, Request, status
from app.config import MissingConfigurationError, Settings, get_settings, require_config
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

TENANT_HEADER: Final = "x-tenant-id"
PROTECTED_PREFIXES: Final = (
    "/accounts",
    "/admin",
    "/assistant",
    "/audit",
    "/calls",
    "/coaching",
    "/crm",
    "/deals",
    "/engage",
    "/exports",
    "/forecast",
    "/intelligence",
    "/knowledge",
    "/ops",
    "/pipeline",
    "/search",
)
BEARER_PREFIX: Final = "Bearer "
SERVICE_TOKEN_PREFIX: Final = "service"
REDACTED_AUTH_VALUE: Final = "[redacted]"


@dataclass(frozen=True, slots=True)
class ServiceTokenClaims:
    tenant_id: str


def tenant_error(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": detail})


def redact_auth_value(value: str | None) -> str:
    if value is None:
        return "<missing>"
    scheme, separator, _ = value.partition(" ")
    if separator:
        return f"{scheme} {REDACTED_AUTH_VALUE}"
    return REDACTED_AUTH_VALUE


def base64url_decode(value: str) -> bytes | None:
    try:
        decoded = base64.urlsafe_b64decode(value + ("=" * (-len(value) % 4)))
    except (binascii.Error, ValueError):
        return None
    if base64.urlsafe_b64encode(decoded).decode().rstrip("=") != value:
        return None
    return decoded


def verify_service_token(token: str, settings: Settings) -> ServiceTokenClaims | None:
    secret = settings.service_token_hmac_secret
    if not secret:
        return None

    parts = token.split(".")
    if len(parts) != 3 or parts[0] != SERVICE_TOKEN_PREFIX:
        return None

    payload_segment = parts[1]
    payload_bytes = base64url_decode(payload_segment)
    if payload_bytes is None:
        return None

    signature = base64url_decode(parts[2])
    if signature is None:
        return None

    expected_signature = hmac.new(secret.encode(), payload_segment.encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(signature, expected_signature):
        return None

    try:
        payload = json.loads(payload_bytes)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

    if not isinstance(payload, dict):
        return None

    tenant_id = payload.get("tenant_id")
    expires_at = payload.get("exp")
    issuer = payload.get("iss")
    audience = payload.get("aud")
    if not isinstance(tenant_id, str) or not isinstance(expires_at, int):
        return None
    if expires_at <= int(time.time()):
        return None
    if not settings.service_token_issuer or issuer != settings.service_token_issuer:
        return None
    if not settings.service_token_audience or audience != settings.service_token_audience:
        return None

    return ServiceTokenClaims(tenant_id=tenant_id)


def verified_bearer_tenant_id(token: str, settings: Settings) -> str | None:
    if settings.auth_token and hmac.compare_digest(token, settings.auth_token):
        return require_config(settings.tenant_id, "CDI_TENANT_ID")

    claims = verify_service_token(token, settings)
    if claims is None:
        return None
    return claims.tenant_id


async def tenant_boundary_middleware(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    if not request.url.path.startswith(PROTECTED_PREFIXES):
        return await call_next(request)

    settings = get_settings()
    try:
        configured_tenant_id = require_config(settings.tenant_id, "CDI_TENANT_ID")
        if not settings.auth_token and not settings.service_token_hmac_secret:
            require_config(settings.auth_token, "CDI_AUTH_TOKEN")
        if settings.service_token_hmac_secret:
            require_config(settings.service_token_issuer, "CDI_SERVICE_TOKEN_ISSUER")
            require_config(settings.service_token_audience, "CDI_SERVICE_TOKEN_AUDIENCE")
    except MissingConfigurationError as error:
        return tenant_error(status.HTTP_503_SERVICE_UNAVAILABLE, str(error))

    authorization = request.headers.get("authorization")
    if authorization is None:
        return tenant_error(status.HTTP_401_UNAUTHORIZED, "Missing authorization")
    if not authorization.startswith(BEARER_PREFIX):
        return tenant_error(status.HTTP_403_FORBIDDEN, "Invalid authorization")

    verified_tenant_id = verified_bearer_tenant_id(authorization.removeprefix(BEARER_PREFIX), settings)
    if verified_tenant_id is None:
        return tenant_error(status.HTTP_403_FORBIDDEN, "Invalid authorization")

    tenant_id = request.headers.get(TENANT_HEADER)
    if tenant_id is None:
        return tenant_error(status.HTTP_401_UNAUTHORIZED, "Missing tenant header")
    if tenant_id != configured_tenant_id:
        return tenant_error(status.HTTP_403_FORBIDDEN, "Unknown tenant")
    if tenant_id != verified_tenant_id:
        return tenant_error(status.HTTP_403_FORBIDDEN, "Tenant mismatch")

    query_tenant_id = request.query_params.get("tenant_id")
    if query_tenant_id is not None and query_tenant_id != tenant_id:
        return tenant_error(status.HTTP_403_FORBIDDEN, "Tenant mismatch")

    request.state.tenant_id = tenant_id
    return await call_next(request)


def require_tenant_match(requested_tenant_id: str, verified_tenant_id: str) -> None:
    if requested_tenant_id != verified_tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant mismatch")
