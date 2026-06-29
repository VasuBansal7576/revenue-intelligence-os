from typing import Final, Literal

from fastapi import FastAPI, Query, Request, status
from starlette.responses import JSONResponse
from app.auth import require_tenant_match, tenant_boundary_middleware
from app.config import MissingConfigurationError, Settings, crm_configured, crm_missing_config, get_settings, llm_configured, llm_missing_config
from app.crm.router import router as crm_router
from app.deals.router import router as deals_router
from app.external import UpstreamServiceError
from app.external import JsonMap
from app.intelligence.router import router as intelligence_router
from app.ingestion.router import router as ingestion_router
from app.knowledge.router import router as knowledge_router
from app.pipeline.router import router as pipeline_router
from app.revenue.router import router as revenue_router
from app.temporal.router import router as temporal_router

RuntimeLabel = Literal["local-demo", "provider-not-ready", "live-provider-ready"]

PROVIDER_REQUIREMENTS: Final = (
    ("hydradb", ("HYDRA_DB_API_KEY",)),
    ("llm", ()),
    ("crm", ("CRM_CLIENT_ID", "CRM_CLIENT_SECRET", "CRM_WEBHOOK_SECRET")),
)

app = FastAPI(title="Causal Deal Intelligence API", version="0.1.0")
app.middleware("http")(tenant_boundary_middleware)
app.include_router(deals_router)
app.include_router(intelligence_router)
app.include_router(ingestion_router)
app.include_router(knowledge_router)
app.include_router(crm_router)
app.include_router(pipeline_router)
app.include_router(temporal_router)
app.include_router(revenue_router)


@app.exception_handler(MissingConfigurationError)
async def missing_configuration_handler(_: Request, error: MissingConfigurationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": f"provider-not-ready: {error.name}"},
    )


@app.exception_handler(UpstreamServiceError)
async def upstream_service_handler(_: Request, error: UpstreamServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": str(error)},
    )


@app.get("/health")
async def health() -> JsonMap:
    settings = get_settings()
    return {
        "status": "ok",
        "runtime": runtime_label(settings),
        "tenant_configured": settings.tenant_id is not None,
        "auth_configured": not auth_missing_config(settings),
        "hydradb_configured": settings.hydradb_api_key is not None,
        "llm_provider": settings.llm_provider,
        "llm_configured": llm_configured(settings),
        "openai_configured": settings.openai_api_key is not None,
        "crm_provider": settings.crm_provider,
        "crm_configured": crm_configured(settings),
    }


@app.get("/ops/readiness")
async def ops_readiness(request: Request, tenant_id: str = Query(...)) -> JsonMap:
    require_tenant_match(tenant_id, request.state.tenant_id)
    settings = get_settings()
    providers = provider_statuses(settings)
    missing_providers = [provider["name"] for provider in providers if provider["state"] == "missing-config"]
    return {
        "tenant_id": tenant_id,
        "status": "ok" if runtime_label(settings) != "provider-not-ready" else "setup-required",
        "runtime": runtime_label(settings),
        "providers": providers,
        "missing_providers": missing_providers,
        "missing_config": provider_missing_config(settings),
        "auth": {
            "state": "configured" if not auth_missing_config(settings) else "missing-config",
            "missing_config": auth_missing_config(settings),
            "notes": [
                "Use Authorization: Bearer <token> and X-Tenant-Id.",
                "Static token or complete HMAC service-token config is required.",
            ],
        },
        "jobs": {
            "state": "persistent-path-configured" if settings.job_store_path else "local-default-path",
            "notes": ["Set CDI_JOB_STORE_PATH for a deployment-managed durable job file."],
        },
        "deployment": {
            "state": "not-deployed-by-this-proof",
            "notes": [
                "Run under a process manager with HTTPS ingress and managed secrets before live use.",
                "This readiness response does not prove live provider validation.",
            ],
        },
    }


def runtime_label(settings: Settings) -> RuntimeLabel:
    if settings.demo_mode:
        return "local-demo"
    if auth_missing_config(settings) or provider_missing_config(settings):
        return "provider-not-ready"
    return "live-provider-ready"


def auth_missing_config(settings: Settings) -> list[str]:
    missing = []
    if not settings.tenant_id:
        missing.append("CDI_TENANT_ID")
    if settings.service_token_hmac_secret:
        if not settings.service_token_issuer:
            missing.append("CDI_SERVICE_TOKEN_ISSUER")
        if not settings.service_token_audience:
            missing.append("CDI_SERVICE_TOKEN_AUDIENCE")
    elif not settings.auth_token:
        missing.append("CDI_AUTH_TOKEN")
    return missing


def provider_missing_config(settings: Settings) -> list[str]:
    missing = []
    if not settings.hydradb_api_key:
        missing.append("HYDRA_DB_API_KEY")
    missing.extend(llm_missing_config(settings))
    missing.extend(crm_missing_config(settings))
    return missing


def provider_statuses(settings: Settings) -> list[JsonMap]:
    providers = []
    for name, config_names in PROVIDER_REQUIREMENTS:
        match name:
            case "llm":
                missing_config = llm_missing_config(settings)
            case "crm":
                missing_config = crm_missing_config(settings)
            case _:
                missing_config = [config_name for config_name in config_names if config_name in provider_missing_config(settings)]
        state = "not-required-for-local-demo" if settings.demo_mode else "ready"
        if missing_config and not settings.demo_mode:
            state = "missing-config"
        providers.append({"name": name, "state": state, "missing_config": missing_config})
    return providers
