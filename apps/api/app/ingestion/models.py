from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ChampionSignalType = Literal["active_advocacy", "silence", "opposition", "passive"]


class ObjectionSignal(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: str
    verbatim_quote: str
    contact_id: str
    severity: str


class ChampionSignal(BaseModel):
    model_config = ConfigDict(frozen=True)

    contact_id: str | None
    signal_type: ChampionSignalType
    evidence_quote: str


class CompetitiveMentionSignal(BaseModel):
    model_config = ConfigDict(frozen=True)

    competitor_name: str
    context: str
    sentiment: str


class CommitmentSignal(BaseModel):
    model_config = ConfigDict(frozen=True)

    contact_id: str | None
    text: str
    due_at: str | None = None


class SentimentShiftSignal(BaseModel):
    model_config = ConfigDict(frozen=True)

    contact_id: str | None
    from_sentiment: str
    to_sentiment: str
    evidence_quote: str


class EconomicBuyerPresence(BaseModel):
    model_config = ConfigDict(frozen=True)

    present: bool
    contact_id: str | None = None
    evidence_quote: str | None = None


class ExtractedCallSignals(BaseModel):
    model_config = ConfigDict(frozen=True)

    tenant_id: str
    deal_id: str
    call_id: str
    objections: tuple[ObjectionSignal, ...] = Field(default_factory=tuple)
    champion_signals: tuple[ChampionSignal, ...] = Field(default_factory=tuple)
    competitive_mentions: tuple[CompetitiveMentionSignal, ...] = Field(default_factory=tuple)
    commitments: tuple[CommitmentSignal, ...] = Field(default_factory=tuple)
    sentiment_shifts: tuple[SentimentShiftSignal, ...] = Field(default_factory=tuple)
    economic_buyer_presence: EconomicBuyerPresence = Field(
        default_factory=lambda: EconomicBuyerPresence(present=False)
    )
    next_steps_agreed: tuple[str, ...] = Field(default_factory=tuple)


class PriorDealState(BaseModel):
    model_config = ConfigDict(frozen=True)

    tenant_id: str
    deal_id: str
    champion_was_silent: bool
    economic_buyer_was_absent: bool


class CausalLinkRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    tenant_id: str
    deal_id: str
    from_node_id: str
    to_node_id: str
    link_type: str
    confidence: float
    evidence_call_id: str
    created_at: str


class IngestCallRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    tenant_id: str
    deal_id: str
    call_id: str
    timestamp: str
    duration_seconds: int
    transcript: str


class IngestAudioForm(BaseModel):
    model_config = ConfigDict(frozen=True)

    tenant_id: str
    deal_id: str
    call_id: str
    timestamp: str
    duration_seconds: int

    def to_request(self, transcript: str) -> IngestCallRequest:
        return IngestCallRequest(
            tenant_id=self.tenant_id,
            deal_id=self.deal_id,
            call_id=self.call_id,
            timestamp=self.timestamp,
            duration_seconds=self.duration_seconds,
            transcript=transcript,
        )


class IngestCallResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    job_id: str
    status: str
    written_call_event_id: str
    causal_links: tuple[CausalLinkRecord, ...]


class IngestionJobRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    job_id: str
    tenant_id: str
    deal_id: str
    call_id: str
    source: str
    status: str
    created_at: str
    updated_at: str
    written_call_event_id: str | None = None
    causal_links: tuple[CausalLinkRecord, ...] = Field(default_factory=tuple)
    error_detail: str | None = None
