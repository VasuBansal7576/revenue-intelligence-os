import type { DealContext, DealRecord } from "@causal-deal/types";
import type { KnowledgeStore } from "./knowledge-store";
import type { MemoryStore } from "./memory-store";
import { causalLinksForDeal, knowledgeNodesFor, traverseCausalLinks } from "./fixture-store-queries";
import {
  callEventNode,
  CausalLinkOwnershipError,
  closeOpenContactMemory,
  closeOpenDealMemory,
  contactMemoryNode,
  createFixtureStoreState,
  dealMemoryNode,
  FixtureStoreLookupError,
  isCurrentAt,
  knowledgeNode,
  required,
  TenantBoundaryError,
  type FixtureSeed
} from "./fixture-store-state";

type FixtureStorePair = {
  readonly memoryStore: MemoryStore;
  readonly knowledgeStore: KnowledgeStore;
};

export { CausalLinkOwnershipError, FixtureStoreLookupError, TenantBoundaryError };
export type { FixtureSeed };

function requiredDealForTenant(
  deals: DealRecord[],
  dealId: string,
  tenantId: string
): DealRecord {
  const deal = deals.find((candidate) => candidate.id === dealId && candidate.tenant_id === tenantId);
  if (deal) return deal;

  const otherTenantDeal = deals.find((candidate) => candidate.id === dealId);
  if (otherTenantDeal) {
    throw new TenantBoundaryError(tenantId, otherTenantDeal.tenant_id);
  }

  throw new FixtureStoreLookupError(`Unknown deal ${dealId}`);
}

export function createFixtureStores(seed: FixtureSeed = {}): FixtureStorePair {
  const state = createFixtureStoreState(seed);

  const knowledgeStore: KnowledgeStore = {
    async writeKnowledgeRecord(record) {
      if ("stage" in record) state.playbooks.push(record);
      else if ("competitor_name" in record) state.battlecards.push(record);
      else state.icpDefinitions.push(record);

      return knowledgeNode(record);
    },
    async queryRelevantKnowledge(params) {
      return knowledgeNodesFor(
        state,
        params.tenant_id,
        params.deal_stage,
        params.objection_types ?? [],
        params.competitor_names ?? []
      );
    }
  };

  const memoryStore: MemoryStore = {
    async writeDealMemory(memory) {
      closeOpenDealMemory(state, memory);
      state.dealMemories.push(memory);
      return dealMemoryNode(memory);
    },
    async writeContactMemory(memory) {
      closeOpenContactMemory(state, memory);
      state.contactMemories.push(memory);
      return contactMemoryNode(memory);
    },
    async writeCallEvent(event) {
      state.callEvents.push(event);
      return callEventNode(event);
    },
    async writeCausalLink(link) {
      const evidenceCall = required(
        state.callEvents.find((event) => event.call_id === link.evidence_call_id),
        `Unknown evidence call ${link.evidence_call_id}`
      );
      if (link.tenant_id !== evidenceCall.tenant_id || link.deal_id !== evidenceCall.deal_id) {
        throw new CausalLinkOwnershipError(link.tenant_id, link.deal_id, link.evidence_call_id);
      }
      state.causalLinks.push(link);
    },
    async queryDealContext(params) {
      const deal = requiredDealForTenant(state.deals, params.deal_id, params.tenant_id);

      const tenant = required(
        state.tenants.find((candidate) => candidate.id === params.tenant_id),
        `Unknown tenant ${params.tenant_id}`
      );
      const dealMemory = required(
        state.dealMemories.find(
          (memory) =>
            memory.deal_id === params.deal_id &&
            memory.tenant_id === params.tenant_id &&
            isCurrentAt(memory.valid_from, memory.valid_to, params.as_of)
        ),
        `No deal memory for ${params.deal_id}`
      );
      const dealContacts = state.contacts.filter(
        (contact) => contact.deal_id === params.deal_id && contact.tenant_id === params.tenant_id
      );
      const currentContactMemories = state.contactMemories.filter(
        (memory) =>
          memory.deal_id === params.deal_id &&
          memory.tenant_id === params.tenant_id &&
          isCurrentAt(memory.valid_from, memory.valid_to, params.as_of)
      );
      const dealCalls = state.callEvents
        .filter((event) => event.deal_id === params.deal_id && event.tenant_id === params.tenant_id)
        .filter((event) => !params.as_of || Date.parse(event.timestamp) <= Date.parse(params.as_of));
      const dealCallIds = new Set(dealCalls.map((event) => event.call_id));
      const dealLinks = state.causalLinks.filter(
        (link) =>
          link.tenant_id === params.tenant_id &&
          link.deal_id === params.deal_id &&
          dealCallIds.has(link.evidence_call_id)
      );
      const competitorNames = dealCalls.flatMap((event) =>
        event.competitive_mentions.map((mention) => mention.competitor_name)
      );

      return {
        tenant,
        deal,
        contacts: dealContacts,
        deal_memory: dealMemory,
        contact_memories: currentContactMemories,
        call_events: dealCalls,
        causal_links: dealLinks,
        knowledge_nodes: knowledgeNodesFor(
          state,
          params.tenant_id,
          dealMemory.stage,
          dealMemory.active_objections,
          competitorNames
        )
      } satisfies DealContext;
    },
    async queryCausalChain(params) {
      const deal = requiredDealForTenant(state.deals, params.deal_id, params.tenant_id);

      const links = causalLinksForDeal(state, params.deal_id, params.tenant_id);
      const maxHops = params.max_hops ?? links.length;

      return {
        deal_id: params.deal_id,
        tenant_id: params.tenant_id,
        links: traverseCausalLinks(links, params.from_node_id, maxHops)
      };
    }
  };

  return { memoryStore, knowledgeStore };
}
