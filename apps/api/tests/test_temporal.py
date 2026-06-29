from datetime import UTC, datetime

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.records import build_deal_context
from app.temporal.timeline import build_timeline_response

TEST_TENANT_ID = "tenant_test"
AUTH_HEADERS = {"X-Tenant-Id": TEST_TENANT_ID, "Authorization": "Bearer test-token"}
QUERY_RESPONSE = {
    "results": [
        {
            "record_type": "deal_memory",
            "tenant_id": TEST_TENANT_ID,
            "deal_id": "deal_northstar_expansion",
            "stage": "Discovery",
            "champion_id": "contact_elena",
            "economic_buyer_id": "contact_marcus",
            "champion_confidence": 0.82,
            "budget_confirmed": False,
            "technical_validated": False,
            "active_objections": [],
            "next_step_agreed": "Share technical validation plan",
            "last_call_id": "call_ns_001",
            "valid_from": "2026-02-04T15:00:00.000Z",
            "valid_to": "2026-02-18T15:00:00.000Z",
        },
        {
            "record_type": "deal_memory",
            "tenant_id": TEST_TENANT_ID,
            "deal_id": "deal_northstar_expansion",
            "stage": "Proposal",
            "champion_id": "contact_elena",
            "economic_buyer_id": "contact_marcus",
            "champion_confidence": 0.34,
            "budget_confirmed": False,
            "technical_validated": True,
            "active_objections": ["budget_freeze"],
            "next_step_agreed": "Send revised rollout plan to CFO",
            "last_call_id": "call_ns_005",
            "valid_from": "2026-03-04T15:00:00.000Z",
            "valid_to": None,
        },
        {
            "record_type": "call_event",
            "id": "call_ns_001",
            "tenant_id": TEST_TENANT_ID,
            "deal_id": "deal_northstar_expansion",
            "timestamp": "2026-02-04T15:00:00.000Z",
        },
        {
            "record_type": "call_event",
            "id": "call_ns_005",
            "tenant_id": TEST_TENANT_ID,
            "deal_id": "deal_northstar_expansion",
            "timestamp": "2026-03-04T15:00:00.000Z",
        },
    ]
}


def configure_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CDI_TENANT_ID", TEST_TENANT_ID)
    monkeypatch.setenv("CDI_AUTH_TOKEN", "test-token")


def test_build_timeline_returns_ordered_snapshots() -> None:
    timeline = build_timeline_response(
        query_response=QUERY_RESPONSE,
        deal_id="deal_northstar_expansion",
        tenant_id=TEST_TENANT_ID,
        as_of=None,
    )

    assert [snapshot.stage for snapshot in timeline.snapshots] == [
        "Discovery",
        "Proposal",
    ]
    assert [snapshot.valid_from for snapshot in timeline.snapshots] == sorted(
        snapshot.valid_from for snapshot in timeline.snapshots
    )
    assert timeline.point_in_time is None


def test_build_timeline_replays_point_in_time_state() -> None:
    discovery = build_timeline_response(
        query_response=QUERY_RESPONSE,
        deal_id="deal_northstar_expansion",
        tenant_id=TEST_TENANT_ID,
        as_of=datetime(2026, 2, 10, 15, tzinfo=UTC),
    )
    proposal = build_timeline_response(
        query_response=QUERY_RESPONSE,
        deal_id="deal_northstar_expansion",
        tenant_id=TEST_TENANT_ID,
        as_of=datetime(2026, 3, 5, 15, tzinfo=UTC),
    )

    assert discovery.point_in_time is not None
    assert discovery.point_in_time.deal_memory.stage == "Discovery"
    assert discovery.point_in_time.call_event_ids == ("call_ns_001",)
    assert proposal.point_in_time is not None
    assert proposal.point_in_time.deal_memory.stage == "Proposal"
    assert "call_ns_005" in proposal.point_in_time.call_event_ids


def test_replay_uses_latest_appended_snapshot_at_boundary() -> None:
    query_response = {
        "results": [
            QUERY_RESPONSE["results"][1] | {"valid_from": "2026-02-20T15:00:00.000Z"},
            QUERY_RESPONSE["results"][0] | {"valid_from": "2026-03-04T15:00:00.000Z", "valid_to": None},
        ]
    }

    before = build_timeline_response(
        query_response=query_response,
        deal_id="deal_northstar_expansion",
        tenant_id=TEST_TENANT_ID,
        as_of=datetime(2026, 3, 1, 15, tzinfo=UTC),
    )
    at_snapshot = build_timeline_response(
        query_response=query_response,
        deal_id="deal_northstar_expansion",
        tenant_id=TEST_TENANT_ID,
        as_of=datetime(2026, 3, 4, 15, tzinfo=UTC),
    )

    assert before.point_in_time is not None
    assert before.point_in_time.deal_memory.stage == "Proposal"
    assert at_snapshot.point_in_time is not None
    assert at_snapshot.point_in_time.deal_memory.stage == "Discovery"


def test_current_context_uses_latest_deal_memory_snapshot() -> None:
    context = build_deal_context(
        {
            "results": [
                {"record_type": "tenant", "id": TEST_TENANT_ID},
                {
                    "record_type": "deal",
                    "tenant_id": TEST_TENANT_ID,
                    "deal_id": "deal_northstar_expansion",
                    "id": "deal_northstar_expansion",
                },
                QUERY_RESPONSE["results"][1],
                QUERY_RESPONSE["results"][0],
            ]
        },
        "deal_northstar_expansion",
        TEST_TENANT_ID,
    )

    assert context["deal_memory"]["last_call_id"] == "call_ns_005"


def test_timeline_route_scopes_by_tenant(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    client = TestClient(app)

    tenant_mismatch = client.get(
        "/deals/deal_northstar_expansion/timeline",
        headers=AUTH_HEADERS,
        params={"tenant_id": "tenant_other"},
    )

    assert tenant_mismatch.status_code == 403


def test_timeline_route_fails_closed_without_hydradb_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    client = TestClient(app)

    response = client.get(
        "/deals/deal_northstar_expansion/timeline",
        headers=AUTH_HEADERS,
        params={
            "tenant_id": TEST_TENANT_ID,
            "as_of": "2026-02-10T15:00:00.000Z",
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "provider-not-ready: HYDRA_DB_API_KEY"
