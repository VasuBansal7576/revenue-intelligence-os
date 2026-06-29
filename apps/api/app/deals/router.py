from fastapi import APIRouter, Query, Request

from app.auth import require_tenant_match
from app.config import get_settings
from app.demo import demo_query_deal
from app.external import HydraDbClient, JsonMap
from app.records import build_deal_context

router = APIRouter(prefix="/deals", tags=["deals"])


@router.get("/{deal_id}/context")
def get_deal_context(deal_id: str, request: Request, tenant_id: str = Query(...)) -> JsonMap:
    require_tenant_match(tenant_id, request.state.tenant_id)
    settings = get_settings()
    query_response = (
        demo_query_deal(tenant_id, deal_id)
        if settings.demo_mode
        else HydraDbClient.from_settings(settings).query_deal(tenant_id, deal_id)
    )
    return build_deal_context(query_response, deal_id, tenant_id)
