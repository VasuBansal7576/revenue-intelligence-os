from pathlib import Path
import sys

from fastapi.testclient import TestClient
import pytest

from app.ingestion import router as ingestion_router
from app.ingestion.models import CausalLinkRecord, ChampionSignal, CompetitiveMentionSignal, EconomicBuyerPresence, ExtractedCallSignals, IngestCallRequest, ObjectionSignal, PriorDealState
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


def audio_form(call_id: str, duration_seconds: str = "1") -> dict[str, str]:
    return {
        "tenant_id": TEST_TENANT_ID,
        "deal_id": DEAL_ID,
        "call_id": call_id,
        "timestamp": TIMESTAMP,
        "duration_seconds": duration_seconds,
    }


def prior_state() -> PriorDealState:
    return PriorDealState(
        tenant_id=TENANT_ID,
        deal_id=DEAL_ID,
        champion_was_silent=False,
        economic_buyer_was_absent=False,
    )


class StaticExtractor:
    def __init__(self, signals: ExtractedCallSignals) -> None:
        self.signals = signals
        self.transcripts: list[str] = []

    def extract_signals(self, transcript: str, tenant_id: str, deal_id: str, call_id: str) -> ExtractedCallSignals:
        self.transcripts.append(transcript)
        return self.signals


class RecordingWriter:
    def __init__(self) -> None:
        self.call_ids: list[str] = []
        self.causal_links: list[str] = []

    def read_prior_state(self, tenant_id: str, deal_id: str) -> PriorDealState:
        return prior_state()

    def write_call(self, request: IngestCallRequest, signals: ExtractedCallSignals, links: tuple[CausalLinkRecord, ...]) -> str:
        self.call_ids.append(request.call_id)
        self.causal_links.extend(link.link_type for link in links)
        return request.call_id


class RecordingTranscriber(StaticExtractor):
    def __init__(self, signals: ExtractedCallSignals) -> None:
        super().__init__(signals)
        self.files: list[tuple[str, bytes, str]] = []

    def transcribe_audio(self, filename: str, content: bytes, content_type: str) -> str:
        self.files.append((filename, content, content_type))
        return TRANSCRIPT


def route_writer(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, extractor: StaticExtractor) -> RecordingWriter:
    writer = RecordingWriter()
    monkeypatch.setenv("CDI_JOB_STORE_PATH", str(tmp_path / "jobs.jsonl"))
    monkeypatch.setattr(ingestion_router.OpenAIClient, "from_settings", lambda settings: extractor)
    monkeypatch.setattr(ingestion_router.HydraDbClient, "from_settings", lambda settings: None)
    monkeypatch.setattr(ingestion_router, "HydraDbCallWriter", lambda client: writer)
    return writer


def test_audio_ingest_route_transcribes_then_persists_job(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    configure_auth(monkeypatch)
    transcriber = RecordingTranscriber(budget_discount_signals())
    route_writer(monkeypatch, tmp_path, transcriber)
    client = TestClient(app)
    response = client.post(
        "/calls/ingest/audio",
        headers=AUTH_HEADERS,
        data=audio_form("call_audio_001"),
        files={"file": ("call.wav", b"RIFFdata", "audio/wav")},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert transcriber.files == [("call.wav", b"RIFFdata", "audio/wav")]
    status = client.get(f"/calls/jobs/{response.json()['job_id']}", headers=AUTH_HEADERS)
    assert status.status_code == 200
    assert (status.json()["status"], status.json()["source"]) == ("completed", "audio")


def test_audio_ingest_route_accepts_local_transcription_command(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    configure_auth(monkeypatch)
    script = tmp_path / "transcribe.py"
    script.write_text(f"from pathlib import Path\nPath(__import__('sys').argv[1]).read_bytes()\nprint({TRANSCRIPT!r})\n")
    extractor = StaticExtractor(budget_discount_signals())
    route_writer(monkeypatch, tmp_path, extractor)
    monkeypatch.setenv("CDI_TRANSCRIPTION_COMMAND", f"{sys.executable} {script} {{audio_path}}")
    monkeypatch.setenv("CDI_LLM_PROVIDER", "codex")
    monkeypatch.setenv("CODEX_ACCESS_TOKEN", "codex-token")

    response = TestClient(app).post(
        "/calls/ingest/audio",
        headers=AUTH_HEADERS,
        data=audio_form("call_audio_local"),
        files={"file": ("call.wav", b"RIFFdata", "audio/wav")},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert extractor.transcripts == [TRANSCRIPT]


def test_audio_ingest_route_fails_closed_without_openai_key(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    configure_auth(monkeypatch)
    monkeypatch.setenv("CDI_JOB_STORE_PATH", str(tmp_path / "jobs.jsonl"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    response = TestClient(app).post(
        "/calls/ingest/audio",
        headers=AUTH_HEADERS,
        data=audio_form("call_audio_002"),
        files={"file": ("call.wav", b"not audio", "audio/wav")},
    )
    assert response.status_code == 503
    assert response.json()["detail"] == "provider-not-ready: OPENAI_API_KEY"


@pytest.mark.parametrize(
    ("data", "files"),
    [
        (audio_form("call_audio_003"), {}),
        (audio_form("call_audio_004", "abc"), {"file": ("call.wav", b"not audio", "audio/wav")}),
    ],
)
def test_audio_ingest_route_rejects_malformed_upload(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    data: dict[str, str],
    files: dict[str, tuple[str, bytes, str]],
) -> None:
    configure_auth(monkeypatch)
    monkeypatch.setenv("CDI_JOB_STORE_PATH", str(tmp_path / "jobs.jsonl"))
    response = TestClient(app).post("/calls/ingest/audio", headers=AUTH_HEADERS, data=data, files=files)
    assert response.status_code == 422
