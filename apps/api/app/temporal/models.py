from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DealMemorySnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    deal_id: str
    tenant_id: str
    stage: str
    champion_id: str | None
    economic_buyer_id: str | None
    champion_confidence: float
    budget_confirmed: bool
    technical_validated: bool
    active_objections: tuple[str, ...] = Field(default_factory=tuple)
    next_step_agreed: str | None
    last_call_id: str
    valid_from: datetime
    valid_to: datetime | None


class PointInTimeDealState(BaseModel):
    model_config = ConfigDict(frozen=True)

    as_of: datetime
    deal_memory: DealMemorySnapshot
    call_event_ids: tuple[str, ...] = Field(default_factory=tuple)


class DealTimelineResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    deal_id: str
    tenant_id: str
    snapshots: tuple[DealMemorySnapshot, ...] = Field(default_factory=tuple)
    point_in_time: PointInTimeDealState | None = None
