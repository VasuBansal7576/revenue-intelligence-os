import assert from "node:assert/strict";
import test from "node:test";

import { isDealBriefing, isDealContext, isTimeline } from "./api-contracts.ts";

const dealMemory = {
  deal_id: "deal_demo",
  tenant_id: "tenant_demo",
  stage: "Proposal",
  champion_id: null,
  economic_buyer_id: null,
  champion_confidence: 0.72,
  budget_confirmed: true,
  technical_validated: true,
  active_objections: ["budget_freeze"],
  next_step_agreed: "Confirm executive date",
  last_call_id: "call_demo",
  valid_from: "2026-03-04T15:00:00.000Z",
  valid_to: null
};

const callEvent = {
  call_id: "call_demo",
  deal_id: "deal_demo",
  tenant_id: "tenant_demo",
  timestamp: "2026-03-04T15:00:00.000Z",
  duration_seconds: 300,
  participants: ["contact_demo"],
  objections_raised: [
    {
      type: "budget_freeze",
      verbatim_quote: "Budget is paused.",
      contact_id: "contact_demo",
      severity: "high"
    }
  ],
  commitments_made: [
    {
      type: "exec_follow_up",
      made_by_contact_id: "contact_demo",
      due_date: "2026-03-07",
      verbatim: "I will confirm the executive date."
    }
  ],
  sentiment_shifts: [
    {
      contact_id: "contact_demo",
      from: "neutral",
      to: "positive",
      timestamp_in_call: 120,
      trigger_quote: "This is back on track."
    }
  ],
  competitive_mentions: [
    {
      competitor_name: "Status Quo",
      context: "Procurement compared doing nothing.",
      sentiment: "neutral"
    }
  ],
  champion_behavior: {
    contact_id: "contact_demo",
    signal_type: "active_advocacy",
    evidence_quote: "I will push this forward."
  },
  summary: "The champion agreed to confirm the executive date."
};

const context = {
  tenant: {
    id: "tenant_demo",
    name: "Demo Tenant",
    domain: "demo.example",
    environment: "test"
  },
  deal: {
    id: "deal_demo",
    tenant_id: "tenant_demo",
    account_name: "Demo Account",
    name: "Demo expansion",
    owner_name: "Maya Chen",
    amount_usd: 100000,
    stage: "Proposal",
    status: "healthy",
    close_date: "2026-04-30"
  },
  contacts: [
    {
      id: "contact_demo",
      tenant_id: "tenant_demo",
      deal_id: "deal_demo",
      name: "Demo Champion",
      title: "VP Operations",
      email: "demo@example.com"
    }
  ],
  deal_memory: dealMemory,
  contact_memories: [
    {
      contact_id: "contact_demo",
      deal_id: "deal_demo",
      tenant_id: "tenant_demo",
      role: "champion",
      engagement_level: "high",
      last_seen_on_call: "call_demo",
      last_seen_timestamp: "2026-03-04T15:03:00.000Z",
      sentiment_trend: "positive",
      key_concerns: ["budget_freeze"],
      valid_from: "2026-03-04T15:00:00.000Z",
      valid_to: null
    }
  ],
  call_events: [callEvent],
  causal_links: [
    {
      tenant_id: "tenant_demo",
      deal_id: "deal_demo",
      from_node_id: "call_demo:budget",
      to_node_id: "deal_demo:deal_memory:2026-03-04T15:00:00.000Z",
      link_type: "champion_silence_triggered_budget_objection",
      confidence: 0.81,
      evidence_call_id: "call_demo",
      created_at: "2026-03-04T16:00:00.000Z"
    }
  ],
  knowledge_nodes: [
    {
      id: "playbook_demo",
      tenant_id: "tenant_demo",
      kind: "Playbook",
      record: {
        id: "playbook_demo",
        tenant_id: "tenant_demo",
        stage: "Proposal",
        title: "Proposal recovery",
        content: "Confirm a named executive next step.",
        objection_handlers: [
          {
            objection_type: "budget_freeze",
            guidance: "Re-open the budget path with the economic buyer.",
            evidence_required: ["latest call", "current champion"]
          }
        ],
        version: 1,
        active: true
      }
    }
  ]
};

const timeline = {
  deal_id: "deal_demo",
  tenant_id: "tenant_demo",
  snapshots: [dealMemory],
  point_in_time: {
    as_of: "2026-03-04T15:00:00.000Z",
    deal_memory: dealMemory,
    call_event_ids: ["call_demo"]
  }
};

const briefing = {
  deal_id: "deal_demo",
  generated_at: "2026-03-04T15:05:00.000Z",
  status_summary: "The champion re-opened the executive path.",
  causal_diagnosis: [
    {
      description: "Budget pressure changed the next step.",
      causal_chain: ["call_demo", "deal_demo:deal_memory:2026-03-04T15:00:00.000Z"],
      evidence_node_ids: ["call_demo"]
    }
  ],
  risk_flags: [{ flag: "Budget pressure", severity: "high", evidence_node_id: "call_demo" }],
  next_best_actions: [
    {
      action: "Confirm the executive date.",
      rationale: "The latest memory has a named next step.",
      cited_memory_node_id: "deal_demo:deal_memory:2026-03-04T15:00:00.000Z",
      cited_knowledge_node_id: "playbook_demo"
    }
  ],
  confidence: 0.8
};

test("valid local-demo workbench payload passes contract guards", () => {
  assert.equal(isDealContext(context), true);
  assert.equal(isTimeline(timeline), true);
  assert.equal(isDealBriefing(briefing), true);
});

test("malformed nested API payloads fail contract guards", () => {
  assert.equal(
    isDealContext({
      ...context,
      call_events: [
        {
          ...callEvent,
          objections_raised: [{ ...callEvent.objections_raised[0], severity: "critical" }]
        }
      ]
    }),
    false
  );
  assert.equal(isTimeline({ ...timeline, snapshots: [{ ...dealMemory, valid_from: "not-a-date" }] }), false);
  assert.equal(isDealBriefing({ ...briefing, generated_at: "not-a-date" }), false);
});
