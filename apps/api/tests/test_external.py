import json
from urllib import error, request

import pytest

from app.config import MissingConfigurationError, get_settings
from app.external import HydraDbClient, JsonHttpClient, OpenAIClient, UpstreamServiceError, parse_json_map
from app.ingestion.models import ExtractedCallSignals


class FakeResponse:
    def __init__(self, body: str) -> None:
        self.body = body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, traceback) -> None:
        return None

    def read(self) -> bytes:
        return self.body.encode("utf-8")


class UrlOpenRecorder:
    def __init__(self, response_body: str) -> None:
        self.response_body = response_body
        self.requests: list[request.Request] = []
        self.timeouts: list[float] = []

    def __call__(self, req: request.Request, timeout: float) -> FakeResponse:
        self.requests.append(req)
        self.timeouts.append(timeout)
        return FakeResponse(self.response_body)


def request_body(req: request.Request) -> str:
    data = req.data
    assert data is not None
    return data.decode("utf-8")


def request_headers(req: request.Request) -> dict[str, str]:
    return dict(req.header_items())


def test_config_reads_provider_contract_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CDI_LLM_PROVIDER", "codex")
    monkeypatch.setenv("CODEX_ACCESS_TOKEN", "codex-token")
    monkeypatch.setenv("CDI_LLM_MODEL", "gpt-5.3-codex")
    monkeypatch.setenv("OPENAI_TRANSCRIPTION_MODEL", "gpt-4o-mini-transcribe")
    monkeypatch.setenv("CDI_JOB_STORE_PATH", "/tmp/cdi-jobs.jsonl")
    monkeypatch.setenv("CDI_CRM_PROVIDER", "manual")
    monkeypatch.setenv("CRM_CLIENT_ID", "crm-client")
    monkeypatch.setenv("CRM_CLIENT_SECRET", "crm-secret")
    monkeypatch.setenv("CRM_WEBHOOK_SECRET", "crm-webhook")
    monkeypatch.setenv("CDI_SERVICE_TOKEN_HMAC_SECRET", "claims-secret")
    monkeypatch.setenv("CDI_SERVICE_TOKEN_ISSUER", "cdi")
    monkeypatch.setenv("CDI_SERVICE_TOKEN_AUDIENCE", "providers")

    settings = get_settings()

    assert settings.llm_provider == "codex"
    assert settings.codex_access_token == "codex-token"
    assert settings.openai_model == "gpt-5.3-codex"
    assert settings.openai_transcription_model == "gpt-4o-mini-transcribe"
    assert settings.job_store_path == "/tmp/cdi-jobs.jsonl"
    assert settings.crm_provider == "manual"
    assert settings.crm_client_id == "crm-client"
    assert settings.crm_client_secret == "crm-secret"
    assert settings.crm_webhook_secret == "crm-webhook"
    assert settings.service_token_hmac_secret == "claims-secret"
    assert settings.service_token_issuer == "cdi"
    assert settings.service_token_audience == "providers"


def test_hydradb_memory_knowledge_and_status_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    recorder = UrlOpenRecorder('{"status":"accepted","job_id":"job_123"}')
    monkeypatch.setattr("app.external.request.urlopen", recorder)
    client = HydraDbClient(
        JsonHttpClient(
            base_url="https://hydra.test",
            bearer_token="hydra-token",
            service="HydraDB",
            timeout_seconds=2.5,
            api_version="2",
        )
    )

    client.ingest_memory("tenant_a", "deal_a", ({"record_type": "call_event", "id": "call_1"},))
    client.ingest_knowledge("tenant_a", ({"record_type": "playbook", "id": "playbook_1", "content": "Use proof."},))
    status = client.ingest_status("job_123")

    assert [req.full_url for req in recorder.requests] == [
        "https://hydra.test/context/ingest",
        "https://hydra.test/context/ingest",
        "https://hydra.test/context/ingest/status/job_123",
    ]
    assert recorder.timeouts == [2.5, 2.5, 2.5]
    assert "type=memory" not in request_body(recorder.requests[0])
    assert '"type": "memory"' not in request_body(recorder.requests[0])
    assert 'name="type"' in request_body(recorder.requests[0])
    assert "memory" in request_body(recorder.requests[0])
    assert "knowledge" in request_body(recorder.requests[1])
    assert "playbook_1" in request_body(recorder.requests[1])
    assert request_headers(recorder.requests[2])["Authorization"] == "Bearer hydra-token"
    assert request_headers(recorder.requests[2])["Api-version"] == "2"
    assert status == {"status": "accepted", "job_id": "job_123"}


def test_openai_audio_transcription_request_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    recorder = UrlOpenRecorder('{"text":"transcript text"}')
    monkeypatch.setattr("app.external.request.urlopen", recorder)
    client = OpenAIClient(
        http=JsonHttpClient(
            base_url="https://api.openai.test/v1",
            bearer_token="openai-token",
            service="OpenAI",
            timeout_seconds=4,
        ),
        model="gpt-5.5",
        transcription_model="gpt-4o-mini-transcribe",
    )

    transcript = client.transcribe_audio("call.wav", b"RIFFdata", "audio/wav")

    req = recorder.requests[0]
    body = request_body(req)
    headers = request_headers(req)
    assert transcript == "transcript text"
    assert req.full_url == "https://api.openai.test/v1/audio/transcriptions"
    assert headers["Authorization"] == "Bearer openai-token"
    assert headers["Content-type"].startswith("multipart/form-data; boundary=")
    assert 'name="model"' in body
    assert "gpt-4o-mini-transcribe" in body
    assert 'name="file"; filename="call.wav"' in body
    assert "Content-Type: audio/wav" in body
    assert "RIFFdata" in body


def test_openai_extract_signals_parses_nested_responses_output_text(monkeypatch: pytest.MonkeyPatch) -> None:
    output = {
        "tenant_id": "tenant_a",
        "deal_id": "deal_a",
        "call_id": "call_a",
        "objections": [
            {
                "type": "budget",
                "verbatim_quote": "We need finance approval.",
                "contact_id": "contact_1",
                "severity": "medium",
            }
        ],
        "next_steps_agreed": ["Send ROI memo"],
    }
    recorder = UrlOpenRecorder(json.dumps({"output": [{"content": [{"output_text": json.dumps(output)}]}]}))
    monkeypatch.setattr("app.external.request.urlopen", recorder)
    client = OpenAIClient(
        http=JsonHttpClient(
            base_url="https://api.openai.test/v1",
            bearer_token="openai-token",
            service="OpenAI",
            timeout_seconds=4,
        ),
        model="gpt-5.5",
        transcription_model="gpt-4o-mini-transcribe",
    )

    signals = client.extract_signals("We need finance approval.", "tenant_a", "deal_a", "call_a")

    assert isinstance(signals, ExtractedCallSignals)
    assert signals.tenant_id == "tenant_a"
    assert signals.deal_id == "deal_a"
    assert signals.call_id == "call_a"
    assert signals.objections[0].verbatim_quote == "We need finance approval."
    assert signals.next_steps_agreed == ("Send ROI memo",)
    assert recorder.requests[0].full_url == "https://api.openai.test/v1/responses"


def test_provider_errors_do_not_leak_secret_like_values(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_urlopen(req: request.Request, timeout: float) -> FakeResponse:
        raise error.HTTPError(req.full_url, 500, "secret-token-abc123", {}, None)

    monkeypatch.setattr("app.external.request.urlopen", fail_urlopen)
    client = JsonHttpClient(
        base_url="https://secret-token-abc123@hydra.test",
        bearer_token="hydra-token",
        service="HydraDB",
        timeout_seconds=1,
    )

    with pytest.raises(UpstreamServiceError) as raised:
        client.post_json("/query", {"tenant_id": "tenant_a"})

    message = str(raised.value)
    assert message == "HydraDB: HTTP 500"
    assert "secret-token" not in message
    assert "hydra-token" not in message


def test_malformed_json_from_provider_is_typed_error() -> None:
    with pytest.raises(UpstreamServiceError) as raised:
        parse_json_map("{bad-json", "HydraDB")

    assert str(raised.value) == "HydraDB: response was not valid JSON"


def test_provider_clients_fail_closed_without_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HYDRA_DB_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("CDI_LLM_PROVIDER", raising=False)
    settings = get_settings()

    with pytest.raises(MissingConfigurationError) as hydra_error:
        HydraDbClient.from_settings(settings)
    with pytest.raises(MissingConfigurationError) as openai_error:
        OpenAIClient.from_settings(settings)

    assert str(hydra_error.value) == "Missing required configuration: HYDRA_DB_API_KEY"
    assert str(openai_error.value) == "Missing required configuration: OPENAI_API_KEY"


def test_codex_llm_provider_uses_codex_auth_file(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    auth_file = tmp_path / "auth.json"
    auth_file.write_text(json.dumps({"tokens": {"access_token": "codex-token-from-file"}}))
    monkeypatch.setenv("CDI_LLM_PROVIDER", "codex")
    monkeypatch.setenv("CODEX_AUTH_FILE", str(auth_file))
    monkeypatch.delenv("CODEX_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    client = OpenAIClient.from_settings(get_settings())

    assert client.http.base_url == "https://chatgpt.com/backend-api/codex"
    assert client.http.bearer_token == "codex-token-from-file"
    assert client.http.service == "OpenAI Codex"
    assert client.model == "gpt-5.3-codex"


def test_codex_llm_provider_does_not_claim_audio_transcription(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CDI_LLM_PROVIDER", "codex")
    monkeypatch.setenv("CODEX_ACCESS_TOKEN", "codex-token")

    client = OpenAIClient.from_settings(get_settings())

    with pytest.raises(MissingConfigurationError) as raised:
        client.transcribe_audio("call.wav", b"RIFFdata", "audio/wav")

    assert str(raised.value) == "Missing required configuration: OPENAI_API_KEY"
