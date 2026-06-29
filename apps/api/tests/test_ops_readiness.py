from fastapi.testclient import TestClient
import pytest

from app.main import app

TEST_TENANT_ID = "tenant_test"
AUTH_HEADERS = {"X-Tenant-Id": TEST_TENANT_ID, "Authorization": "Bearer test-token"}


def configure_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CDI_TENANT_ID", TEST_TENANT_ID)
    monkeypatch.setenv("CDI_AUTH_TOKEN", "test-token")


def clear_provider_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "CDI_DEMO_MODE",
        "CDI_LLM_PROVIDER",
        "CODEX_ACCESS_TOKEN",
        "CODEX_AUTH_FILE",
        "HYDRA_DB_API_KEY",
        "OPENAI_API_KEY",
        "CRM_CLIENT_ID",
        "CRM_CLIENT_SECRET",
        "CRM_WEBHOOK_SECRET",
        "CDI_CRM_PROVIDER",
        "CDI_SERVICE_TOKEN_HMAC_SECRET",
        "CDI_SERVICE_TOKEN_ISSUER",
        "CDI_SERVICE_TOKEN_AUDIENCE",
    ):
        monkeypatch.delenv(name, raising=False)


def test_health_reports_local_demo_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("CDI_DEMO_MODE", "1")

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json()["runtime"] == "local-demo"


def test_health_reports_provider_not_ready_until_credentials_exist(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    clear_provider_env(monkeypatch)

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json()["runtime"] == "provider-not-ready"


def test_health_reports_live_provider_ready_when_required_config_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("HYDRA_DB_API_KEY", "hydra-secret")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-secret")
    monkeypatch.setenv("CRM_CLIENT_ID", "crm-client")
    monkeypatch.setenv("CRM_CLIENT_SECRET", "crm-secret")
    monkeypatch.setenv("CRM_WEBHOOK_SECRET", "crm-webhook")

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json()["runtime"] == "live-provider-ready"


def test_health_reports_codex_llm_configured_without_openai_key(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("CDI_LLM_PROVIDER", "codex")
    monkeypatch.setenv("CODEX_ACCESS_TOKEN", "codex-token")
    monkeypatch.setenv("HYDRA_DB_API_KEY", "hydra-secret")
    monkeypatch.setenv("CRM_CLIENT_ID", "crm-client")
    monkeypatch.setenv("CRM_CLIENT_SECRET", "crm-secret")
    monkeypatch.setenv("CRM_WEBHOOK_SECRET", "crm-webhook")

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["runtime"] == "live-provider-ready"
    assert body["llm_provider"] == "codex"
    assert body["llm_configured"] is True
    assert body["openai_configured"] is False


def test_ops_readiness_requires_tenant_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    clear_provider_env(monkeypatch)

    response = TestClient(app).get("/ops/readiness", params={"tenant_id": TEST_TENANT_ID})

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing authorization"


def test_ops_readiness_reports_missing_provider_names_without_secret_values(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("HYDRA_DB_API_KEY", "hydra-raw-secret")

    response = TestClient(app).get("/ops/readiness", headers=AUTH_HEADERS, params={"tenant_id": TEST_TENANT_ID})

    assert response.status_code == 200
    body = response.json()
    assert body["runtime"] == "provider-not-ready"
    assert {provider["name"] for provider in body["providers"]} == {"hydradb", "llm", "crm"}
    assert body["missing_providers"] == ["llm", "crm"]
    assert body["missing_config"] == ["OPENAI_API_KEY", "CRM_CLIENT_ID", "CRM_CLIENT_SECRET", "CRM_WEBHOOK_SECRET"]
    assert "hydra-raw-secret" not in response.text
    assert "test-token" not in response.text


def test_ops_readiness_accepts_codex_llm_auth_without_openai_key(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("CDI_LLM_PROVIDER", "codex")
    monkeypatch.setenv("CODEX_ACCESS_TOKEN", "codex-token")
    monkeypatch.setenv("HYDRA_DB_API_KEY", "hydra-secret")

    response = TestClient(app).get("/ops/readiness", headers=AUTH_HEADERS, params={"tenant_id": TEST_TENANT_ID})

    assert response.status_code == 200
    body = response.json()
    assert body["runtime"] == "provider-not-ready"
    assert body["missing_providers"] == ["crm"]
    assert body["missing_config"] == ["CRM_CLIENT_ID", "CRM_CLIENT_SECRET", "CRM_WEBHOOK_SECRET"]
    assert next(provider for provider in body["providers"] if provider["name"] == "llm") == {
        "name": "llm",
        "state": "ready",
        "missing_config": [],
    }


def test_ops_readiness_accepts_manual_crm_without_crm_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("CDI_LLM_PROVIDER", "codex")
    monkeypatch.setenv("CODEX_ACCESS_TOKEN", "codex-token")
    monkeypatch.setenv("HYDRA_DB_API_KEY", "hydra-secret")
    monkeypatch.setenv("CDI_CRM_PROVIDER", "manual")

    response = TestClient(app).get("/ops/readiness", headers=AUTH_HEADERS, params={"tenant_id": TEST_TENANT_ID})

    assert response.status_code == 200
    body = response.json()
    assert body["runtime"] == "live-provider-ready"
    assert body["missing_providers"] == []
    assert body["missing_config"] == []
    assert next(provider for provider in body["providers"] if provider["name"] == "crm") == {
        "name": "crm",
        "state": "ready",
        "missing_config": [],
    }


def test_ops_readiness_reports_demo_without_requiring_provider_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("CDI_DEMO_MODE", "1")

    response = TestClient(app).get("/ops/readiness", headers=AUTH_HEADERS, params={"tenant_id": TEST_TENANT_ID})

    assert response.status_code == 200
    assert response.json()["runtime"] == "local-demo"
