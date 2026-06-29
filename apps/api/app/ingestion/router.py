from fastapi import APIRouter, HTTPException, Request, status
from pydantic import ValidationError
from starlette.datastructures import FormData, UploadFile

from app.auth import require_tenant_match
from app.config import MissingConfigurationError, get_settings
from app.external import HydraDbClient, OpenAIClient, UpstreamServiceError
from app.ingestion.jobs import FileIngestionJobStore
from app.ingestion.models import IngestAudioForm, IngestCallRequest, IngestCallResponse, IngestionJobRecord
from app.ingestion.service import HydraDbCallWriter, ingest_call
from app.transcription import transcribe_audio

router = APIRouter(prefix="/calls", tags=["calls"])


@router.post("/ingest", response_model=IngestCallResponse)
def ingest_call_route(request: IngestCallRequest, http_request: Request) -> IngestCallResponse:
    require_tenant_match(request.tenant_id, http_request.state.tenant_id)
    settings = get_settings()
    store = FileIngestionJobStore.from_settings(settings)
    job = store.start(request, "transcript", f"call.ingest:{request.call_id}")
    try:
        response = ingest_call(
            request,
            extractor=OpenAIClient.from_settings(settings),
            writer=HydraDbCallWriter(HydraDbClient.from_settings(settings)),
        )
    except (MissingConfigurationError, UpstreamServiceError, ValidationError) as error:
        store.fail(job, str(error))
        raise
    store.complete(job, response)
    return response


def parse_audio_form(form_data: FormData) -> tuple[IngestAudioForm, UploadFile]:
    try:
        form = IngestAudioForm.model_validate(
            {
                "tenant_id": form_data.get("tenant_id"),
                "deal_id": form_data.get("deal_id"),
                "call_id": form_data.get("call_id"),
                "timestamp": form_data.get("timestamp"),
                "duration_seconds": form_data.get("duration_seconds"),
            }
        )
    except ValidationError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=error.errors()) from error
    match form_data.get("file"):
        case UploadFile() as file:
            return form, file
        case _:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Missing file")


@router.post("/ingest/audio", response_model=IngestCallResponse)
async def ingest_audio_route(http_request: Request) -> IngestCallResponse:
    form, file = parse_audio_form(await http_request.form())
    require_tenant_match(form.tenant_id, http_request.state.tenant_id)
    settings = get_settings()
    request = form.to_request("")
    store = FileIngestionJobStore.from_settings(settings)
    job = store.start(request, "audio", f"call.audio:{form.call_id}")
    try:
        openai = OpenAIClient.from_settings(settings)
        transcript = transcribe_audio(
            settings,
            openai,
            file.filename or "audio",
            await file.read(),
            file.content_type or "application/octet-stream",
        )
        response = ingest_call(
            form.to_request(transcript),
            extractor=openai,
            writer=HydraDbCallWriter(HydraDbClient.from_settings(settings)),
        )
        response = response.model_copy(update={"job_id": job.job_id})
    except (MissingConfigurationError, UpstreamServiceError, ValidationError) as error:
        store.fail(job, str(error))
        raise
    store.complete(job, response)
    return response


@router.get("/jobs/{job_id}", response_model=IngestionJobRecord)
def get_ingestion_job(job_id: str, request: Request) -> IngestionJobRecord:
    job = FileIngestionJobStore.from_settings(get_settings()).get(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    require_tenant_match(job.tenant_id, request.state.tenant_id)
    return job
