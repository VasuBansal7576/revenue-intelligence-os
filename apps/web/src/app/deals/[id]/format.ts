import type { CallEvent, CausalLink, ContactMemory, DealMemory } from "@causal-deal/types";

export type BadgeTone = "success" | "warning" | "danger" | "info" | "production";

export function formatMoney(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0
  }).format(value);
}

export function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

export function confidencePercent(value: number) {
  return `${Math.round(value * 100)}%`;
}

export function signalTone(type: string): BadgeTone {
  if (type.includes("budget") || type.includes("discount") || type.includes("stall")) return "danger";
  if (type.includes("security") || type.includes("integration") || type.includes("timing")) return "warning";
  return "info";
}

export function nodeDomId(value: string) {
  return `evidence-${value.replace(/[^a-zA-Z0-9_-]/g, "-")}`;
}

export function dealMemoryNodeId(memory: DealMemory) {
  return `${memory.deal_id}:deal_memory:${memory.valid_from}`;
}

export function contactMemoryNodeId(memory: ContactMemory) {
  return `${memory.deal_id}:contact_memory:${memory.contact_id}:${memory.valid_from}`;
}

export function callEventNodeId(call: CallEvent) {
  return call.call_id;
}

export function causalLinkNodeId(link: CausalLink) {
  return `${link.from_node_id}->${link.to_node_id}`;
}
