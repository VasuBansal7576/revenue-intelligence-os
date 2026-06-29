import type {
  CallEvent,
  CausalLink,
  ChampionBehaviorSignal,
  CommitmentRecord,
  CompetitiveMention,
  ContactMemory,
  ContactRecord,
  DealBriefing,
  DealContext,
  DealMemory,
  DealRecord,
  DealTimelineResponse,
  NextBestAction,
  ObjectionRecord,
  SentimentShift,
  Tenant
} from "@causal-deal/types";
import { isKnowledgeNode } from "./knowledge-contracts.ts";

function isString(value: unknown): value is string {
  return typeof value === "string";
}

function isNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function isBoolean(value: unknown): value is boolean {
  return typeof value === "boolean";
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isStringArray(value: unknown): value is readonly string[] {
  return Array.isArray(value) && value.every(isString);
}

function isArrayOf<T>(value: unknown, guard: (item: unknown) => item is T): value is readonly T[] {
  return Array.isArray(value) && value.every(guard);
}

function isOptionalString(value: unknown): value is string | null {
  return value === null || isString(value);
}

function isOptionalDateTime(value: unknown): value is string | null {
  return value === null || isDateTime(value);
}

function isAllowed(value: unknown, allowed: readonly string[]): value is string {
  return isString(value) && allowed.includes(value);
}

function isDateTime(value: unknown): value is string {
  return isString(value) && /^\d{4}-\d{2}-\d{2}T/.test(value) && !Number.isNaN(Date.parse(value));
}

function hasStringFields(value: Record<string, unknown>, fields: readonly string[]): boolean {
  return fields.every((field) => isString(value[field]));
}

export function isDealContext(value: unknown): value is DealContext {
  return (
    isRecord(value) &&
    isTenant(value["tenant"]) &&
    isDealRecord(value["deal"]) &&
    isArrayOf(value["contacts"], isContactRecord) &&
    isDealMemory(value["deal_memory"]) &&
    isArrayOf(value["contact_memories"], isContactMemory) &&
    isArrayOf(value["call_events"], isCallEvent) &&
    isArrayOf(value["causal_links"], isCausalLink) &&
    isArrayOf(value["knowledge_nodes"], isKnowledgeNode)
  );
}

function isTenant(value: unknown): value is Tenant {
  return (
    isRecord(value) &&
    hasStringFields(value, ["id", "name", "domain"]) &&
    isAllowed(value["environment"], ["production", "test"])
  );
}

function isDealRecord(value: unknown): value is DealRecord {
  return (
    isRecord(value) &&
    hasStringFields(value, ["id", "tenant_id", "account_name", "name", "owner_name", "stage", "close_date"]) &&
    isNumber(value["amount_usd"]) &&
    isAllowed(value["status"], ["healthy", "stalling"])
  );
}

function isContactRecord(value: unknown): value is ContactRecord {
  return isRecord(value) && hasStringFields(value, ["id", "tenant_id", "deal_id", "name", "title", "email"]);
}

function isDealMemory(value: unknown): value is DealMemory {
  return (
    isRecord(value) &&
    hasStringFields(value, ["deal_id", "tenant_id", "stage", "last_call_id", "valid_from"]) &&
    isOptionalString(value["champion_id"]) &&
    isOptionalString(value["economic_buyer_id"]) &&
    isNumber(value["champion_confidence"]) &&
    isBoolean(value["budget_confirmed"]) &&
    isBoolean(value["technical_validated"]) &&
    isStringArray(value["active_objections"]) &&
    isOptionalString(value["next_step_agreed"]) &&
    isString(value["last_call_id"]) &&
    isDateTime(value["valid_from"]) &&
    isOptionalDateTime(value["valid_to"])
  );
}

function isContactMemory(value: unknown): value is ContactMemory {
  return (
    isRecord(value) &&
    hasStringFields(value, ["contact_id", "deal_id", "tenant_id", "last_seen_on_call", "last_seen_timestamp", "valid_from"]) &&
    isAllowed(value["role"], ["champion", "economic_buyer", "technical_buyer", "blocker", "unknown"]) &&
    isAllowed(value["engagement_level"], ["high", "medium", "low", "silent"]) &&
    isAllowed(value["sentiment_trend"], ["positive", "neutral", "negative", "declining"]) &&
    isStringArray(value["key_concerns"]) &&
    isDateTime(value["last_seen_timestamp"]) &&
    isDateTime(value["valid_from"]) &&
    isOptionalDateTime(value["valid_to"])
  );
}

function isObjection(value: unknown): value is ObjectionRecord {
  return (
    isRecord(value) &&
    hasStringFields(value, ["type", "verbatim_quote", "contact_id"]) &&
    isAllowed(value["severity"], ["low", "medium", "high"])
  );
}

function isCommitment(value: unknown): value is CommitmentRecord {
  return (
    isRecord(value) &&
    hasStringFields(value, ["type", "made_by_contact_id", "verbatim"]) &&
    (value["due_date"] === undefined || isString(value["due_date"]))
  );
}

function isSentimentShift(value: unknown): value is SentimentShift {
  return (
    isRecord(value) &&
    hasStringFields(value, ["contact_id", "trigger_quote"]) &&
    isAllowed(value["from"], ["positive", "neutral", "negative"]) &&
    isAllowed(value["to"], ["positive", "neutral", "negative"]) &&
    isNumber(value["timestamp_in_call"])
  );
}

function isCompetitiveMention(value: unknown): value is CompetitiveMention {
  return (
    isRecord(value) &&
    hasStringFields(value, ["competitor_name", "context"]) &&
    isAllowed(value["sentiment"], ["positive", "neutral", "negative"])
  );
}

function isChampionBehavior(value: unknown): value is ChampionBehaviorSignal {
  return (
    isRecord(value) &&
    isOptionalString(value["contact_id"]) &&
    isAllowed(value["signal_type"], ["active_advocacy", "passive", "silence", "opposition"]) &&
    isString(value["evidence_quote"])
  );
}

function isCallEvent(value: unknown): value is CallEvent {
  return (
    isRecord(value) &&
    hasStringFields(value, ["call_id", "deal_id", "tenant_id", "summary"]) &&
    isDateTime(value["timestamp"]) &&
    isNumber(value["duration_seconds"]) &&
    isStringArray(value["participants"]) &&
    isArrayOf(value["objections_raised"], isObjection) &&
    isArrayOf(value["commitments_made"], isCommitment) &&
    isArrayOf(value["sentiment_shifts"], isSentimentShift) &&
    isArrayOf(value["competitive_mentions"], isCompetitiveMention) &&
    isChampionBehavior(value["champion_behavior"])
  );
}

function isCausalLink(value: unknown): value is CausalLink {
  return (
    isRecord(value) &&
    hasStringFields(value, ["tenant_id", "deal_id", "from_node_id", "to_node_id", "link_type", "evidence_call_id"]) &&
    isDateTime(value["created_at"]) &&
    isNumber(value["confidence"])
  );
}

function isPointInTime(value: unknown): value is DealTimelineResponse["point_in_time"] {
  return isRecord(value) && isDateTime(value["as_of"]) && isDealMemory(value["deal_memory"]) && isStringArray(value["call_event_ids"]);
}

export function isTimeline(value: unknown): value is DealTimelineResponse {
  return (
    isRecord(value) &&
    isString(value["deal_id"]) &&
    isString(value["tenant_id"]) &&
    Array.isArray(value["snapshots"]) &&
    value["snapshots"].every(isDealMemory) &&
    (value["point_in_time"] === null || isPointInTime(value["point_in_time"]))
  );
}

function isDiagnosis(value: unknown): value is DealBriefing["causal_diagnosis"][number] {
  return (
    isRecord(value) &&
    isString(value["description"]) &&
    isStringArray(value["causal_chain"]) &&
    isStringArray(value["evidence_node_ids"])
  );
}

function isRiskFlag(value: unknown): value is DealBriefing["risk_flags"][number] {
  return isRecord(value) && isString(value["flag"]) && isString(value["severity"]) && isString(value["evidence_node_id"]);
}

function isNextBestAction(value: unknown): value is NextBestAction {
  return (
    isRecord(value) &&
    isString(value["action"]) &&
    isString(value["rationale"]) &&
    (value["cited_memory_node_id"] === null || isString(value["cited_memory_node_id"])) &&
    (value["cited_knowledge_node_id"] === null || isString(value["cited_knowledge_node_id"]))
  );
}

export function isDealBriefing(value: unknown): value is DealBriefing {
  return (
    isRecord(value) &&
    isString(value["deal_id"]) &&
    isDateTime(value["generated_at"]) &&
    isString(value["status_summary"]) &&
    Array.isArray(value["causal_diagnosis"]) &&
    value["causal_diagnosis"].every(isDiagnosis) &&
    Array.isArray(value["risk_flags"]) &&
    value["risk_flags"].every(isRiskFlag) &&
    Array.isArray(value["next_best_actions"]) &&
    value["next_best_actions"].every(isNextBestAction) &&
    isNumber(value["confidence"])
  );
}
