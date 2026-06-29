import json

from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field

from app.auth import require_tenant_match
from app.config import Settings, get_settings, llm_missing_config
from app.demo import demo_pipeline_query
from app.external import JsonMap
from app.records import float_field, records_by_type, records_from_query, string_field

router = APIRouter(tags=["revenue"])


class AssistantQuery(BaseModel):
    model_config = ConfigDict(frozen=True)

    question: str = Field(min_length=1)


def tenant_records(request: Request, tenant_id: str, requires_llm: bool = False) -> tuple[JsonMap, ...]:
    require_tenant_match(tenant_id, request.state.tenant_id)
    settings = get_settings()
    if not settings.demo_mode:
        raise_provider_not_ready(settings, requires_llm)
    return tuple(record for record in records_from_query(demo_pipeline_query(tenant_id)) if string_field(record, "tenant_id") == tenant_id)


def raise_provider_not_ready(settings: Settings, requires_llm: bool = False) -> None:
    missing = []
    if not settings.hydradb_api_key:
        missing.append("HYDRA_DB_API_KEY")
    if requires_llm:
        missing.extend(llm_missing_config(settings))
    detail = f"provider-not-ready: {', '.join(missing)}" if missing else "provider-not-ready: seeded provider records unavailable"
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)


def list_response(tenant_id: str, records: tuple[JsonMap, ...], record_type: str) -> JsonMap:
    return {"tenant_id": tenant_id, "items": list(records_by_type(records, record_type))}


def record_by_id(records: tuple[JsonMap, ...], record_type: str, record_id: str) -> JsonMap:
    for record in records_by_type(records, record_type):
        if string_field(record, "id") == record_id or string_field(record, "call_id") == record_id:
            return record
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")


def weighted_forecast(records: tuple[JsonMap, ...]) -> float:
    return sum(float_field(deal, "amount_usd") * float_field(deal, "forecast_probability") for deal in records_by_type(records, "deal"))


@router.get("/accounts")
def accounts(request: Request, tenant_id: str = Query(...)) -> JsonMap:
    return list_response(tenant_id, tenant_records(request, tenant_id), "account")


@router.get("/accounts/{account_id}")
def account(account_id: str, request: Request, tenant_id: str = Query(...)) -> JsonMap:
    return record_by_id(tenant_records(request, tenant_id), "account", account_id)


@router.get("/deals")
def deals(request: Request, tenant_id: str = Query(...)) -> JsonMap:
    return list_response(tenant_id, tenant_records(request, tenant_id), "deal")


@router.get("/calls")
def calls(request: Request, tenant_id: str = Query(...)) -> JsonMap:
    return list_response(tenant_id, tenant_records(request, tenant_id), "call_event")


@router.get("/calls/{call_id}")
def call(call_id: str, request: Request, tenant_id: str = Query(...)) -> JsonMap:
    return record_by_id(tenant_records(request, tenant_id), "call_event", call_id)


@router.get("/search")
def search(request: Request, tenant_id: str = Query(...), q: str = Query(default="")) -> JsonMap:
    records = tenant_records(request, tenant_id)
    needle = q.lower()
    items = [record for record in records if string_field(record, "id") and (not needle or needle in json.dumps(record, sort_keys=True).lower())]
    return {"tenant_id": tenant_id, "query": q, "items": items}


@router.get("/forecast/summary")
def forecast_summary(request: Request, tenant_id: str = Query(...)) -> JsonMap:
    records = tenant_records(request, tenant_id)
    forecast = record_by_id(records, "forecast_submission", "forecast_2026_03_maya")
    return forecast | {"weighted_forecast_amount": weighted_forecast(records)}


@router.get("/forecast/submissions")
def forecast_submissions(request: Request, tenant_id: str = Query(...)) -> JsonMap:
    return list_response(tenant_id, tenant_records(request, tenant_id), "forecast_submission")


@router.get("/coaching/scorecards")
def coaching_scorecards(request: Request, tenant_id: str = Query(...)) -> JsonMap:
    return list_response(tenant_id, tenant_records(request, tenant_id), "coaching_scorecard")


@router.get("/coaching/reps/{rep_id}")
def coaching_rep(rep_id: str, request: Request, tenant_id: str = Query(...)) -> JsonMap:
    records = tenant_records(request, tenant_id)
    rep = record_by_id(records, "user", rep_id)
    scorecards = tuple(record for record in records_by_type(records, "coaching_scorecard") if string_field(record, "rep_id") == rep_id)
    return {"tenant_id": tenant_id, "rep": rep, "risk_rows": list(scorecards)}


@router.get("/engage/tasks")
def engage_tasks(request: Request, tenant_id: str = Query(...)) -> JsonMap:
    return list_response(tenant_id, tenant_records(request, tenant_id), "engagement_task")


@router.get("/engage/tasks/{task_id}")
def engage_task(task_id: str, request: Request, tenant_id: str = Query(...)) -> JsonMap:
    return record_by_id(tenant_records(request, tenant_id), "engagement_task", task_id)


@router.post("/assistant/query")
def assistant_query(payload: AssistantQuery, request: Request, tenant_id: str = Query(...)) -> JsonMap:
    records = tenant_records(request, tenant_id, requires_llm=True)
    answer = record_by_id(records, "assistant_answer", "assistant_answer_northstar_risk")
    return {
        "tenant_id": tenant_id,
        "question": payload.question,
        "answer": string_field(answer, "answer"),
        "citations": answer.get("citation_ids", []),
        "runtime": "local-demo",
    }


@router.get("/admin/users")
def admin_users(request: Request, tenant_id: str = Query(...)) -> JsonMap:
    return list_response(tenant_id, tenant_records(request, tenant_id), "user")


@router.get("/admin/settings")
def admin_settings(request: Request, tenant_id: str = Query(...)) -> JsonMap:
    return list_response(tenant_id, tenant_records(request, tenant_id), "admin_setting")


@router.get("/audit/events")
def audit_events(request: Request, tenant_id: str = Query(...)) -> JsonMap:
    return list_response(tenant_id, tenant_records(request, tenant_id), "audit_event")


@router.get("/exports")
def exports(request: Request, tenant_id: str = Query(...)) -> JsonMap:
    return list_response(tenant_id, tenant_records(request, tenant_id), "export_job")


@router.get("/exports/{export_id}")
def export(export_id: str, request: Request, tenant_id: str = Query(...)) -> JsonMap:
    return record_by_id(tenant_records(request, tenant_id), "export_job", export_id)
