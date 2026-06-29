from datetime import UTC, datetime
from pathlib import Path

from app.config import Settings
from app.ingestion.models import IngestCallRequest, IngestCallResponse, IngestionJobRecord

DEFAULT_JOB_STORE_PATH = ".cdi/ingestion-jobs.jsonl"


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class FileIngestionJobStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    @classmethod
    def from_settings(cls, settings: Settings) -> "FileIngestionJobStore":
        return cls(Path(settings.job_store_path or DEFAULT_JOB_STORE_PATH))

    def start(self, request: IngestCallRequest, source: str, job_id: str) -> IngestionJobRecord:
        now = utc_now()
        job = IngestionJobRecord(
            job_id=job_id,
            tenant_id=request.tenant_id,
            deal_id=request.deal_id,
            call_id=request.call_id,
            source=source,
            status="running",
            created_at=now,
            updated_at=now,
        )
        self.save(job)
        return job

    def complete(self, job: IngestionJobRecord, response: IngestCallResponse) -> IngestionJobRecord:
        completed = job.model_copy(
            update={
                "status": "completed",
                "updated_at": utc_now(),
                "written_call_event_id": response.written_call_event_id,
                "causal_links": response.causal_links,
            }
        )
        self.save(completed)
        return completed

    def fail(self, job: IngestionJobRecord, detail: str) -> IngestionJobRecord:
        failed = job.model_copy(update={"status": "failed", "updated_at": utc_now(), "error_detail": detail})
        self.save(failed)
        return failed

    def get(self, job_id: str) -> IngestionJobRecord | None:
        latest: IngestionJobRecord | None = None
        try:
            with self.path.open() as handle:
                for line in handle:
                    job = IngestionJobRecord.model_validate_json(line)
                    if job.job_id == job_id:
                        latest = job
        except FileNotFoundError:
            return None
        return latest

    def save(self, job: IngestionJobRecord) -> None:
        # ponytail: append-only file store is enough here; move to DB-backed leases when workers run concurrently.
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as handle:
            handle.write(f"{job.model_dump_json()}\n")
