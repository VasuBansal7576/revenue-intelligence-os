import {
  battlecards,
  callEvents,
  causalLinks,
  contactMemories,
  contacts,
  dealMemories,
  deals,
  playbooks,
  tenants
} from "@causal-deal/fixtures";
import type {
  Battlecard,
  CallEvent,
  CausalLink,
  ContactMemory,
  ContactRecord,
  DealMemory,
  DealRecord,
  ICPDefinition,
  KnowledgeNode,
  KnowledgeRecord,
  MemoryNode,
  Playbook,
  Tenant
} from "@causal-deal/types";

export type FixtureSeed = {
  readonly tenants?: readonly Tenant[];
  readonly deals?: readonly DealRecord[];
  readonly contacts?: readonly ContactRecord[];
  readonly dealMemories?: readonly DealMemory[];
  readonly contactMemories?: readonly ContactMemory[];
  readonly callEvents?: readonly CallEvent[];
  readonly causalLinks?: readonly CausalLink[];
  readonly playbooks?: readonly Playbook[];
  readonly battlecards?: readonly Battlecard[];
  readonly icpDefinitions?: readonly ICPDefinition[];
};

export type FixtureStoreState = {
  tenants: Tenant[];
  deals: DealRecord[];
  contacts: ContactRecord[];
  dealMemories: DealMemory[];
  contactMemories: ContactMemory[];
  callEvents: CallEvent[];
  causalLinks: CausalLink[];
  playbooks: Playbook[];
  battlecards: Battlecard[];
  icpDefinitions: ICPDefinition[];
};

export class FixtureStoreLookupError extends Error {
  readonly name = "FixtureStoreLookupError";

  constructor(message: string) {
    super(message);
  }
}

export class TenantBoundaryError extends Error {
  readonly name = "TenantBoundaryError";

  constructor(readonly requestedTenantId: string, readonly actualTenantId: string) {
    super(`Tenant boundary violation: requested ${requestedTenantId}, got ${actualTenantId}`);
  }
}

export class CausalLinkOwnershipError extends Error {
  readonly name = "CausalLinkOwnershipError";

  constructor(readonly linkTenantId: string, readonly linkDealId: string, readonly evidenceCallId: string) {
    super(
      `Causal link ownership violation: link ${linkTenantId}/${linkDealId} does not own evidence call ${evidenceCallId}`
    );
  }
}

export function isCurrentAt(validFrom: string, validTo: string | null, asOf?: string): boolean {
  if (!asOf) return validTo === null;
  const at = Date.parse(asOf);
  return Date.parse(validFrom) <= at && (validTo === null || at < Date.parse(validTo));
}

export function required<T>(value: T | undefined, message: string): T {
  if (value === undefined) throw new FixtureStoreLookupError(message);
  return value;
}

export function dealMemoryNode(record: DealMemory): MemoryNode<DealMemory> {
  return {
    id: `${record.deal_id}:deal_memory:${record.valid_from}`,
    tenant_id: record.tenant_id,
    kind: "DealMemory",
    record
  };
}

export function contactMemoryNode(record: ContactMemory): MemoryNode<ContactMemory> {
  return {
    id: `${record.contact_id}:contact_memory:${record.valid_from}`,
    tenant_id: record.tenant_id,
    kind: "ContactMemory",
    record
  };
}

export function callEventNode(record: CallEvent): MemoryNode<CallEvent> {
  return {
    id: record.call_id,
    tenant_id: record.tenant_id,
    kind: "CallEvent",
    record
  };
}

function knowledgeKind(record: KnowledgeRecord): KnowledgeNode["kind"] {
  if ("stage" in record) return "Playbook";
  if ("competitor_name" in record) return "Battlecard";
  return "ICPDefinition";
}

export function knowledgeNode(record: KnowledgeRecord): KnowledgeNode {
  return {
    id: record.id,
    tenant_id: record.tenant_id,
    kind: knowledgeKind(record),
    record
  };
}

export function createFixtureStoreState(seed: FixtureSeed): FixtureStoreState {
  return {
    tenants: [...(seed.tenants ?? tenants)],
    deals: [...(seed.deals ?? deals)],
    contacts: [...(seed.contacts ?? contacts)],
    dealMemories: [...(seed.dealMemories ?? dealMemories)],
    contactMemories: [...(seed.contactMemories ?? contactMemories)],
    callEvents: [...(seed.callEvents ?? callEvents)],
    causalLinks: [...(seed.causalLinks ?? causalLinks)],
    playbooks: [...(seed.playbooks ?? playbooks)],
    battlecards: [...(seed.battlecards ?? battlecards)],
    icpDefinitions: [...(seed.icpDefinitions ?? [])]
  };
}

export function closeOpenDealMemory(state: FixtureStoreState, memory: DealMemory): void {
  if (memory.valid_to !== null) return;
  state.dealMemories = state.dealMemories.map((candidate) => {
    if (
      candidate.deal_id === memory.deal_id &&
      candidate.tenant_id === memory.tenant_id &&
      candidate.valid_to === null &&
      Date.parse(candidate.valid_from) < Date.parse(memory.valid_from)
    ) {
      return { ...candidate, valid_to: memory.valid_from };
    }

    return candidate;
  });
}

export function closeOpenContactMemory(state: FixtureStoreState, memory: ContactMemory): void {
  if (memory.valid_to !== null) return;
  state.contactMemories = state.contactMemories.map((candidate) => {
    if (
      candidate.contact_id === memory.contact_id &&
      candidate.tenant_id === memory.tenant_id &&
      candidate.valid_to === null &&
      Date.parse(candidate.valid_from) < Date.parse(memory.valid_from)
    ) {
      return { ...candidate, valid_to: memory.valid_from };
    }

    return candidate;
  });
}
