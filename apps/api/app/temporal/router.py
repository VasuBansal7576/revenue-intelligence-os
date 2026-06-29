from datetime import datetime

from fastapi import APIRouter, Query, Request

from app.auth import require_tenant_match
from app.config import get_settings
from app.demo import demo_query_deal
from app.external import HydraDbClient
from app.temporal.models import DealTimelineResponse
from app.temporal.timeline import build_timeline_response

router = APIRouter(prefix="/deals", tags=["deal-timeline"])


@router.get("/{deal_id}/timeline", response_model=DealTimelineResponse)
async def get_deal_timeline(
    deal_id: str,
    request: Request,
    tenant_id: str = Query(...),
    as_of: datetime | None = Query(default=None),
) -> DealTimelineResponse:
    require_tenant_match(tenant_id, request.state.tenant_id)
    settings = get_settings()
    query_response = (
        demo_query_deal(tenant_id, deal_id)
        if settings.demo_mode
        else HydraDbClient.from_settings(settings).query_deal(tenant_id, deal_id)
    )
    return build_timeline_response(query_response=query_response, deal_id=deal_id, tenant_id=tenant_id, as_of=as_of)
