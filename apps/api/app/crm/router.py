from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field

from app.auth import require_tenant_match
from app.config import get_settings, require_config
from app.external import HydraDbClient, JsonMap

CrmRecordType = Literal["source_fact", "integration_fact"]


class CrmSyncRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    tenant_id: str
    provider: str = Field(min_length=1)
    record_type: CrmRecordType = "integration_fact"
    id: str | None = None
    deal_id: str | None = None
    source_record_id: str | None = None
    stage: str | None = None
    amount: float | None = None
    content: str | None = None


router = APIRouter(prefix="/crm", tags=["crm"])


@router.post("/sync")
def sync_crm_record(payload: CrmSyncRequest, request: Request) -> JsonMap:
    require_tenant_match(payload.tenant_id, request.state.tenant_id)
    settings = get_settings()
    if settings.crm_provider != "manual":
        require_config(settings.crm_client_id, "CRM_CLIENT_ID")
        require_config(settings.crm_client_secret, "CRM_CLIENT_SECRET")
        require_config(settings.crm_webhook_secret, "CRM_WEBHOOK_SECRET")
    return HydraDbClient.from_settings(settings).ingest_knowledge(
        payload.tenant_id,
        (crm_record(payload),),
    )


def crm_record(payload: CrmSyncRequest) -> JsonMap:
    source_record_id = payload.source_record_id or payload.id or payload.provider
    record: JsonMap = {
        "tenant_id": payload.tenant_id,
        "provider": payload.provider,
        "record_type": payload.record_type,
        "id": payload.id or f"{payload.record_type}:{payload.provider}:{source_record_id}",
        "source": f"crm:{payload.provider}",
        "content": payload.content or f"CRM {payload.provider} source record {source_record_id}",
    }
    if payload.deal_id is not None:
        record["deal_id"] = payload.deal_id
    if payload.source_record_id is not None:
        record["source_record_id"] = payload.source_record_id
    if payload.stage is not None:
        record["stage"] = payload.stage
    if payload.amount is not None:
        record["amount"] = payload.amount
    return record
