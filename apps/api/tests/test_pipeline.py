from fastapi.testclient import TestClient
import pytest

from app.external import JsonMap
from app.main import app

TEST_TENANT_ID = "tenant_test"
AUTH_HEADERS = {"X-Tenant-Id": TEST_TENANT_ID, "Authorization": "Bearer test-token"}


def configure_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CDI_TENANT_ID", TEST_TENANT_ID)
    monkeypatch.setenv("CDI_AUTH_TOKEN", "test-token")


class EmptyPipelineHttp:
    def post_json(self, path: str, payload: JsonMap) -> JsonMap:
        return {"results": []}


class EmptyPipelineHydraClient:
    http = EmptyPipelineHttp()

    @classmethod
    def from_settings(cls, settings) -> "EmptyPipelineHydraClient":
        return cls()


class PipelineHttp:
    def post_json(self, path: str, payload: JsonMap) -> JsonMap:
        assert path == "/query"
        assert payload["tenant_id"] == TEST_TENANT_ID
        return {
            "results": [
                {"record_type": "deal", "tenant_id": TEST_TENANT_ID, "deal_id": "deal_1", "id": "deal_1", "amount": 100000, "stage": "Proposal", "forecast_probability": 0.5},
                {"record_type": "deal", "tenant_id": TEST_TENANT_ID, "deal_id": "deal_2", "id": "deal_2", "amount": 50000, "stage": "Closed Won", "forecast_probability": 1},
                {"record_type": "deal_memory", "tenant_id": TEST_TENANT_ID, "deal_id": "deal_1", "id": "memory_1", "active_objections": ["budget_freeze"]},
                {"record_type": "source_fact", "tenant_id": TEST_TENANT_ID, "deal_id": "deal_1", "id": "source_1"},
                {"record_type": "integration_fact", "tenant_id": TEST_TENANT_ID, "deal_id": "deal_2", "id": "integration_1"},
            ]
        }


class PipelineHydraClient:
    http = PipelineHttp()

    @classmethod
    def from_settings(cls, settings) -> "PipelineHydraClient":
        return cls()


def test_pipeline_summary_fails_closed_without_hydradb_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    monkeypatch.delenv("HYDRA_DB_API_KEY", raising=False)

    response = TestClient(app).get(
        "/pipeline/summary",
        headers=AUTH_HEADERS,
        params={"tenant_id": TEST_TENANT_ID},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "provider-not-ready: HYDRA_DB_API_KEY"


def test_pipeline_summary_computes_metrics_from_records(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    monkeypatch.setenv("HYDRA_DB_API_KEY", "hydra-key")
    monkeypatch.setattr("app.pipeline.router.HydraDbClient", PipelineHydraClient)

    response = TestClient(app).get(
        "/pipeline/summary",
        headers=AUTH_HEADERS,
        params={"tenant_id": TEST_TENANT_ID},
    )

    assert response.status_code == 200
    assert response.json() == {
        "tenant_id": TEST_TENANT_ID,
        "deal_count": 2,
        "open_deal_count": 1,
        "total_pipeline_amount": 150000.0,
        "weighted_forecast_amount": 100000.0,
        "at_risk_deal_count": 1,
        "source_fact_count": 1,
        "integration_fact_count": 1,
        "risks": [{"deal_id": "deal_1", "active_objections": ["budget_freeze"]}],
    }


def test_pipeline_summary_uses_shared_deal_record_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    monkeypatch.setenv("HYDRA_DB_API_KEY", "hydra-key")

    class SharedShapeHttp:
        def post_json(self, path: str, payload: JsonMap) -> JsonMap:
            return {
                "results": [
                    {"record_type": "deal", "tenant_id": TEST_TENANT_ID, "id": "deal_shared_shape", "amount_usd": 250000, "stage": "Proposal", "forecast_probability": 0.4},
                    {"record_type": "deal_memory", "tenant_id": TEST_TENANT_ID, "deal_id": "deal_shared_shape", "active_objections": ["legal_review"]},
                ]
            }

    class SharedShapeHydraClient:
        http = SharedShapeHttp()

        @classmethod
        def from_settings(cls, settings) -> "SharedShapeHydraClient":
            return cls()

    monkeypatch.setattr("app.pipeline.router.HydraDbClient", SharedShapeHydraClient)

    response = TestClient(app).get(
        "/pipeline/summary",
        headers=AUTH_HEADERS,
        params={"tenant_id": TEST_TENANT_ID},
    )

    assert response.status_code == 200
    assert response.json()["total_pipeline_amount"] == 250000.0
    assert response.json()["weighted_forecast_amount"] == 100000.0
    assert response.json()["risks"] == [{"deal_id": "deal_shared_shape", "active_objections": ["legal_review"]}]


def test_pipeline_summary_respects_zero_amount_and_probability(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    monkeypatch.setenv("HYDRA_DB_API_KEY", "hydra-key")

    class ZeroValueHttp:
        def post_json(self, path: str, payload: JsonMap) -> JsonMap:
            return {
                "results": [
                    {"record_type": "deal", "tenant_id": TEST_TENANT_ID, "id": "deal_zero", "amount_usd": 0, "stage": "Proposal", "forecast_probability": 0},
                    {"record_type": "integration_fact", "tenant_id": TEST_TENANT_ID, "deal_id": "deal_zero", "amount": 999999, "probability": 1},
                ]
            }

    class ZeroValueHydraClient:
        http = ZeroValueHttp()

        @classmethod
        def from_settings(cls, settings) -> "ZeroValueHydraClient":
            return cls()

    monkeypatch.setattr("app.pipeline.router.HydraDbClient", ZeroValueHydraClient)

    response = TestClient(app).get(
        "/pipeline/summary",
        headers=AUTH_HEADERS,
        params={"tenant_id": TEST_TENANT_ID},
    )

    assert response.status_code == 200
    assert response.json()["total_pipeline_amount"] == 0.0
    assert response.json()["weighted_forecast_amount"] == 0.0


def test_pipeline_summary_uses_latest_memory_for_risk(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    monkeypatch.setenv("HYDRA_DB_API_KEY", "hydra-key")

    class MemoryArcHttp:
        def post_json(self, path: str, payload: JsonMap) -> JsonMap:
            return {
                "results": [
                    {"record_type": "deal", "tenant_id": TEST_TENANT_ID, "id": "deal_memory_arc", "amount_usd": 1000, "stage": "Proposal"},
                    {
                        "record_type": "deal_memory",
                        "tenant_id": TEST_TENANT_ID,
                        "deal_id": "deal_memory_arc",
                        "valid_from": "2026-01-01T00:00:00.000Z",
                        "active_objections": ["budget_freeze"],
                    },
                    {
                        "record_type": "deal_memory",
                        "tenant_id": TEST_TENANT_ID,
                        "deal_id": "deal_memory_arc",
                        "valid_from": "2026-02-01T00:00:00.000Z",
                        "active_objections": [],
                    },
                ]
            }

    class MemoryArcHydraClient:
        http = MemoryArcHttp()

        @classmethod
        def from_settings(cls, settings) -> "MemoryArcHydraClient":
            return cls()

    monkeypatch.setattr("app.pipeline.router.HydraDbClient", MemoryArcHydraClient)

    response = TestClient(app).get(
        "/pipeline/summary",
        headers=AUTH_HEADERS,
        params={"tenant_id": TEST_TENANT_ID},
    )

    assert response.status_code == 200
    assert response.json()["at_risk_deal_count"] == 0
    assert response.json()["risks"] == []


def test_pipeline_summary_returns_zeroes_without_records(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    monkeypatch.setenv("HYDRA_DB_API_KEY", "hydra-key")
    monkeypatch.setattr("app.pipeline.router.HydraDbClient", EmptyPipelineHydraClient)

    response = TestClient(app).get(
        "/pipeline/summary",
        headers=AUTH_HEADERS,
        params={"tenant_id": TEST_TENANT_ID},
    )

    assert response.status_code == 200
    assert response.json()["deal_count"] == 0
    assert response.json()["total_pipeline_amount"] == 0.0
