from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app.external import JsonMap
from app.ingestion import router as ingestion_router
from app.ingestion.causal_linker import build_causal_links
from app.ingestion.models import CausalLinkRecord, ChampionSignal, CompetitiveMentionSignal, EconomicBuyerPresence, ExtractedCallSignals, IngestCallRequest, ObjectionSignal, PriorDealState
from app.ingestion.service import HydraDbCallWriter, ingest_call
from app.main import app

TEST_TENANT_ID = "tenant_test"
AUTH_HEADERS = {"X-Tenant-Id": TEST_TENANT_ID, "Authorization": "Bearer test-token"}
TENANT_ID = "tenant_novaridge"
DEAL_ID = "deal_northstar_expansion"
CALL_ID = "call_ns_005"
TIMESTAMP = "2026-03-04T15:00:00.000Z"
TRANSCRIPT = "Marcus paused new spend until the logistics migration clears."


def configure_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CDI_TENANT_ID", TEST_TENANT_ID)
    monkeypatch.setenv("CDI_AUTH_TOKEN", "test-token")


def budget_discount_signals() -> ExtractedCallSignals:
    return ExtractedCallSignals(
        tenant_id=TENANT_ID,
        deal_id=DEAL_ID,
        call_id=CALL_ID,
        objections=(
            ObjectionSignal(type="budget_freeze", verbatim_quote=TRANSCRIPT, contact_id="contact_avi", severity="high"),
            ObjectionSignal(
                type="competitor_discount",
                verbatim_quote="Procurement asked whether the incumbent discount is safer for now.",
                contact_id="contact_avi",
                severity="high",
            ),
        ),
        champion_signals=(
            ChampionSignal(
                contact_id="contact_elena",
                signal_type="silence",
                evidence_quote="Elena has not replied to the revised proposal thread.",
            ),
        ),
        competitive_mentions=(
            CompetitiveMentionSignal(
                competitor_name="CallPilot",
                context="Procurement asked about extending the incumbent at a discount.",
                sentiment="positive",
            ),
        ),
        economic_buyer_presence=EconomicBuyerPresence(present=False),
    )


def ingest_request(transcript: str = TRANSCRIPT, call_id: str = CALL_ID) -> IngestCallRequest:
    return IngestCallRequest(
        tenant_id=TENANT_ID,
        deal_id=DEAL_ID,
        call_id=call_id,
        timestamp=TIMESTAMP,
        duration_seconds=1800,
        transcript=transcript,
    )


def transcript_payload(call_id: str) -> dict[str, str | int]:
    return {
        "tenant_id": TEST_TENANT_ID,
        "deal_id": DEAL_ID,
        "call_id": call_id,
        "timestamp": TIMESTAMP,
        "duration_seconds": 1800,
        "transcript": TRANSCRIPT,
    }


def prior_state(champion_was_silent: bool = False, economic_buyer_was_absent: bool = False) -> PriorDealState:
    return PriorDealState(
        tenant_id=TENANT_ID,
        deal_id=DEAL_ID,
        champion_was_silent=champion_was_silent,
        economic_buyer_was_absent=economic_buyer_was_absent,
    )


def prior_deal_memory() -> JsonMap:
    return {
        "record_type": "deal_memory",
        "tenant_id": TENANT_ID,
        "deal_id": DEAL_ID,
        "stage": "Proposal",
        "champion_id": "contact_elena",
        "economic_buyer_id": "contact_marcus",
        "champion_confidence": 0.72,
        "budget_confirmed": False,
        "technical_validated": True,
        "active_objections": [],
        "next_step_agreed": "Send rollout plan",
        "last_call_id": "call_ns_004",
        "valid_from": "2026-02-20T15:00:00.000Z",
        "valid_to": None,
    }


def contact_memory(engagement: str, valid_from: str) -> JsonMap:
    return {
        "record_type": "contact_memory",
        "tenant_id": TENANT_ID,
        "deal_id": DEAL_ID,
        "contact_id": "contact_elena",
        "role": "champion",
        "engagement_level": engagement,
        "valid_from": valid_from,
        "valid_to": None,
    }


class StaticExtractor:
    def __init__(self, signals: ExtractedCallSignals) -> None:
        self.signals = signals

    def extract_signals(self, transcript: str, tenant_id: str, deal_id: str, call_id: str) -> ExtractedCallSignals:
        return self.signals


class RecordingWriter:
    def __init__(self, state: PriorDealState | None = None) -> None:
        self.call_ids: list[str] = []
        self.causal_links: list[str] = []
        self.prior_state = state or prior_state()

    def read_prior_state(self, tenant_id: str, deal_id: str) -> PriorDealState:
        return self.prior_state

    def write_call(self, request: IngestCallRequest, signals: ExtractedCallSignals, links: tuple[CausalLinkRecord, ...]) -> str:
        self.call_ids.append(request.call_id)
        self.causal_links.extend(link.link_type for link in links)
        return request.call_id


class MemoryClient:
    def __init__(self, records: tuple[JsonMap, ...]) -> None:
        self.records = records
        self.written: tuple[JsonMap, ...] = ()

    def query_deal(self, tenant_id: str, deal_id: str) -> JsonMap:
        return {"results": list(self.records)}

    def ingest_memory(self, tenant_id: str, sub_tenant_id: str, records: tuple[JsonMap, ...]) -> JsonMap:
        self.written = records
        return {"job_id": "job_memory"}


def route_writer(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, extractor: StaticExtractor) -> RecordingWriter:
    writer = RecordingWriter()
    monkeypatch.setenv("CDI_JOB_STORE_PATH", str(tmp_path / "jobs.jsonl"))
    monkeypatch.setattr(ingestion_router.OpenAIClient, "from_settings", lambda settings: extractor)
    monkeypatch.setattr(ingestion_router.HydraDbClient, "from_settings", lambda settings: None)
    monkeypatch.setattr(ingestion_router, "HydraDbCallWriter", lambda client: writer)
    return writer


def test_causal_linker_writes_owned_high_confidence_links() -> None:
    links = build_causal_links(budget_discount_signals(), prior_state(True, True))
    assert [link.link_type for link in links] == [
        "champion_silence_triggered_budget_objection",
        "economic_buyer_absence_triggered_stall",
        "competitor_mention_triggered_pricing_concern",
    ]
    assert all(link.tenant_id == TENANT_ID and link.deal_id == DEAL_ID and link.confidence >= 0.6 for link in links)


def test_ingest_service_writes_real_call_records() -> None:
    writer = RecordingWriter(prior_state(True, True))
    result = ingest_call(ingest_request(), StaticExtractor(budget_discount_signals()), writer)
    assert result.written_call_event_id in writer.call_ids
    assert writer.causal_links == [
        "champion_silence_triggered_budget_objection",
        "economic_buyer_absence_triggered_stall",
        "competitor_mention_triggered_pricing_concern",
    ]


def test_ingest_service_does_not_invent_prior_causal_links() -> None:
    writer = RecordingWriter()
    result = ingest_call(ingest_request(), StaticExtractor(budget_discount_signals()), writer)
    assert result.written_call_event_id == CALL_ID
    assert writer.causal_links == ["competitor_mention_triggered_pricing_concern"]


def test_ingest_call_appends_deal_and_contact_memory_snapshots() -> None:
    client = MemoryClient((prior_deal_memory(),))
    result = ingest_call(ingest_request("Budget is frozen and Elena has gone quiet."), StaticExtractor(budget_discount_signals()), HydraDbCallWriter(client))
    deal_memory, contacts = next(record for record in client.written if record["record_type"] == "deal_memory"), [record for record in client.written if record["record_type"] == "contact_memory"]
    assert result.written_call_event_id == CALL_ID
    written_call_refs = {
        (record["record_type"], record.get("call_id") or record.get("evidence_call_id") or record.get("last_call_id") or record.get("last_seen_on_call")) for record in client.written
    }
    assert written_call_refs >= {("call_event", CALL_ID), ("causal_link", CALL_ID), ("deal_memory", CALL_ID), ("contact_memory", CALL_ID)}
    assert (deal_memory["active_objections"], deal_memory["last_call_id"], deal_memory["valid_from"], deal_memory["valid_to"]) == (["budget_freeze", "competitor_discount"], CALL_ID, TIMESTAMP, None)
    assert {(record["role"], record["engagement_level"], record["contact_id"]) for record in contacts} >= {
        ("champion", "silent", "contact_elena"),
        ("economic_buyer", "silent", "contact_marcus"),
    }


def test_prior_state_uses_latest_contact_memory_snapshot() -> None:
    client = MemoryClient((contact_memory("silent", "2026-02-20T15:00:00.000Z"), contact_memory("high", "2026-03-01T15:00:00.000Z")))
    result = ingest_call(ingest_request("Marcus paused spend."), StaticExtractor(budget_discount_signals()), HydraDbCallWriter(client))
    assert [link.link_type for link in result.causal_links] == ["competitor_mention_triggered_pricing_concern"]


def test_ingest_route_fails_closed_without_model_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_auth(monkeypatch)
    response = TestClient(app).post("/calls/ingest", headers=AUTH_HEADERS, json=transcript_payload(CALL_ID))
    assert response.status_code == 503
    assert response.json()["detail"] == "provider-not-ready: OPENAI_API_KEY"


def test_transcript_ingest_route_persists_completed_job(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    configure_auth(monkeypatch)
    route_writer(monkeypatch, tmp_path, StaticExtractor(budget_discount_signals()))
    client = TestClient(app)
    response = client.post("/calls/ingest", headers=AUTH_HEADERS, json=transcript_payload("call_ns_006"))
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    status = client.get(f"/calls/jobs/{response.json()['job_id']}", headers=AUTH_HEADERS)
    assert status.status_code == 200
    assert status.json()["status"] == "completed"
