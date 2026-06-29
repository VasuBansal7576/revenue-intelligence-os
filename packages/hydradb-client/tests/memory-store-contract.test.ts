import { describe, expect, it } from "vitest";
import type { CallEvent, CausalLink, ContactMemory, DealMemory, Playbook } from "@causal-deal/types";
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

describe.each(testStores)("$name contract", ({ create }) => {
  it("returns Memory and Knowledge context for a deal", async () => {
    const { memoryStore, knowledgeStore } = create();

    const context = await memoryStore.queryDealContext({
      deal_id: "deal_northstar_expansion",
      tenant_id: "tenant_novaridge"
    });

    expect(context.deal_memory.stage).toBe("Proposal");
    expect(context.contact_memories.map((memory) => memory.contact_id)).toContain("contact_elena");
    expect(context.call_events.map((event) => event.call_id)).toContain("call_ns_005");
    expect(context.knowledge_nodes.map((node) => node.id)).toEqual(
      expect.arrayContaining(["playbook_proposal_risk", "battlecard_callpilot"])
    );

    const knowledge = await knowledgeStore.queryRelevantKnowledge({
      tenant_id: "tenant_novaridge",
      deal_stage: "Proposal",
      objection_types: ["budget_freeze"],
      competitor_names: ["CallPilot"]
    });

    expect(knowledge.map((node) => node.id)).toEqual(
      expect.arrayContaining(["playbook_proposal_risk", "battlecard_callpilot"])
    );
  });

  it("persists memory, call, causal, and knowledge writes", async () => {
    const { memoryStore, knowledgeStore } = create();
    const nextMemory = {
      deal_id: "deal_northstar_expansion",
      tenant_id: "tenant_novaridge",
      stage: "Proposal",
      champion_id: "contact_elena",
      economic_buyer_id: "contact_marcus",
      champion_confidence: 0.22,
      budget_confirmed: false,
      technical_validated: true,
      active_objections: ["executive_alignment"],
      next_step_agreed: "Book CFO reset call",
      last_call_id: "call_ns_006",
      valid_from: "2026-03-11T15:00:00.000Z",
      valid_to: null
    } satisfies DealMemory;
    const contactMemory = {
      contact_id: "contact_elena",
      deal_id: "deal_northstar_expansion",
      tenant_id: "tenant_novaridge",
      role: "champion",
      engagement_level: "silent",
      last_seen_on_call: "call_ns_006",
      last_seen_timestamp: "2026-03-11T15:10:00.000Z",
      sentiment_trend: "declining",
      key_concerns: ["executive reset"],
      valid_from: "2026-03-11T15:00:00.000Z",
      valid_to: null
    } satisfies ContactMemory;
    const call = {
      call_id: "call_ns_006",
      deal_id: "deal_northstar_expansion",
      tenant_id: "tenant_novaridge",
      timestamp: "2026-03-11T15:00:00.000Z",
      duration_seconds: 1200,
      participants: ["contact_avi"],
      objections_raised: [
        {
          type: "executive_alignment",
          verbatim_quote: "Marcus needs to restart this with Elena.",
          contact_id: "contact_avi",
          severity: "high"
        }
      ],
      commitments_made: [],
      sentiment_shifts: [],
      competitive_mentions: [],
      champion_behavior: {
        contact_id: "contact_elena",
        signal_type: "silence",
        evidence_quote: "Elena has not joined the last two calls."
      },
      summary: "Avi confirmed executive alignment is now the blocker."
    } satisfies CallEvent;
    const causalLink = {
      tenant_id: "tenant_novaridge",
      deal_id: "deal_northstar_expansion",
      from_node_id: "call_ns_005:budget_freeze",
      to_node_id: "call_ns_006:executive_alignment",
      link_type: "stage_regression_triggered_by",
      confidence: 0.72,
      evidence_call_id: "call_ns_006",
      created_at: "2026-03-11T16:00:00.000Z"
    } satisfies CausalLink;
    const playbook = {
      id: "playbook_exec_reset",
      tenant_id: "tenant_novaridge",
      stage: "Proposal",
      title: "Executive reset",
      content: "When executive alignment is the blocker, schedule a reset with the economic buyer.",
      objection_handlers: [
        {
          objection_type: "executive_alignment",
          guidance: "Rebuild the business case with the CFO.",
          evidence_required: ["economic buyer absence", "champion silence"]
        }
      ],
      version: 1,
      active: true
    } satisfies Playbook;

    await memoryStore.writeDealMemory(nextMemory);
    await memoryStore.writeContactMemory(contactMemory);
    await memoryStore.writeCallEvent(call);
    await memoryStore.writeCausalLink(causalLink);
    await knowledgeStore.writeKnowledgeRecord(playbook);

    const context = await memoryStore.queryDealContext({
      deal_id: "deal_northstar_expansion",
      tenant_id: "tenant_novaridge"
    });

    expect(context.deal_memory.active_objections).toEqual(["executive_alignment"]);
    expect(context.contact_memories).toContainEqual(contactMemory);
    expect(context.call_events.map((event) => event.call_id)).toContain("call_ns_006");
    expect(context.causal_links).toContainEqual(causalLink);
    expect(context.knowledge_nodes.map((node) => node.id)).toContain("playbook_exec_reset");
  });
});
