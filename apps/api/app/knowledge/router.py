from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict

from app.auth import require_tenant_match
from app.config import get_settings
from app.external import HydraDbClient, JsonMap

KnowledgeRecordType = Literal["playbook", "battlecard", "icp_definition", "source_fact", "integration_fact"]


class KnowledgeIngestRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="allow")

    tenant_id: str
    record_type: KnowledgeRecordType
    id: str


router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/ingest")
def ingest_knowledge(request: KnowledgeIngestRequest, http_request: Request) -> JsonMap:
    settings = get_settings()
    require_tenant_match(request.tenant_id, http_request.state.tenant_id)
    return HydraDbClient.from_settings(settings).ingest_knowledge(
        request.tenant_id,
        (request.model_dump(mode="json"),),
    )
