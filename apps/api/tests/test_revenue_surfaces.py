from fastapi.testclient import TestClient
import pytest

from app.main import app

TEST_TENANT_ID = "tenant_test"
AUTH_HEADERS = {"X-Tenant-Id": TEST_TENANT_ID, "Authorization": "Bearer test-token"}


def configure_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CDI_TENANT_ID", TEST_TENANT_ID)
    monkeypatch.setenv("CDI_AUTH_TOKEN", "test-token")


def configure_demo(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    monkeypatch.setenv("CDI_DEMO_MODE", "1")
    monkeypatch.delenv("HYDRA_DB_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def test_library_routes_return_demo_records(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_demo(monkeypatch)
    client = TestClient(app)

    accounts = client.get("/accounts", headers=AUTH_HEADERS, params={"tenant_id": TEST_TENANT_ID})
    account = client.get("/accounts/account_northstar", headers=AUTH_HEADERS, params={"tenant_id": TEST_TENANT_ID})
    deals = client.get("/deals", headers=AUTH_HEADERS, params={"tenant_id": TEST_TENANT_ID})
    calls = client.get("/calls", headers=AUTH_HEADERS, params={"tenant_id": TEST_TENANT_ID})
    call = client.get("/calls/call_ns_005", headers=AUTH_HEADERS, params={"tenant_id": TEST_TENANT_ID})
    search = client.get("/search", headers=AUTH_HEADERS, params={"tenant_id": TEST_TENANT_ID, "q": "Northstar"})

    assert accounts.status_code == 200
    assert {item["id"] for item in accounts.json()["items"]} == {"account_northstar", "account_atlas"}
    assert account.status_code == 200
    assert account.json()["id"] == "account_northstar"
    assert deals.status_code == 200
    assert {item["id"] for item in deals.json()["items"]} == {"deal_northstar_expansion", "deal_atlas_renewal"}
    assert calls.status_code == 200
    assert {item["call_id"] for item in calls.json()["items"]} >= {"call_ns_001", "call_ns_005", "call_at_003"}
    assert call.status_code == 200
    assert call.json()["summary"] == "Budget freeze and CFO silence made the proposal-stage deal risky."
    assert search.status_code == 200
    assert "account_northstar" in {item["id"] for item in search.json()["items"]}


def test_library_routes_fail_closed_in_provider_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    monkeypatch.delenv("CDI_DEMO_MODE", raising=False)
    monkeypatch.delenv("HYDRA_DB_API_KEY", raising=False)

    response = TestClient(app).get("/accounts", headers=AUTH_HEADERS, params={"tenant_id": TEST_TENANT_ID})

    assert response.status_code == 503
    assert response.json()["detail"] == "provider-not-ready: HYDRA_DB_API_KEY"


def test_forecast_coaching_and_engage_routes_return_demo_records(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_demo(monkeypatch)
    client = TestClient(app)

    forecast = client.get("/forecast/summary", headers=AUTH_HEADERS, params={"tenant_id": TEST_TENANT_ID})
    submissions = client.get("/forecast/submissions", headers=AUTH_HEADERS, params={"tenant_id": TEST_TENANT_ID})
    scorecards = client.get("/coaching/scorecards", headers=AUTH_HEADERS, params={"tenant_id": TEST_TENANT_ID})
    rep = client.get("/coaching/reps/user_maya", headers=AUTH_HEADERS, params={"tenant_id": TEST_TENANT_ID})
    tasks = client.get("/engage/tasks", headers=AUTH_HEADERS, params={"tenant_id": TEST_TENANT_ID})
    task = client.get("/engage/tasks/task_followup_cfo", headers=AUTH_HEADERS, params={"tenant_id": TEST_TENANT_ID})
    mutation = client.patch("/engage/tasks/task_followup_cfo", headers=AUTH_HEADERS, params={"tenant_id": TEST_TENANT_ID})

    assert forecast.status_code == 200
    assert forecast.json()["forecast_category"] == "best_case"
    assert forecast.json()["weighted_forecast_amount"] == 131280.0
    assert submissions.status_code == 200
    assert submissions.json()["items"][0]["id"] == "forecast_2026_03_maya"
    assert scorecards.status_code == 200
    assert scorecards.json()["items"][0]["rep_id"] == "user_maya"
    assert rep.status_code == 200
    assert rep.json()["risk_rows"][0]["improvement_areas"] == ["secure direct CFO next step"]
    assert tasks.status_code == 200
    assert {item["id"] for item in tasks.json()["items"]} == {"task_followup_cfo", "task_atlas_redlines"}
    assert task.status_code == 200
    assert task.json()["status"] == "open"
    assert mutation.status_code == 405


def test_forecast_route_rejects_tenant_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_demo(monkeypatch)

    response = TestClient(app).get(
        "/forecast/summary",
        headers=AUTH_HEADERS,
        params={"tenant_id": "tenant_other"},
    )

    assert response.status_code == 403


def test_revenue_workflow_routes_fail_closed_in_provider_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    monkeypatch.delenv("CDI_DEMO_MODE", raising=False)
    monkeypatch.delenv("HYDRA_DB_API_KEY", raising=False)

    response = TestClient(app).get("/engage/tasks", headers=AUTH_HEADERS, params={"tenant_id": TEST_TENANT_ID})

    assert response.status_code == 503
    assert response.json()["detail"] == "provider-not-ready: HYDRA_DB_API_KEY"


def test_assistant_admin_audit_and_exports_return_demo_records(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_demo(monkeypatch)
    client = TestClient(app)

    assistant = client.post(
        "/assistant/query",
        headers=AUTH_HEADERS,
        params={"tenant_id": TEST_TENANT_ID},
        json={"question": "why is Northstar risky?"},
    )
    users = client.get("/admin/users", headers=AUTH_HEADERS, params={"tenant_id": TEST_TENANT_ID})
    settings = client.get("/admin/settings", headers=AUTH_HEADERS, params={"tenant_id": TEST_TENANT_ID})
    audit = client.get("/audit/events", headers=AUTH_HEADERS, params={"tenant_id": TEST_TENANT_ID})
    exports = client.get("/exports", headers=AUTH_HEADERS, params={"tenant_id": TEST_TENANT_ID})
    export = client.get("/exports/export_pipeline_snapshot", headers=AUTH_HEADERS, params={"tenant_id": TEST_TENANT_ID})

    assert assistant.status_code == 200
    assert assistant.json()["answer"] == "Northstar is risky because CFO budget approval stalled after champion silence."
    assert assistant.json()["citations"] == ["call_ns_005", "deal_northstar_expansion:deal_memory:2026-03-04T15:00:00.000Z"]
    assert users.status_code == 200
    assert {item["id"] for item in users.json()["items"]} == {"user_maya", "user_owen"}
    assert settings.status_code == 200
    assert settings.json()["items"][0]["key"] == "exports.enabled"
    assert audit.status_code == 200
    assert audit.json()["items"][0]["action"] == "export.created"
    assert exports.status_code == 200
    assert exports.json()["items"][0]["status"] == "ready"
    assert export.status_code == 200
    assert export.json()["status"] == "ready"


def test_assistant_fails_closed_without_provider_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    monkeypatch.delenv("CDI_DEMO_MODE", raising=False)
    monkeypatch.delenv("HYDRA_DB_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = TestClient(app).post(
        "/assistant/query",
        headers=AUTH_HEADERS,
        params={"tenant_id": TEST_TENANT_ID},
        json={"question": "why is Northstar risky?"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "provider-not-ready: HYDRA_DB_API_KEY, OPENAI_API_KEY"
