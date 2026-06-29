from fastapi.testclient import TestClient
import pytest

from app.external import JsonMap
from app.knowledge.router import HydraDbClient
from app.main import app

TEST_TENANT_ID = "tenant_test"
AUTH_HEADERS = {"X-Tenant-Id": TEST_TENANT_ID, "Authorization": "Bearer test-token"}


def configure_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CDI_TENANT_ID", TEST_TENANT_ID)
    monkeypatch.setenv("CDI_AUTH_TOKEN", "test-token")


class RecordingKnowledgeClient:
    def __init__(self) -> None:
        self.tenant_id = ""
        self.records: tuple[JsonMap, ...] = ()

    def ingest_knowledge(self, tenant_id: str, records: tuple[JsonMap, ...]) -> JsonMap:
        self.tenant_id = tenant_id
        self.records = records
        return {"status": "accepted", "job_id": "knowledge_job_1"}


def playbook_payload(record_type: str = "playbook", tenant_id: str = TEST_TENANT_ID) -> JsonMap:
    return {
        "tenant_id": tenant_id,
        "record_type": record_type,
        "id": "playbook_test",
        "stage": "Proposal",
        "title": "Test",
        "content": "Use cited evidence.",
        "objection_handlers": [],
        "version": 1,
        "active": True,
    }


@pytest.mark.parametrize("record_type", ("playbook", "battlecard", "icp_definition", "source_fact", "integration_fact"))
def test_knowledge_ingest_sends_valid_record_to_hydradb(monkeypatch: pytest.MonkeyPatch, record_type: str) -> None:
    configure_auth(monkeypatch)
    client = RecordingKnowledgeClient()
    monkeypatch.setattr(HydraDbClient, "from_settings", lambda settings: client)

    response = TestClient(app).post("/knowledge/ingest", headers=AUTH_HEADERS, json=playbook_payload(record_type))

    assert response.status_code == 200
    assert response.json() == {"status": "accepted", "job_id": "knowledge_job_1"}
    assert client.tenant_id == TEST_TENANT_ID
    assert client.records == (playbook_payload(record_type),)


def test_knowledge_ingest_requires_authorization(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)

    response = TestClient(app).post("/knowledge/ingest", json=playbook_payload())

    assert response.status_code == 401


def test_knowledge_ingest_rejects_bad_record_type(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)

    response = TestClient(app).post("/knowledge/ingest", headers=AUTH_HEADERS, json=playbook_payload("deal_memory"))

    assert response.status_code == 422


def test_knowledge_ingest_rejects_tenant_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)

    response = TestClient(app).post(
        "/knowledge/ingest",
        headers=AUTH_HEADERS,
        json=playbook_payload(tenant_id="tenant_other"),
    )

    assert response.status_code == 403


def test_knowledge_ingest_fails_closed_without_hydradb_key(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    monkeypatch.delenv("HYDRA_DB_API_KEY", raising=False)

    response = TestClient(app).post("/knowledge/ingest", headers=AUTH_HEADERS, json=playbook_payload())

    assert response.status_code == 503
    assert response.json()["detail"] == "provider-not-ready: HYDRA_DB_API_KEY"
