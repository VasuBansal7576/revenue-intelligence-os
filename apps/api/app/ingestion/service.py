from typing import Protocol, assert_never

from app.external import HydraDbClient, JsonMap, UpstreamServiceError
from app.ingestion.causal_linker import build_causal_links
from app.ingestion.models import (
    CausalLinkRecord,
    ChampionSignal,
    ExtractedCallSignals,
    IngestCallRequest,
    IngestCallResponse,
    ObjectionSignal,
    PriorDealState,
)
from app.records import (
    bool_field,
    deal_records,
    float_field,
    latest_record,
    optional_string_field,
    records_from_query,
    string_field,
    strings_field,
    valid_from_time,
)


class SignalExtractor(Protocol):
    def extract_signals(self, transcript: str, tenant_id: str, deal_id: str, call_id: str) -> ExtractedCallSignals: ...


class CallWriter(Protocol):
    def read_prior_state(self, tenant_id: str, deal_id: str) -> PriorDealState: ...

    def write_call(
        self,
        request: IngestCallRequest,
        signals: ExtractedCallSignals,
        links: tuple[CausalLinkRecord, ...],
    ) -> str: ...


class HydraDbCallWriter:
    def __init__(self, client: HydraDbClient) -> None:
        self.client = client

    def read_prior_state(self, tenant_id: str, deal_id: str) -> PriorDealState:
        records = records_from_query(self.client.query_deal(tenant_id, deal_id))
        return prior_state_from_records(records, tenant_id, deal_id)

    def write_call(
        self,
        request: IngestCallRequest,
        signals: ExtractedCallSignals,
        links: tuple[CausalLinkRecord, ...],
    ) -> str:
        prior_records = records_from_query(self.client.query_deal(request.tenant_id, request.deal_id))
        prior_deal = current_deal_memory(prior_records, request.tenant_id, request.deal_id)
        records: tuple[JsonMap, ...] = (
            call_event_record(request, signals),
            evolve_deal_memory(request, signals, prior_deal),
            *evolve_contact_memories(request, signals, prior_deal),
            *(
                {
                    "record_type": "causal_link",
                    "id": f"{link.from_node_id}->{link.to_node_id}",
                    "tenant_id": link.tenant_id,
                    "deal_id": link.deal_id,
                    "from_node_id": link.from_node_id,
                    "to_node_id": link.to_node_id,
                    "link_type": link.link_type,
                    "confidence": link.confidence,
                    "evidence_call_id": link.evidence_call_id,
                    "created_at": link.created_at,
                }
                for link in links
            ),
        )
        self.client.ingest_memory(request.tenant_id, request.deal_id, records)
        return request.call_id


def current_deal_memory(records: tuple[JsonMap, ...], tenant_id: str, deal_id: str) -> JsonMap | None:
    try:
        return latest_record(records, "deal_memory", deal_id, tenant_id)
    except UpstreamServiceError:
        return None


def call_event_record(request: IngestCallRequest, signals: ExtractedCallSignals) -> JsonMap:
    return {
        "record_type": "call_event",
        "id": request.call_id,
        "call_id": request.call_id,
        "tenant_id": request.tenant_id,
        "deal_id": request.deal_id,
        "timestamp": request.timestamp,
        "duration_seconds": request.duration_seconds,
        "participants": sorted(
            {
                signal.contact_id
                for signal in (*signals.objections, *signals.champion_signals)
                if signal.contact_id is not None
            }
        ),
        "objections_raised": [signal.model_dump() for signal in signals.objections],
        "commitments_made": [signal.model_dump() for signal in signals.commitments],
        "sentiment_shifts": [signal.model_dump() for signal in signals.sentiment_shifts],
        "competitive_mentions": [signal.model_dump() for signal in signals.competitive_mentions],
        "champion_behavior": signals.champion_signals[0].model_dump()
        if signals.champion_signals
        else {"contact_id": None, "signal_type": "passive", "evidence_quote": ""},
        "summary": request.transcript[:240],
        "transcript": request.transcript,
    }


def evolve_deal_memory(
    request: IngestCallRequest,
    signals: ExtractedCallSignals,
    prior: JsonMap | None,
) -> JsonMap:
    prior_objections = strings_field(prior or {}, "active_objections")
    active_objections = list(dict.fromkeys((*prior_objections, *(signal.type for signal in signals.objections))))
    return {
        "record_type": "deal_memory",
        "id": f"{request.deal_id}:deal_memory:{request.timestamp}",
        "tenant_id": request.tenant_id,
        "deal_id": request.deal_id,
        "stage": string_field(prior or {}, "stage"),
        "champion_id": champion_id(signals, prior),
        "economic_buyer_id": economic_buyer_id(signals, prior),
        "champion_confidence": champion_confidence(signals, prior),
        "budget_confirmed": bool_field(prior or {}, "budget_confirmed") and "budget_freeze" not in active_objections,
        "technical_validated": bool_field(prior or {}, "technical_validated"),
        "active_objections": active_objections,
        "next_step_agreed": next_step_agreed(signals, prior),
        "last_call_id": request.call_id,
        "valid_from": request.timestamp,
        "valid_to": None,
    }


def champion_id(signals: ExtractedCallSignals, prior: JsonMap | None) -> str | None:
    for signal in signals.champion_signals:
        if signal.contact_id is not None:
            return signal.contact_id
    return optional_string_field(prior or {}, "champion_id")


def economic_buyer_id(signals: ExtractedCallSignals, prior: JsonMap | None) -> str | None:
    if signals.economic_buyer_presence.contact_id is not None:
        return signals.economic_buyer_presence.contact_id
    return optional_string_field(prior or {}, "economic_buyer_id")


def champion_confidence(signals: ExtractedCallSignals, prior: JsonMap | None) -> float:
    confidence = float_field(prior or {}, "champion_confidence")
    if not signals.champion_signals:
        return confidence
    match signals.champion_signals[0].signal_type:
        case "active_advocacy":
            return max(confidence, 0.8)
        case "silence":
            return max(0.0, confidence - 0.3)
        case "opposition":
            return min(confidence, 0.2)
        case "passive":
            return confidence
        case unknown:
            assert_never(unknown)


def next_step_agreed(signals: ExtractedCallSignals, prior: JsonMap | None) -> str | None:
    if signals.next_steps_agreed:
        return signals.next_steps_agreed[0]
    return optional_string_field(prior or {}, "next_step_agreed")


def evolve_contact_memories(
    request: IngestCallRequest,
    signals: ExtractedCallSignals,
    prior_deal: JsonMap | None,
) -> tuple[JsonMap, ...]:
    records = [champion_contact_memory(request, signal, signals) for signal in signals.champion_signals if signal.contact_id]
    buyer_id = economic_buyer_id(signals, prior_deal)
    if buyer_id is not None:
        records.append(buyer_contact_memory(request, signals, buyer_id))
    known = {string_field(record, "contact_id") for record in records}
    records.extend(objection_contact_memory(request, signal) for signal in signals.objections if signal.contact_id not in known)
    return tuple(records)


def champion_contact_memory(request: IngestCallRequest, signal: ChampionSignal, signals: ExtractedCallSignals) -> JsonMap:
    match signal.signal_type:
        case "active_advocacy":
            engagement, sentiment = "high", "positive"
        case "silence":
            engagement, sentiment = "silent", "declining"
        case "opposition":
            engagement, sentiment = "low", "negative"
        case "passive":
            engagement, sentiment = "medium", "neutral"
        case unknown:
            assert_never(unknown)
    return contact_memory_record(request, signal.contact_id, "champion", engagement, sentiment, concerns_for(signal.contact_id, signals))


def buyer_contact_memory(request: IngestCallRequest, signals: ExtractedCallSignals, contact_id: str) -> JsonMap:
    if signals.economic_buyer_presence.present:
        return contact_memory_record(request, contact_id, "economic_buyer", "high", "neutral", ())
    return contact_memory_record(request, contact_id, "economic_buyer", "silent", "declining", ())


def objection_contact_memory(request: IngestCallRequest, signal: ObjectionSignal) -> JsonMap:
    return contact_memory_record(request, signal.contact_id, "unknown", "low", "negative", (signal.type,))


def concerns_for(contact_id: str, signals: ExtractedCallSignals) -> tuple[str, ...]:
    return tuple(signal.type for signal in signals.objections if signal.contact_id == contact_id)


def contact_memory_record(
    request: IngestCallRequest,
    contact_id: str,
    role: str,
    engagement: str,
    sentiment: str,
    concerns: tuple[str, ...],
) -> JsonMap:
    return {
        "record_type": "contact_memory",
        "id": f"{request.deal_id}:contact_memory:{contact_id}:{request.timestamp}",
        "tenant_id": request.tenant_id,
        "deal_id": request.deal_id,
        "contact_id": contact_id,
        "role": role,
        "engagement_level": engagement,
        "last_seen_on_call": request.call_id,
        "last_seen_timestamp": request.timestamp,
        "sentiment_trend": sentiment,
        "key_concerns": list(concerns),
        "valid_from": request.timestamp,
        "valid_to": None,
    }


def prior_state_from_records(records: tuple[JsonMap, ...], tenant_id: str, deal_id: str) -> PriorDealState:
    contact_memories = deal_records(records, "contact_memory", deal_id, tenant_id)
    return PriorDealState(
        tenant_id=tenant_id,
        deal_id=deal_id,
        champion_was_silent=latest_contact_memory_is(contact_memories, "champion", "silent"),
        economic_buyer_was_absent=latest_contact_memory_is(contact_memories, "economic_buyer", "silent"),
    )


def latest_contact_memory_is(records: tuple[JsonMap, ...], role: str, engagement: str) -> bool:
    matching = tuple(record for record in records if string_field(record, "role") == role)
    if not matching:
        return False
    return string_field(max(matching, key=valid_from_time), "engagement_level") == engagement


def ingest_call(
    request: IngestCallRequest,
    extractor: SignalExtractor,
    writer: CallWriter,
) -> IngestCallResponse:
    prior_state = writer.read_prior_state(request.tenant_id, request.deal_id)
    signals = extractor.extract_signals(
        request.transcript,
        request.tenant_id,
        request.deal_id,
        request.call_id,
    )
    links = build_causal_links(signals, prior_state)
    written_call_event_id = writer.write_call(request, signals, links)

    return IngestCallResponse(
        job_id=f"call.ingest:{request.call_id}",
        status="completed",
        written_call_event_id=written_call_event_id,
        causal_links=links,
    )
