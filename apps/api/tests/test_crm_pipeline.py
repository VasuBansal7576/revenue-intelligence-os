from fastapi.testclient import TestClient
import pytest

from app.external import JsonMap
from app.main import app

TEST_TENANT_ID = "tenant_test"
AUTH_HEADERS = {"X-Tenant-Id": TEST_TENANT_ID, "Authorization": "Bearer test-token"}


def configure_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CDI_TENANT_ID", TEST_TENANT_ID)
    monkeypatch.setenv("CDI_AUTH_TOKEN", "test-token")


def configure_crm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CRM_CLIENT_ID", "crm-client")
    monkeypatch.setenv("CRM_CLIENT_SECRET", "crm-secret")
    monkeypatch.setenv("CRM_WEBHOOK_SECRET", "crm-webhook")


def clear_crm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CRM_CLIENT_ID", raising=False)
    monkeypatch.delenv("CRM_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("CRM_WEBHOOK_SECRET", raising=False)
    monkeypatch.delenv("CDI_CRM_PROVIDER", raising=False)


class RecordingHydraClient:
    def __init__(self) -> None:
        self.tenant_id = ""
        self.records: tuple[JsonMap, ...] = ()

    def ingest_knowledge(self, tenant_id: str, records: tuple[JsonMap, ...]) -> JsonMap:
        self.tenant_id = tenant_id
        self.records = records
        return {"status": "accepted", "job_id": "crm_job_1"}

    @classmethod
    def from_settings(cls, settings) -> "RecordingHydraClient":
        return cls()


def test_crm_sync_fails_closed_without_crm_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    monkeypatch.setenv("HYDRA_DB_API_KEY", "hydra-key")
    clear_crm(monkeypatch)

    response = TestClient(app).post(
        "/crm/sync",
        headers=AUTH_HEADERS,
        json={"tenant_id": TEST_TENANT_ID, "provider": "salesforce"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "provider-not-ready: CRM_CLIENT_ID"


def test_manual_crm_sync_writes_record_without_crm_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    clear_crm(monkeypatch)
    monkeypatch.setenv("CDI_CRM_PROVIDER", "manual")
    monkeypatch.setenv("HYDRA_DB_API_KEY", "hydra-key")
    client = RecordingHydraClient()
    monkeypatch.setattr("app.crm.router.HydraDbClient", type("HydraFactory", (), {"from_settings": classmethod(lambda cls, settings: client)}))

    response = TestClient(app).post(
        "/crm/sync",
        headers=AUTH_HEADERS,
        json={
            "tenant_id": TEST_TENANT_ID,
            "provider": "manual",
            "record_type": "integration_fact",
            "deal_id": "deal_1",
            "stage": "Proposal",
            "amount": 100000,
        },
    )

    assert response.status_code == 200
    assert response.json() == {"status": "accepted", "job_id": "crm_job_1"}
    assert client.records[0]["source"] == "crm:manual"
    assert client.records[0]["stage"] == "Proposal"


def test_crm_sync_fails_closed_without_hydradb_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    configure_crm(monkeypatch)
    monkeypatch.delenv("HYDRA_DB_API_KEY", raising=False)

    response = TestClient(app).post(
        "/crm/sync",
        headers=AUTH_HEADERS,
        json={"tenant_id": TEST_TENANT_ID, "provider": "hubspot"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "provider-not-ready: HYDRA_DB_API_KEY"


def test_crm_sync_rejects_tenant_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)

    response = TestClient(app).post(
        "/crm/sync",
        headers=AUTH_HEADERS,
        json={"tenant_id": "tenant_other", "provider": "salesforce"},
    )

    assert response.status_code == 403


def test_crm_sync_writes_scoped_source_record(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    configure_crm(monkeypatch)
    monkeypatch.setenv("HYDRA_DB_API_KEY", "hydra-key")
    client = RecordingHydraClient()
    monkeypatch.setattr("app.crm.router.HydraDbClient", type("HydraFactory", (), {"from_settings": classmethod(lambda cls, settings: client)}))

    response = TestClient(app).post(
        "/crm/sync",
        headers=AUTH_HEADERS,
        json={
            "tenant_id": TEST_TENANT_ID,
            "provider": "salesforce",
            "record_type": "source_fact",
            "deal_id": "deal_1",
            "source_record_id": "opp_123",
            "stage": "Proposal",
            "amount": 100000,
        },
    )

    assert response.status_code == 200
    assert response.json() == {"status": "accepted", "job_id": "crm_job_1"}
    assert client.tenant_id == TEST_TENANT_ID
    assert client.records == (
        {
            "tenant_id": TEST_TENANT_ID,
            "provider": "salesforce",
            "record_type": "source_fact",
            "id": "source_fact:salesforce:opp_123",
            "source": "crm:salesforce",
            "deal_id": "deal_1",
            "source_record_id": "opp_123",
            "stage": "Proposal",
            "amount": 100000.0,
            "content": "CRM salesforce source record opp_123",
        },
    )
