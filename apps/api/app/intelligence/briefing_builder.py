from app.external import JsonMap, JsonValue
from app.intelligence.models import DealBriefing, NextBestAction
from app.records import string_field


def enforce_cited_actions(
    actions: tuple[NextBestAction, ...],
    valid_memory_node_ids: tuple[str, ...],
    valid_knowledge_node_ids: tuple[str, ...],
) -> tuple[NextBestAction, ...]:
    memory_ids = frozenset(valid_memory_node_ids)
    knowledge_ids = frozenset(valid_knowledge_node_ids)
    return tuple(
        action
        for action in actions
        if (
            action.cited_memory_node_id is not None
            or action.cited_knowledge_node_id is not None
        )
        and (
            action.cited_memory_node_id is None or action.cited_memory_node_id in memory_ids
        )
        and (
            action.cited_knowledge_node_id is None
            or action.cited_knowledge_node_id in knowledge_ids
        )
    )


def memory_node_ids(context: JsonMap) -> tuple[str, ...]:
    return record_ids(
        (
            context.get("deal_memory"),
            context.get("contact_memories"),
            context.get("call_events"),
            context.get("causal_links"),
        )
    )


def knowledge_node_ids(context: JsonMap) -> tuple[str, ...]:
    return record_ids((context.get("knowledge_nodes"),))


def enforce_cited_briefing(
    briefing: DealBriefing,
    valid_memory_node_ids: tuple[str, ...],
    valid_knowledge_node_ids: tuple[str, ...],
) -> DealBriefing:
    valid_evidence_ids = frozenset(valid_memory_node_ids) | frozenset(valid_knowledge_node_ids)
    return briefing.model_copy(
        update={
            "causal_diagnosis": tuple(
                diagnosis
                for diagnosis in briefing.causal_diagnosis
                if diagnosis.evidence_node_ids
                and all(node_id in valid_evidence_ids for node_id in diagnosis.evidence_node_ids)
            ),
            "risk_flags": tuple(risk for risk in briefing.risk_flags if risk.evidence_node_id in valid_evidence_ids),
            "next_best_actions": enforce_cited_actions(
                briefing.next_best_actions,
                valid_memory_node_ids,
                valid_knowledge_node_ids,
            ),
        }
    )


def record_ids(values: tuple[JsonValue, ...]) -> tuple[str, ...]:
    ids: list[str] = []
    for value in values:
        for record in records(value):
            record_id = string_field(record, "id")
            if record_id:
                ids.append(record_id)
    return tuple(ids)


def records(value: JsonValue) -> tuple[JsonMap, ...]:
    match value:
        case dict() as record:
            return (record,)
        case list() as items:
            found: list[JsonMap] = []
            for item in items:
                match item:
                    case dict() as record:
                        found.append(record)
                    case _:
                        continue
            return tuple(found)
        case _:
            return ()
