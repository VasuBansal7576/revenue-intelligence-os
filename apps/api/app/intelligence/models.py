from pydantic import BaseModel, ConfigDict, Field


class CausalDiagnosis(BaseModel):
    model_config = ConfigDict(frozen=True)

    description: str
    causal_chain: tuple[str, ...]
    evidence_node_ids: tuple[str, ...]


class RiskFlag(BaseModel):
    model_config = ConfigDict(frozen=True)

    flag: str
    severity: str
    evidence_node_id: str


class NextBestAction(BaseModel):
    model_config = ConfigDict(frozen=True)

    action: str
    rationale: str
    cited_memory_node_id: str | None
    cited_knowledge_node_id: str | None


class DealBriefing(BaseModel):
    model_config = ConfigDict(frozen=True)

    deal_id: str
    generated_at: str
    status_summary: str
    causal_diagnosis: tuple[CausalDiagnosis, ...] = Field(default_factory=tuple)
    risk_flags: tuple[RiskFlag, ...] = Field(default_factory=tuple)
    next_best_actions: tuple[NextBestAction, ...] = Field(default_factory=tuple)
    confidence: float
