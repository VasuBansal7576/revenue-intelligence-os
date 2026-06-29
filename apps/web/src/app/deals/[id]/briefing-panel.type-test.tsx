import type { DealBriefing, DealContext } from "@causal-deal/types";
import type { ReactElement } from "react";

import { BriefingPanel } from "./briefing-panel";

declare const context: DealContext;

const briefing: DealBriefing = {
  deal_id: "deal_123",
  generated_at: "2026-03-04T15:00:00.000Z",
  status_summary: "Buyer graph changed after the last call.",
  causal_diagnosis: [
    {
      description: "Champion silence followed the security objection.",
      causal_chain: ["call_001", "deal_memory_001"],
      evidence_node_ids: ["call_001"]
    }
  ],
  risk_flags: [{ flag: "Budget owner absent", severity: "high", evidence_node_id: "call_001" }],
  next_best_actions: [
    {
      action: "Confirm the budget owner before sending pricing.",
      rationale: "The latest memory snapshot has budget unconfirmed.",
      cited_memory_node_id: "deal_123:deal_memory:2026-03-04T15:00:00.000Z",
      cited_knowledge_node_id: "playbook_budget"
    }
  ],
  confidence: 0.81
};

const briefingPanel: ReactElement = <BriefingPanel context={context} briefing={briefing} />;

const missingActionBriefing: DealBriefing = {
  ...briefing,
  next_best_actions: [
    // @ts-expect-error DealBriefing actions must include API action text.
    {
      rationale: "The latest memory snapshot has budget unconfirmed.",
      cited_memory_node_id: "deal_123:deal_memory:2026-03-04T15:00:00.000Z",
      cited_knowledge_node_id: "playbook_budget"
    }
  ]
};

// @ts-expect-error BriefingPanel must fail closed without API briefing data.
const missingBriefing: ReactElement = <BriefingPanel context={context} />;

void briefingPanel;
void missingActionBriefing;
void missingBriefing;
