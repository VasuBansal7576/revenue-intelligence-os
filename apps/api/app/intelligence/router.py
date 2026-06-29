from fastapi import APIRouter, Query, Request

from app.auth import require_tenant_match
from app.config import get_settings
from app.demo import demo_briefing, demo_query_deal
from app.external import HydraDbClient, OpenAIClient
from app.intelligence.briefing_builder import enforce_cited_briefing, knowledge_node_ids, memory_node_ids
from app.intelligence.models import DealBriefing
from app.records import build_deal_context

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


@router.get("/deal/{deal_id}", response_model=DealBriefing)
def get_deal_intelligence(deal_id: str, request: Request, tenant_id: str = Query(...)) -> DealBriefing:
    require_tenant_match(tenant_id, request.state.tenant_id)
    settings = get_settings()
    query_response = (
        demo_query_deal(tenant_id, deal_id)
        if settings.demo_mode
        else HydraDbClient.from_settings(settings).query_deal(tenant_id, deal_id)
    )
    context = build_deal_context(query_response, deal_id, tenant_id)
    briefing = (
        demo_briefing(deal_id)
        if settings.demo_mode
        else OpenAIClient.from_settings(settings).build_briefing(deal_id, context)
    )
    return enforce_cited_briefing(briefing, memory_node_ids(context), knowledge_node_ids(context))
