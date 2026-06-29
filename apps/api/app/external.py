from dataclasses import dataclass
import json
from typing import Mapping
from urllib import error, request

from app.config import MissingConfigurationError, Settings, require_config
from app.ingestion.models import ExtractedCallSignals
from app.intelligence.models import DealBriefing

type JsonValue = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
type JsonMap = dict[str, JsonValue]


@dataclass(frozen=True, slots=True)
class UpstreamServiceError(Exception):
    service: str
    detail: str

    def __str__(self) -> str:
        return f"{self.service}: {self.detail}"


@dataclass(frozen=True, slots=True)
class JsonHttpClient:
    base_url: str
    bearer_token: str
    service: str
    timeout_seconds: float = 30.0
    api_version: str | None = None

    def post_json(self, path: str, payload: JsonMap) -> JsonMap:
        body = json.dumps(payload).encode("utf-8")
        return parse_json_map(self._send("POST", path, body, self._headers("application/json")), self.service)

    def post_form(self, path: str, fields: Mapping[str, str]) -> JsonMap:
        boundary = "cdi-boundary"
        body = encode_multipart(fields, boundary)
        return parse_json_map(
            self._send("POST", path, body, self._headers(f"multipart/form-data; boundary={boundary}")),
            self.service,
        )

    def post_multipart_file(
        self,
        path: str,
        fields: Mapping[str, str],
        file_field: str,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> JsonMap:
        boundary = "cdi-boundary"
        body = encode_multipart_file(fields, file_field, filename, content, content_type, boundary)
        return parse_json_map(
            self._send("POST", path, body, self._headers(f"multipart/form-data; boundary={boundary}")),
            self.service,
        )

    def get_json(self, path: str) -> JsonMap:
        response = self._send("GET", path, None, self._headers("application/json"))
        return parse_json_map(response, self.service)

    def _headers(self, content_type: str) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {self.bearer_token}", "Content-Type": content_type}
        if self.api_version is not None:
            headers["API-Version"] = self.api_version
        return headers

    def _send(self, method: str, path: str, body: bytes | None, headers: Mapping[str, str]) -> str:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        req = request.Request(url, data=body, headers=dict(headers), method=method)
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                return response.read().decode("utf-8")
        except error.HTTPError as upstream_error:
            raise UpstreamServiceError(service=self.service, detail=f"HTTP {upstream_error.code}") from upstream_error
        except error.URLError as upstream_error:
            raise UpstreamServiceError(service=self.service, detail="request failed") from upstream_error
        except TimeoutError as upstream_error:
            raise UpstreamServiceError(service=self.service, detail="request timed out") from upstream_error


def encode_multipart(fields: Mapping[str, str], boundary: str) -> bytes:
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.extend([
            f"--{boundary}\r\n".encode("utf-8"),
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"),
            value.encode("utf-8"),
            b"\r\n",
        ])
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks)


def encode_multipart_file(
    fields: Mapping[str, str],
    file_field: str,
    filename: str,
    content: bytes,
    content_type: str,
    boundary: str,
) -> bytes:
    chunks = [
        encode_multipart(fields, boundary).removesuffix(f"--{boundary}--\r\n".encode("utf-8")),
        f"--{boundary}\r\n".encode("utf-8"),
        f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\n'.encode("utf-8"),
        f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
        content,
        b"\r\n",
        f"--{boundary}--\r\n".encode("utf-8"),
    ]
    return b"".join(chunks)


def parse_json_map(raw: str, service: str) -> JsonMap:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as decode_error:
        raise UpstreamServiceError(service=service, detail="response was not valid JSON") from decode_error
    match parsed:
        case dict():
            return parsed
        case _:
            raise UpstreamServiceError(service=service, detail="response was not a JSON object")


def hydra_document(record: JsonMap, fallback_title: str) -> JsonMap:
    return {"title": str(record.get("id", record.get("record_type", fallback_title))), "text": json.dumps(record)}


def response_format(name: str, schema: JsonMap) -> JsonMap:
    return {"format": {"type": "json_schema", "name": name, "schema": schema, "strict": True}}


@dataclass(frozen=True, slots=True)
class HydraDbClient:
    http: JsonHttpClient

    @classmethod
    def from_settings(cls, settings: Settings) -> "HydraDbClient":
        return cls(
            http=JsonHttpClient(
                base_url=settings.hydradb_base_url,
                bearer_token=require_config(settings.hydradb_api_key, "HYDRA_DB_API_KEY"),
                service="HydraDB",
                timeout_seconds=settings.provider_timeout_seconds,
                api_version="2",
            )
        )

    def ingest_memory(self, tenant_id: str, sub_tenant_id: str, records: tuple[JsonMap, ...]) -> JsonMap:
        memories = tuple(hydra_document(record, "cdi_record") | {"infer": False} for record in records)
        return self.http.post_form(
            "/context/ingest",
            {
                "type": "memory",
                "tenant_id": tenant_id,
                "sub_tenant_id": sub_tenant_id,
                "memories": json.dumps(memories),
            },
        )

    def ingest_knowledge(self, tenant_id: str, records: tuple[JsonMap, ...]) -> JsonMap:
        knowledge = tuple(
            hydra_document(record, "cdi_knowledge")
            | {"metadata": {"tenant_id": tenant_id, "record_type": record.get("record_type")}}
            for record in records
        )
        return self.http.post_form(
            "/context/ingest",
            {
                "type": "knowledge",
                "tenant_id": tenant_id,
                "knowledge": json.dumps(knowledge),
            },
        )

    def ingest_status(self, job_id: str) -> JsonMap:
        return self.http.get_json(f"/context/ingest/status/{job_id}")

    def query_deal(self, tenant_id: str, deal_id: str) -> JsonMap:
        return self.http.post_json(
            "/query",
            {
                "tenant_id": tenant_id,
                "query": f"deal_id:{deal_id}",
                "type": "all",
                "query_by": "hybrid",
                "mode": "thinking",
                "max_results": 50,
                "graph_context": True,
                "metadata_filters": {"deal_id": deal_id},
            },
        )


@dataclass(frozen=True, slots=True)
class OpenAIClient:
    http: JsonHttpClient
    model: str
    transcription_model: str
    supports_audio: bool = True

    @classmethod
    def from_settings(cls, settings: Settings) -> "OpenAIClient":
        if settings.llm_provider == "codex":
            return cls(
                http=JsonHttpClient(
                    base_url=settings.codex_base_url,
                    bearer_token=require_config(settings.codex_access_token, "CODEX_ACCESS_TOKEN or ~/.codex/auth.json"),
                    service="OpenAI Codex",
                    timeout_seconds=settings.provider_timeout_seconds,
                ),
                model=settings.openai_model,
                transcription_model=settings.openai_transcription_model,
                supports_audio=False,
            )
        return cls(
            http=JsonHttpClient(
                base_url="https://api.openai.com/v1",
                bearer_token=require_config(settings.openai_api_key, "OPENAI_API_KEY"),
                service="OpenAI",
                timeout_seconds=settings.provider_timeout_seconds,
            ),
            model=settings.openai_model,
            transcription_model=settings.openai_transcription_model,
        )

    def extract_signals(self, transcript: str, tenant_id: str, deal_id: str, call_id: str) -> ExtractedCallSignals:
        payload = {
            "model": self.model,
            "input": [
                {"role": "system", "content": "Extract sales-call signals as JSON matching the provided schema. Do not invent evidence."},
                {
                    "role": "user",
                    "content": json.dumps({"tenant_id": tenant_id, "deal_id": deal_id, "call_id": call_id, "transcript": transcript}),
                },
            ],
            "text": response_format("extracted_call_signals", ExtractedCallSignals.model_json_schema()),
        }
        return ExtractedCallSignals.model_validate_json(extract_output_text(self.http.post_json("/responses", payload), self.http.service))

    def build_briefing(self, deal_id: str, context: JsonMap) -> DealBriefing:
        payload = {
            "model": self.model,
            "input": [
                {"role": "system", "content": "Return a cited causal deal briefing. Every action must cite an existing memory or knowledge node id."},
                {"role": "user", "content": json.dumps(context)},
            ],
            "text": response_format("deal_briefing", DealBriefing.model_json_schema()),
        }
        briefing = DealBriefing.model_validate_json(extract_output_text(self.http.post_json("/responses", payload), self.http.service))
        if briefing.deal_id == deal_id:
            return briefing
        raise UpstreamServiceError(service=self.http.service, detail="briefing deal_id mismatch")

    def transcribe_audio(self, filename: str, content: bytes, content_type: str) -> str:
        if not self.supports_audio:
            raise MissingConfigurationError(name="OPENAI_API_KEY")
        response = self.http.post_multipart_file(
            "/audio/transcriptions", {"model": self.transcription_model}, "file", filename, content, content_type
        )
        return extract_output_text(response, self.http.service)


def extract_output_text(value: JsonValue, service: str) -> str:
    match value:
        case {"output_text": str(text)}:
            return text
        case {"text": str(text)}:
            return text
        case list() as items:
            for item in items:
                try:
                    return extract_output_text(item, service)
                except UpstreamServiceError:
                    continue
        case dict() as items:
            for item in items.values():
                try:
                    return extract_output_text(item, service)
                except UpstreamServiceError:
                    continue
        case _:
            pass
    raise UpstreamServiceError(service=service, detail="JSON text output was not found")
