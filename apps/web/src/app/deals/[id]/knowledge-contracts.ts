import type { KnowledgeNode, ObjectionHandler } from "@causal-deal/types";

const KNOWLEDGE_KINDS = ["Playbook", "Battlecard", "ICPDefinition", "SourceFact", "IntegrationFact"] as const;

type KnowledgeKind = (typeof KNOWLEDGE_KINDS)[number];

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

function hasStringFields(value: Record<string, unknown>, fields: readonly string[]): boolean {
  return fields.every((field) => isString(value[field]));
}

function hasOptionalStringFields(value: Record<string, unknown>, fields: readonly string[]): boolean {
  return fields.every((field) => value[field] === undefined || isString(value[field]));
}

function isObjectionHandler(value: unknown): value is ObjectionHandler {
  return isRecord(value) && hasStringFields(value, ["objection_type", "guidance"]) && isStringArray(value["evidence_required"]);
}

function isPlaybook(value: Record<string, unknown>): boolean {
  return (
    hasStringFields(value, ["id", "tenant_id", "stage", "title", "content"]) &&
    isArrayOf(value["objection_handlers"], isObjectionHandler) &&
    isNumber(value["version"]) &&
    isBoolean(value["active"])
  );
}

function isBattlecard(value: Record<string, unknown>): boolean {
  return (
    hasStringFields(value, ["id", "tenant_id", "competitor_name"]) &&
    isStringArray(value["our_strengths"]) &&
    isStringArray(value["their_weaknesses"]) &&
    isStringArray(value["traps_to_avoid"]) &&
    isStringArray(value["win_themes"]) &&
    isNumber(value["version"]) &&
    isBoolean(value["active"])
  );
}

function isIcpDefinition(value: Record<string, unknown>): boolean {
  return (
    hasStringFields(value, ["id", "tenant_id", "segment"]) &&
    isRecord(value["firmographic_criteria"]) &&
    isStringArray(value["behavioral_signals"]) &&
    isStringArray(value["disqualifiers"]) &&
    isNumber(value["version"]) &&
    isBoolean(value["active"])
  );
}

function isSourceFact(value: Record<string, unknown>): boolean {
  return (
    hasStringFields(value, ["id", "tenant_id"]) &&
    value["record_type"] === "source_fact" &&
    hasOptionalStringFields(value, ["source", "content", "deal_id", "source_record_id", "stage"])
  );
}

function isIntegrationFact(value: Record<string, unknown>): boolean {
  return (
    hasStringFields(value, ["id", "tenant_id"]) &&
    value["record_type"] === "integration_fact" &&
    hasOptionalStringFields(value, ["source", "content", "deal_id", "source_record_id", "stage"]) &&
    (value["amount"] === undefined || isNumber(value["amount"]))
  );
}

const knowledgeRecordValidators: { readonly [K in KnowledgeKind]: (record: Record<string, unknown>) => boolean } = {
  Playbook: isPlaybook,
  Battlecard: isBattlecard,
  ICPDefinition: isIcpDefinition,
  SourceFact: isSourceFact,
  IntegrationFact: isIntegrationFact
};

function isKnowledgeKind(value: unknown): value is KnowledgeKind {
  return isString(value) && KNOWLEDGE_KINDS.some((kind) => kind === value);
}

export function isKnowledgeNode(value: unknown): value is KnowledgeNode {
  if (!isRecord(value) || !isRecord(value["record"])) return false;
  const record = value["record"];
  const kind = value["kind"];
  return (
    isString(value["id"]) &&
    isString(value["tenant_id"]) &&
    isKnowledgeKind(kind) &&
    knowledgeRecordValidators[kind](record)
  );
}
