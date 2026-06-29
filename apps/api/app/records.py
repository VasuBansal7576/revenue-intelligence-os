from datetime import UTC, datetime
import json

from app.external import JsonMap, JsonValue, UpstreamServiceError
from app.temporal.models import DealMemorySnapshot

MIN_UTC = datetime.min.replace(tzinfo=UTC)


def records_from_query(value: JsonValue) -> tuple[JsonMap, ...]:
    found: list[JsonMap] = []
    collect_records(value, found)
    return tuple(found)


def collect_records(value: JsonValue, found: list[JsonMap]) -> None:
    match value:
        case {"record_type": str()}:
            found.append(value)
        case {"text": str(text)}:
            decoded = decode_record_text(text)
            if decoded is not None:
                found.append(decoded)
        case list() as items:
            for item in items:
                collect_records(item, found)
        case dict() as items:
            for item in items.values():
                collect_records(item, found)
        case _:
            return


def decode_record_text(text: str) -> JsonMap | None:
    try:
        decoded = json.loads(text)
    except json.JSONDecodeError:
        return None
    match decoded:
        case {"record_type": str()}:
            return decoded
        case _:
            return None


def string_field(record: JsonMap, name: str) -> str:
    value = record.get(name)
    match value:
        case str(text):
            return text
        case _:
            return ""


def optional_string_field(record: JsonMap, name: str) -> str | None:
    value = record.get(name)
    match value:
        case str(text):
            return text
        case None:
            return None
        case _:
            return None


def bool_field(record: JsonMap, name: str) -> bool:
    value = record.get(name)
    match value:
        case bool(flag):
            return flag
        case _:
            return False


def float_field(record: JsonMap, name: str) -> float:
    value = record.get(name)
    match value:
        case int(number) | float(number):
            return float(number)
        case _:
            return 0.0


def strings_field(record: JsonMap, name: str) -> tuple[str, ...]:
    value = record.get(name)
    match value:
        case list() as items:
            return tuple(item for item in items if isinstance(item, str))
        case _:
            return ()


def utc_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def valid_from_time(record: JsonMap) -> datetime:
    value = string_field(record, "valid_from")
    if value:
        return utc_time(value)
    return MIN_UTC


def deal_memory_snapshot(record: JsonMap) -> DealMemorySnapshot:
    return DealMemorySnapshot(
        deal_id=string_field(record, "deal_id"),
        tenant_id=string_field(record, "tenant_id"),
        stage=string_field(record, "stage"),
        champion_id=optional_string_field(record, "champion_id"),
        economic_buyer_id=optional_string_field(record, "economic_buyer_id"),
        champion_confidence=float_field(record, "champion_confidence"),
        budget_confirmed=bool_field(record, "budget_confirmed"),
        technical_validated=bool_field(record, "technical_validated"),
        active_objections=strings_field(record, "active_objections"),
        next_step_agreed=optional_string_field(record, "next_step_agreed"),
        last_call_id=string_field(record, "last_call_id"),
        valid_from=utc_time(string_field(record, "valid_from")),
        valid_to=utc_time(string_field(record, "valid_to")) if string_field(record, "valid_to") else None,
    )


def records_by_type(records: tuple[JsonMap, ...], record_type: str) -> tuple[JsonMap, ...]:
    return tuple(record for record in records if string_field(record, "record_type") == record_type)


def first_record(records: tuple[JsonMap, ...], record_type: str, deal_id: str, tenant_id: str) -> JsonMap:
    for record in records_by_type(records, record_type):
        if string_field(record, "deal_id") == deal_id and string_field(record, "tenant_id") == tenant_id:
            return record
    raise UpstreamServiceError(service="HydraDB", detail=f"missing {record_type} for {deal_id}")


def latest_record(records: tuple[JsonMap, ...], record_type: str, deal_id: str, tenant_id: str) -> JsonMap:
    candidates = deal_records(records, record_type, deal_id, tenant_id)
    if candidates:
        return max(candidates, key=valid_from_time)
    raise UpstreamServiceError(service="HydraDB", detail=f"missing {record_type} for {deal_id}")


def tenant_record(records: tuple[JsonMap, ...], tenant_id: str) -> JsonMap:
    for record in records_by_type(records, "tenant"):
        if string_field(record, "id") == tenant_id:
            return record
    raise UpstreamServiceError(service="HydraDB", detail=f"missing tenant {tenant_id}")


def deal_records(records: tuple[JsonMap, ...], record_type: str, deal_id: str, tenant_id: str) -> tuple[JsonMap, ...]:
    return tuple(
        record
        for record in records_by_type(records, record_type)
        if string_field(record, "deal_id") == deal_id and string_field(record, "tenant_id") == tenant_id
    )


def knowledge_node(record: JsonMap) -> JsonMap:
    record_type = string_field(record, "record_type")
    match record_type:
        case "playbook":
            kind = "Playbook"
        case "battlecard":
            kind = "Battlecard"
        case "icp_definition":
            kind = "ICPDefinition"
        case "source_fact":
            kind = "SourceFact"
        case "integration_fact":
            kind = "IntegrationFact"
        case "knowledge_node":
            return record
        case _:
            raise UpstreamServiceError(service="HydraDB", detail=f"unknown knowledge record type {record_type}")
    return {
        "id": string_field(record, "id"),
        "tenant_id": string_field(record, "tenant_id"),
        "kind": kind,
        "record": record,
    }


def build_deal_context(query_response: JsonMap, deal_id: str, tenant_id: str) -> JsonMap:
    records = records_from_query(query_response)
    return {
        "tenant": tenant_record(records, tenant_id),
        "deal": first_record(records, "deal", deal_id, tenant_id),
        "contacts": list(deal_records(records, "contact", deal_id, tenant_id)),
        "deal_memory": latest_record(records, "deal_memory", deal_id, tenant_id),
        "contact_memories": list(deal_records(records, "contact_memory", deal_id, tenant_id)),
        "call_events": list(deal_records(records, "call_event", deal_id, tenant_id)),
        "causal_links": list(deal_records(records, "causal_link", deal_id, tenant_id)),
        "knowledge_nodes": [
            knowledge_node(record)
            for record in records
            if string_field(record, "record_type") in ("knowledge_node", "playbook", "battlecard", "icp_definition", "source_fact", "integration_fact")
            and string_field(record, "tenant_id") == tenant_id
        ],
    }
