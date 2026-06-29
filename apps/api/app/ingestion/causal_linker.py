from app.ingestion.models import CausalLinkRecord, ExtractedCallSignals, PriorDealState

CREATED_AT = "2026-03-11T16:00:00.000Z"


def build_causal_links(signals: ExtractedCallSignals, prior: PriorDealState) -> tuple[CausalLinkRecord, ...]:
    links: list[CausalLinkRecord] = []
    objection_types = {objection.type for objection in signals.objections}

    if prior.champion_was_silent and "budget_freeze" in objection_types:
        links.append(
            CausalLinkRecord(
                tenant_id=signals.tenant_id,
                deal_id=signals.deal_id,
                from_node_id="prior:champion_silence",
                to_node_id=f"{signals.call_id}:budget_freeze",
                link_type="champion_silence_triggered_budget_objection",
                confidence=0.81,
                evidence_call_id=signals.call_id,
                created_at=CREATED_AT,
            )
        )

    if prior.economic_buyer_was_absent and "budget_freeze" in objection_types:
        links.append(
            CausalLinkRecord(
                tenant_id=signals.tenant_id,
                deal_id=signals.deal_id,
                from_node_id="prior:economic_buyer_absence",
                to_node_id=f"{signals.call_id}:budget_freeze",
                link_type="economic_buyer_absence_triggered_stall",
                confidence=0.7,
                evidence_call_id=signals.call_id,
                created_at=CREATED_AT,
            )
        )

    if "competitor_discount" in objection_types and signals.competitive_mentions:
        links.append(
            CausalLinkRecord(
                tenant_id=signals.tenant_id,
                deal_id=signals.deal_id,
                from_node_id=f"{signals.call_id}:competitive_mentions",
                to_node_id=f"{signals.call_id}:competitor_discount",
                link_type="competitor_mention_triggered_pricing_concern",
                confidence=0.74,
                evidence_call_id=signals.call_id,
                created_at=CREATED_AT,
            )
        )

    return tuple(link for link in links if link.confidence >= 0.6)
