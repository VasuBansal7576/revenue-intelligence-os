from dataclasses import dataclass
import json
from os import getenv
from pathlib import Path


@dataclass(frozen=True, slots=True)
class MissingConfigurationError(Exception):
    name: str

    def __str__(self) -> str:
        return f"Missing required configuration: {self.name}"


@dataclass(frozen=True, slots=True)
class Settings:
    tenant_id: str | None
    auth_token: str | None
    hydradb_api_key: str | None
    hydradb_base_url: str
    llm_provider: str
    openai_api_key: str | None
    openai_model: str
    openai_transcription_model: str
    transcription_command: str | None
    codex_access_token: str | None
    codex_base_url: str
    provider_timeout_seconds: float
    job_store_path: str | None
    crm_provider: str
    crm_client_id: str | None
    crm_client_secret: str | None
    crm_webhook_secret: str | None
    service_token_hmac_secret: str | None
    service_token_issuer: str | None
    service_token_audience: str | None
    demo_mode: bool


def get_settings() -> Settings:
    llm_provider = getenv("CDI_LLM_PROVIDER", "openai").lower()
    return Settings(
        tenant_id=getenv("CDI_TENANT_ID"),
        auth_token=getenv("CDI_AUTH_TOKEN"),
        hydradb_api_key=getenv("HYDRA_DB_API_KEY"),
        hydradb_base_url=getenv("HYDRA_DB_BASE_URL", "https://api.hydradb.com"),
        llm_provider=llm_provider,
        openai_api_key=getenv("OPENAI_API_KEY"),
        openai_model=getenv("CDI_LLM_MODEL", getenv("OPENAI_MODEL", default_llm_model(llm_provider))),
        openai_transcription_model=getenv("OPENAI_TRANSCRIPTION_MODEL", "gpt-4o-transcribe"),
        transcription_command=getenv("CDI_TRANSCRIPTION_COMMAND"),
        codex_access_token=codex_access_token(llm_provider),
        codex_base_url=getenv("CODEX_BASE_URL", "https://chatgpt.com/backend-api/codex"),
        provider_timeout_seconds=float(getenv("PROVIDER_HTTP_TIMEOUT_SECONDS", "30")),
        job_store_path=getenv("CDI_JOB_STORE_PATH"),
        crm_provider=getenv("CDI_CRM_PROVIDER", "external").lower(),
        crm_client_id=getenv("CRM_CLIENT_ID"),
        crm_client_secret=getenv("CRM_CLIENT_SECRET"),
        crm_webhook_secret=getenv("CRM_WEBHOOK_SECRET"),
        service_token_hmac_secret=getenv("CDI_SERVICE_TOKEN_HMAC_SECRET"),
        service_token_issuer=getenv("CDI_SERVICE_TOKEN_ISSUER"),
        service_token_audience=getenv("CDI_SERVICE_TOKEN_AUDIENCE"),
        demo_mode=getenv("CDI_DEMO_MODE") == "1",
    )


def require_config(value: str | None, name: str) -> str:
    if value:
        return value
    raise MissingConfigurationError(name=name)


def default_llm_model(provider: str) -> str:
    if provider == "codex":
        return "gpt-5.3-codex"
    return "gpt-5.5"


def codex_access_token(provider: str) -> str | None:
    if provider != "codex":
        return None
    token = getenv("CODEX_ACCESS_TOKEN")
    if token:
        return token
    return codex_access_token_from_file(Path(getenv("CODEX_AUTH_FILE", "~/.codex/auth.json")).expanduser())


def codex_access_token_from_file(path: Path) -> str | None:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    match data:
        case {"tokens": {"access_token": str(token)}} if token:
            return token
        case {"OPENAI_API_KEY": str(token)} if token:
            return token
        case _:
            return None


def llm_missing_config(settings: Settings) -> list[str]:
    if settings.llm_provider == "codex":
        return [] if settings.codex_access_token else ["CODEX_ACCESS_TOKEN or ~/.codex/auth.json"]
    return [] if settings.openai_api_key else ["OPENAI_API_KEY"]


def llm_configured(settings: Settings) -> bool:
    return not llm_missing_config(settings)


def crm_missing_config(settings: Settings) -> list[str]:
    if settings.crm_provider == "manual":
        return []
    missing = []
    if not settings.crm_client_id:
        missing.append("CRM_CLIENT_ID")
    if not settings.crm_client_secret:
        missing.append("CRM_CLIENT_SECRET")
    if not settings.crm_webhook_secret:
        missing.append("CRM_WEBHOOK_SECRET")
    return missing


def crm_configured(settings: Settings) -> bool:
    return not crm_missing_config(settings)
