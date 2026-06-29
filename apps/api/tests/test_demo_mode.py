from fastapi.testclient import TestClient
import pytest

from app.demo import demo_pipeline_query
from app.main import app
from app.records import records_by_type, records_from_query

TEST_TENANT_ID = "tenant_test"
DEAL_ID = "deal_northstar_expansion"
AUTH_HEADERS = {"X-Tenant-Id": TEST_TENANT_ID, "Authorization": "Bearer test-token"}


def configure_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CDI_TENANT_ID", TEST_TENANT_ID)
    monkeypatch.setenv("CDI_AUTH_TOKEN", "test-token")


def configure_demo(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    monkeypatch.setenv("CDI_DEMO_MODE", "1")
    monkeypatch.delenv("HYDRA_DB_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def test_context_route_fails_closed_without_demo_or_hydradb(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    monkeypatch.delenv("CDI_DEMO_MODE", raising=False)
    monkeypatch.delenv("HYDRA_DB_API_KEY", raising=False)

    response = TestClient(app).get(
        f"/deals/{DEAL_ID}/context",
        headers=AUTH_HEADERS,
        params={"tenant_id": TEST_TENANT_ID},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "provider-not-ready: HYDRA_DB_API_KEY"


def test_demo_context_returns_seeded_deal_without_provider_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_demo(monkeypatch)

    response = TestClient(app).get(
        f"/deals/{DEAL_ID}/context",
        headers=AUTH_HEADERS,
        params={"tenant_id": TEST_TENANT_ID},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["tenant"]["name"] == "Northstar Robotics"
    assert body["deal"]["id"] == DEAL_ID
    assert body["deal_memory"]["active_objections"] == ["budget_freeze"]
    assert {node["id"] for node in body["knowledge_nodes"]} >= {
        "source_fact_crm_stage",
        "integration_fact_crm_amount",
    }


def test_demo_context_matches_web_contract_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_demo(monkeypatch)

    response = TestClient(app).get(
        f"/deals/{DEAL_ID}/context",
        headers=AUTH_HEADERS,
        params={"tenant_id": TEST_TENANT_ID},
    )

    assert response.status_code == 200
    body = response.json()
    assert {"id", "name", "domain", "environment"} <= body["tenant"].keys()
    assert {"id", "tenant_id", "account_name", "name", "owner_name", "amount_usd", "stage", "status", "close_date"} <= body[
        "deal"
    ].keys()
    assert {"id", "tenant_id", "deal_id", "name", "title", "email"} <= body["contacts"][0].keys()
    assert body["contact_memories"]
    assert {
        "contact_id",
        "deal_id",
        "tenant_id",
        "role",
        "engagement_level",
        "last_seen_on_call",
        "last_seen_timestamp",
        "sentiment_trend",
        "key_concerns",
        "valid_from",
        "valid_to",
    } <= body["contact_memories"][0].keys()
    assert {
        "call_id",
        "deal_id",
        "tenant_id",
        "timestamp",
        "duration_seconds",
        "participants",
        "objections_raised",
        "commitments_made",
        "sentiment_shifts",
        "competitive_mentions",
        "champion_behavior",
        "summary",
    } <= body["call_events"][0].keys()
    evidence_call = next(call for call in body["call_events"] if call["objections_raised"])
    assert {"type", "verbatim_quote", "contact_id", "severity"} <= evidence_call["objections_raised"][0].keys()
    assert {"type", "made_by_contact_id", "due_date", "verbatim"} <= evidence_call["commitments_made"][0].keys()
    assert {"contact_id", "from", "to", "timestamp_in_call", "trigger_quote"} <= evidence_call["sentiment_shifts"][0].keys()
    assert {"competitor_name", "context", "sentiment"} <= evidence_call["competitive_mentions"][0].keys()
    assert {"contact_id", "signal_type", "evidence_quote"} <= evidence_call["champion_behavior"].keys()
    assert {"tenant_id", "deal_id", "from_node_id", "to_node_id", "link_type", "confidence", "evidence_call_id", "created_at"} <= body[
        "causal_links"
    ][0].keys()
    assert {"id", "tenant_id", "kind", "record"} <= body["knowledge_nodes"][0].keys()


def test_demo_timeline_replays_seeded_point_in_time(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_demo(monkeypatch)

    response = TestClient(app).get(
        f"/deals/{DEAL_ID}/timeline",
        headers=AUTH_HEADERS,
        params={"tenant_id": TEST_TENANT_ID, "as_of": "2026-02-10T15:00:00.000Z"},
    )

    assert response.status_code == 200
    body = response.json()
    assert [snapshot["stage"] for snapshot in body["snapshots"]] == ["Discovery", "Proposal"]
    assert body["point_in_time"]["deal_memory"]["stage"] == "Discovery"
    assert body["point_in_time"]["call_event_ids"] == ["call_ns_001"]


def test_demo_intelligence_returns_cited_briefing_without_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_demo(monkeypatch)

    response = TestClient(app).get(
        f"/intelligence/deal/{DEAL_ID}",
        headers=AUTH_HEADERS,
        params={"tenant_id": TEST_TENANT_ID},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["deal_id"] == DEAL_ID
    assert body["risk_flags"][0]["evidence_node_id"] == "deal_northstar_expansion:deal_memory:2026-03-04T15:00:00.000Z"
    assert body["next_best_actions"][0]["cited_knowledge_node_id"] == "source_fact_crm_stage"


def test_demo_pipeline_summary_returns_seeded_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_demo(monkeypatch)

    response = TestClient(app).get(
        "/pipeline/summary",
        headers=AUTH_HEADERS,
        params={"tenant_id": TEST_TENANT_ID},
    )

    assert response.status_code == 200
    assert response.json() == {
        "tenant_id": TEST_TENANT_ID,
        "deal_count": 2,
        "open_deal_count": 2,
        "total_pipeline_amount": 212000.0,
        "weighted_forecast_amount": 131280.0,
        "at_risk_deal_count": 1,
        "source_fact_count": 2,
        "integration_fact_count": 2,
        "risks": [{"deal_id": DEAL_ID, "active_objections": ["budget_freeze"]}],
    }


def test_demo_pipeline_seed_covers_production_breadth(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_demo(monkeypatch)

    records = records_from_query(demo_pipeline_query(TEST_TENANT_ID))

    assert len(records_by_type(records, "account")) == 2
    assert len(records_by_type(records, "user")) == 2
    assert len(records_by_type(records, "deal")) == 2
    assert len(records_by_type(records, "call_event")) >= 3
    assert len(records_by_type(records, "forecast_submission")) == 1
    assert len(records_by_type(records, "coaching_scorecard")) == 1
    assert len(records_by_type(records, "engagement_task")) == 2
    assert len(records_by_type(records, "audit_event")) == 1
    assert len(records_by_type(records, "export_job")) == 1


def test_demo_mode_still_requires_verified_tenant(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_demo(monkeypatch)

    response = TestClient(app).get(
        f"/deals/{DEAL_ID}/context",
        headers=AUTH_HEADERS,
        params={"tenant_id": "tenant_other"},
    )

    assert response.status_code == 403
