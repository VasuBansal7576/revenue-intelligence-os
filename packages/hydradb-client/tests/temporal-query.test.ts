import { describe, expect, it } from "vitest";
import { createFixtureStores } from "../src/fixture-memory-store";
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
    create: (): StorePair => {
      const fixtureStores = createFixtureStores();
      return createHydraDbStores({
        memory: fixtureStores.memoryStore,
        knowledge: fixtureStores.knowledgeStore
      });
    }
  }
] satisfies readonly {
  readonly name: string;
  readonly create: () => StorePair;
}[];

describe.each(testStores)("$name temporal behavior", ({ create }) => {
  it("returns point-in-time deal state for as_of queries", async () => {
    const { memoryStore } = create();

    const discovery = await memoryStore.queryDealContext({
      deal_id: "deal_northstar_expansion",
      tenant_id: "tenant_novaridge",
      as_of: "2026-02-10T15:00:00.000Z"
    });
    const proposal = await memoryStore.queryDealContext({
      deal_id: "deal_northstar_expansion",
      tenant_id: "tenant_novaridge",
      as_of: "2026-03-05T15:00:00.000Z"
    });

    expect(discovery.deal_memory.stage).toBe("Discovery");
    expect(discovery.call_events.map((event) => event.call_id)).toEqual(["call_ns_001"]);
    expect(proposal.deal_memory.stage).toBe("Proposal");
    expect(proposal.call_events.map((event) => event.call_id)).toContain("call_ns_005");
  });

  it("traverses causal chain from a starting node up to max_hops", async () => {
    const { memoryStore } = create();

    const chain = await memoryStore.queryCausalChain({
      deal_id: "deal_northstar_expansion",
      tenant_id: "tenant_novaridge",
      from_node_id: "call_ns_003:champion_behavior",
      max_hops: 1
    });

    expect(chain.links.map((link) => link.to_node_id)).toEqual(["call_ns_004:champion_behavior"]);
  });
});
