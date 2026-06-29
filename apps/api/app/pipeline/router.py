from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, ConfigDict

from app.auth import require_tenant_match
from app.config import get_settings
from app.demo import demo_pipeline_query
from app.external import HydraDbClient, JsonMap, JsonValue
from app.records import records_by_type, records_from_query, string_field, strings_field, valid_from_time


class PipelineRisk(BaseModel):
    model_config = ConfigDict(frozen=True)

    deal_id: str
    active_objections: tuple[str, ...]


class PipelineSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    tenant_id: str
    deal_count: int
    open_deal_count: int
    total_pipeline_amount: float
    weighted_forecast_amount: float
    at_risk_deal_count: int
    source_fact_count: int
    integration_fact_count: int
    risks: tuple[PipelineRisk, ...]


router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/summary", response_model=PipelineSummary)
def pipeline_summary(request: Request, tenant_id: str = Query(...)) -> PipelineSummary:
    require_tenant_match(tenant_id, request.state.tenant_id)
    settings = get_settings()
    query_response = (
        demo_pipeline_query(tenant_id)
        if settings.demo_mode
        else HydraDbClient.from_settings(settings).http.post_json(
            "/query",
            {
                "tenant_id": tenant_id,
                "query": "record_type:deal OR record_type:deal_memory OR record_type:source_fact OR record_type:integration_fact",
                "type": "all",
                "query_by": "hybrid",
                "mode": "thinking",
                "max_results": 200,
                "graph_context": True,
                "metadata_filters": {"tenant_id": tenant_id},
            },
        )
    )
    return summarize_pipeline(tenant_id, query_response)


def summarize_pipeline(tenant_id: str, query_response: JsonMap) -> PipelineSummary:
    records = tuple(record for record in records_from_query(query_response) if string_field(record, "tenant_id") == tenant_id)
    deals = records_by_type(records, "deal")
    memories = records_by_type(records, "deal_memory")
    source_facts = records_by_type(records, "source_fact")
    integration_facts = records_by_type(records, "integration_fact")
    risks = risk_rows(memories)
    return PipelineSummary(
        tenant_id=tenant_id,
        deal_count=len(deals),
        open_deal_count=sum(1 for deal in deals if open_stage(string_field(deal, "stage"))),
        total_pipeline_amount=sum(amount_for_deal(deal, integration_facts) for deal in deals),
        weighted_forecast_amount=sum(amount_for_deal(deal, integration_facts) * probability_for_deal(deal) for deal in deals),
        at_risk_deal_count=len(risks),
        source_fact_count=len(source_facts),
        integration_fact_count=len(integration_facts),
        risks=risks,
    )


def open_stage(stage: str) -> bool:
    return stage.lower() not in {"closed won", "closed lost", "won", "lost"}


def amount_for_deal(deal: JsonMap, integration_facts: tuple[JsonMap, ...]) -> float:
    amount = number_field(deal, "amount_usd")
    if amount is not None:
        return amount
    amount = number_field(deal, "amount")
    if amount is not None:
        return amount
    deal_id = string_field(deal, "deal_id") or string_field(deal, "id")
    for fact in integration_facts:
        if string_field(fact, "deal_id") == deal_id:
            return number_field(fact, "amount") or 0.0
    return 0.0


def probability_for_deal(deal: JsonMap) -> float:
    probability = number_field(deal, "forecast_probability")
    if probability is not None:
        return probability
    return number_field(deal, "probability") or 0.0


def risk_rows(memories: tuple[JsonMap, ...]) -> tuple[PipelineRisk, ...]:
    latest_by_deal: dict[str, JsonMap] = {}
    for memory in memories:
        deal_id = string_field(memory, "deal_id")
        if not deal_id:
            continue
        current = latest_by_deal.get(deal_id)
        if current is None or valid_from_time(memory) >= valid_from_time(current):
            latest_by_deal[deal_id] = memory
    risks: list[PipelineRisk] = []
    for memory in latest_by_deal.values():
        objections = strings_field(memory, "active_objections")
        if objections:
            risks.append(PipelineRisk(deal_id=string_field(memory, "deal_id"), active_objections=objections))
    return tuple(risks)


def number_field(record: JsonMap, name: str) -> float | None:
    value: JsonValue = record.get(name)
    match value:
        case int(number) | float(number):
            return float(number)
        case _:
            return None
