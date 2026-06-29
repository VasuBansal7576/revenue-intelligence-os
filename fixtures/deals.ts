import type { DealMemory, DealRecord } from "@causal-deal/types";

export const deals = [
  {
    id: "deal_northstar_expansion",
    tenant_id: "tenant_novaridge",
    account_name: "Northstar Logistics",
    name: "Northstar enterprise expansion",
    owner_name: "Maya Chen",
    amount_usd: 186000,
    stage: "Proposal",
    status: "stalling",
    close_date: "2026-04-30"
  },
  {
    id: "deal_atlas_renewal",
    tenant_id: "tenant_novaridge",
    account_name: "Atlas Medical Group",
    name: "Atlas platform renewal",
    owner_name: "Owen Patel",
    amount_usd: 92000,
    stage: "Legal Review",
    status: "healthy",
    close_date: "2026-03-28"
  }
] satisfies DealRecord[];

export const dealMemories = [
  {
    deal_id: "deal_northstar_expansion",
    tenant_id: "tenant_novaridge",
    stage: "Discovery",
    champion_id: "contact_elena",
    economic_buyer_id: "contact_marcus",
    champion_confidence: 0.82,
    budget_confirmed: false,
    technical_validated: false,
    active_objections: [],
    next_step_agreed: "Share technical validation plan",
    last_call_id: "call_ns_001",
    valid_from: "2026-02-04T15:00:00.000Z",
    valid_to: "2026-02-18T15:00:00.000Z"
  },
  {
    deal_id: "deal_northstar_expansion",
    tenant_id: "tenant_novaridge",
    stage: "Solution Validation",
    champion_id: "contact_elena",
    economic_buyer_id: "contact_marcus",
    champion_confidence: 0.58,
    budget_confirmed: false,
    technical_validated: true,
    active_objections: ["integration_risk"],
    next_step_agreed: "Run sandbox review with integrations team",
    last_call_id: "call_ns_003",
    valid_from: "2026-02-18T15:00:00.000Z",
    valid_to: "2026-03-04T15:00:00.000Z"
  },
  {
    deal_id: "deal_northstar_expansion",
    tenant_id: "tenant_novaridge",
    stage: "Proposal",
    champion_id: "contact_elena",
    economic_buyer_id: "contact_marcus",
    champion_confidence: 0.34,
    budget_confirmed: false,
    technical_validated: true,
    active_objections: ["budget_freeze", "competitor_discount"],
    next_step_agreed: "Send revised rollout plan to CFO",
    last_call_id: "call_ns_005",
    valid_from: "2026-03-04T15:00:00.000Z",
    valid_to: null
  },
  {
    deal_id: "deal_atlas_renewal",
    tenant_id: "tenant_novaridge",
    stage: "Business Case",
    champion_id: "contact_priya",
    economic_buyer_id: "contact_daniel",
    champion_confidence: 0.76,
    budget_confirmed: true,
    technical_validated: true,
    active_objections: ["security_review"],
    next_step_agreed: "Security sends signed questionnaire",
    last_call_id: "call_at_002",
    valid_from: "2026-02-12T17:00:00.000Z",
    valid_to: "2026-02-26T17:00:00.000Z"
  },
  {
    deal_id: "deal_atlas_renewal",
    tenant_id: "tenant_novaridge",
    stage: "Legal Review",
    champion_id: "contact_priya",
    economic_buyer_id: "contact_daniel",
    champion_confidence: 0.89,
    budget_confirmed: true,
    technical_validated: true,
    active_objections: [],
    next_step_agreed: "Procurement to return redlines",
    last_call_id: "call_at_003",
    valid_from: "2026-02-26T17:00:00.000Z",
    valid_to: null
  }
] satisfies DealMemory[];
