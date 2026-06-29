from datetime import UTC, datetime

from app.external import JsonMap
from app.records import deal_memory_snapshot, records_by_type, records_from_query, string_field, utc_time as parse_utc_time
from app.temporal.models import (
    DealMemorySnapshot,
    DealTimelineResponse,
    PointInTimeDealState,
)


def is_current_at(snapshot: DealMemorySnapshot, as_of: datetime) -> bool:
    return snapshot.valid_from <= as_of and (
        snapshot.valid_to is None or as_of < snapshot.valid_to
    )


def visible_call_ids(records: tuple[JsonMap, ...], deal_id: str, tenant_id: str, as_of: datetime) -> tuple[str, ...]:
    return tuple(
        string_field(call, "id")
        for call in records_by_type(records, "call_event")
        if string_field(call, "deal_id") == deal_id
        and string_field(call, "tenant_id") == tenant_id
        and parse_utc_time(string_field(call, "timestamp")) <= as_of
    )


def snapshots_for(records: tuple[JsonMap, ...], deal_id: str, tenant_id: str) -> tuple[DealMemorySnapshot, ...]:
    return tuple(
        sorted(
            (
                deal_memory_snapshot(record)
                for record in records_by_type(records, "deal_memory")
                if string_field(record, "deal_id") == deal_id and string_field(record, "tenant_id") == tenant_id
            ),
            key=lambda snapshot: snapshot.valid_from,
        )
    )


def build_timeline_response(
    query_response: JsonMap,
    deal_id: str,
    tenant_id: str,
    as_of: datetime | None,
) -> DealTimelineResponse:
    records = records_from_query(query_response)
    snapshots = snapshots_for(records, deal_id, tenant_id)
    point_in_time: PointInTimeDealState | None = None

    if as_of is not None:
        replay_at = normalize_utc(as_of)
        deal_memory = next(
            (snapshot for snapshot in reversed(snapshots) if is_current_at(snapshot, replay_at)),
            None,
        )
        if deal_memory is not None:
            point_in_time = PointInTimeDealState(
                as_of=replay_at,
                deal_memory=deal_memory,
                call_event_ids=visible_call_ids(records, deal_id, tenant_id, replay_at),
            )

    return DealTimelineResponse(
        deal_id=deal_id,
        tenant_id=tenant_id,
        snapshots=snapshots,
        point_in_time=point_in_time,
    )


def normalize_utc(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        return moment.replace(tzinfo=UTC)
    return moment.astimezone(UTC)
