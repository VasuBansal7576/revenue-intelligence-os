import { describe, expect, it } from "vitest";
import type { CausalLink, DealMemory, DealRecord, Tenant } from "@causal-deal/types";
import { createFixtureStores, type FixtureSeed } from "../src/fixture-memory-store";
import { createHydraDbStores } from "../src/hydradb-memory-store";
import type { KnowledgeStore } from "../src/knowledge-store";
import type { MemoryStore } from "../src/memory-store";

type StorePair = {
  readonly memoryStore: MemoryStore;
  readonly knowledgeStore: KnowledgeStore;
};

const testStores = [
  {
    name: "fixture store",
    create: createFixtureStores
  },
  {
    name: "HydraDB adapter boundary with injected fixture driver",
    create: (seed?: FixtureSeed): StorePair => {
      const fixtureStores = createFixtureStores(seed);
      return createHydraDbStores({
        memory: fixtureStores.memoryStore,
        knowledge: fixtureStores.knowledgeStore
      });
    }
  }
] satisfies readonly {
  readonly name: string;
  readonly create: (seed?: FixtureSeed) => StorePair;
}[];

const tenantA = {
  id: "tenant_a",
  name: "Tenant A",
  domain: "a.example",
  environment: "test"
} satisfies Tenant;
const tenantB = {
  id: "tenant_b",
  name: "Tenant B",
  domain: "b.example",
  environment: "test"
} satisfies Tenant;
const sharedDealA = {
  id: "shared_deal",
  tenant_id: tenantA.id,
  account_name: "Shared A",
  name: "Shared deal A",
  owner_name: "Owner A",
  amount_usd: 1000,
  stage: "Tenant A Stage",
  status: "healthy",
  close_date: "2026-04-01"
} satisfies DealRecord;
const sharedDealB = {
  id: "shared_deal",
  tenant_id: tenantB.id,
  account_name: "Shared B",
  name: "Shared deal B",
  owner_name: "Owner B",
  amount_usd: 2000,
  stage: "Tenant B Stage",
  status: "stalling",
  close_date: "2026-04-02"
} satisfies DealRecord;
const sharedDealMemoryA = {
  deal_id: "shared_deal",
  tenant_id: tenantA.id,
  stage: "Tenant A Stage",
  champion_id: null,
  economic_buyer_id: null,
  champion_confidence: 0.8,
  budget_confirmed: true,
  technical_validated: true,
  active_objections: [],
  next_step_agreed: null,
  last_call_id: "call_a",
  valid_from: "2026-03-01T00:00:00.000Z",
  valid_to: null
} satisfies DealMemory;
const sharedDealMemoryB = {
  ...sharedDealMemoryA,
  tenant_id: tenantB.id,
  stage: "Tenant B Stage",
  champion_confidence: 0.2,
  budget_confirmed: false,
  last_call_id: "call_b"
} satisfies DealMemory;

describe.each(testStores)("$name tenant boundary", ({ create }) => {
  it("scopes tenant-local deal IDs before returning deal context", async () => {
    const { memoryStore } = create({
      tenants: [tenantA, tenantB],
      deals: [sharedDealA, sharedDealB],
      contacts: [],
      dealMemories: [sharedDealMemoryA, sharedDealMemoryB],
      contactMemories: [],
      callEvents: [],
      causalLinks: [],
      playbooks: [],
      battlecards: []
    });

    const context = await memoryStore.queryDealContext({
      deal_id: "shared_deal",
      tenant_id: tenantB.id
    });

    expect(context.tenant.id).toBe(tenantB.id);
    expect(context.deal.account_name).toBe("Shared B");
    expect(context.deal_memory.stage).toBe("Tenant B Stage");
  });

  it("blocks cross-tenant deal context reads", async () => {
    const { memoryStore } = create();

    await expect(
      memoryStore.queryDealContext({
        deal_id: "deal_northstar_expansion",
        tenant_id: "tenant_other"
      })
    ).rejects.toThrow("Tenant boundary violation");
  });

  it("blocks cross-tenant causal chain reads", async () => {
    const { memoryStore } = create();

    await expect(
      memoryStore.queryCausalChain({
        deal_id: "deal_northstar_expansion",
        tenant_id: "tenant_other"
      })
    ).rejects.toThrow("Tenant boundary violation");
  });

  it("rejects causal links whose evidence call belongs to another tenant or deal", async () => {
    const { memoryStore } = create();
    const poisonedLink = {
      tenant_id: "tenant_other",
      deal_id: "deal_other",
      from_node_id: "external:signal",
      to_node_id: "call_ns_005:budget_freeze",
      link_type: "stage_regression_triggered_by",
      confidence: 0.9,
      evidence_call_id: "call_ns_005",
      created_at: "2026-03-11T16:00:00.000Z"
    } satisfies CausalLink;

    await expect(memoryStore.writeCausalLink(poisonedLink)).rejects.toThrow("Causal link ownership violation");

    const context = await memoryStore.queryDealContext({
      deal_id: "deal_northstar_expansion",
      tenant_id: "tenant_novaridge"
    });
    const chain = await memoryStore.queryCausalChain({
      deal_id: "deal_northstar_expansion",
      tenant_id: "tenant_novaridge"
    });

    expect(context.causal_links).not.toContainEqual(poisonedLink);
    expect(chain.links).not.toContainEqual(poisonedLink);
  });
});
