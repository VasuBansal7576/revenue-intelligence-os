import type { ContactMemory, ContactRecord } from "@causal-deal/types";

export const contacts = [
  {
    id: "contact_elena",
    tenant_id: "tenant_novaridge",
    deal_id: "deal_northstar_expansion",
    name: "Elena Torres",
    title: "VP Operations",
    email: "elena.torres@northstar.example"
  },
  {
    id: "contact_marcus",
    tenant_id: "tenant_novaridge",
    deal_id: "deal_northstar_expansion",
    name: "Marcus Reid",
    title: "Chief Financial Officer",
    email: "marcus.reid@northstar.example"
  },
  {
    id: "contact_avi",
    tenant_id: "tenant_novaridge",
    deal_id: "deal_northstar_expansion",
    name: "Avi Raman",
    title: "Director of IT",
    email: "avi.raman@northstar.example"
  },
  {
    id: "contact_priya",
    tenant_id: "tenant_novaridge",
    deal_id: "deal_atlas_renewal",
    name: "Priya Shah",
    title: "Revenue Operations Lead",
    email: "priya.shah@atlas.example"
  },
  {
    id: "contact_daniel",
    tenant_id: "tenant_novaridge",
    deal_id: "deal_atlas_renewal",
    name: "Daniel Brooks",
    title: "Chief Operating Officer",
    email: "daniel.brooks@atlas.example"
  },
  {
    id: "contact_mina",
    tenant_id: "tenant_novaridge",
    deal_id: "deal_atlas_renewal",
    name: "Mina Okafor",
    title: "Security Manager",
    email: "mina.okafor@atlas.example"
  }
] satisfies ContactRecord[];

export const contactMemories = [
  {
    contact_id: "contact_elena",
    deal_id: "deal_northstar_expansion",
    tenant_id: "tenant_novaridge",
    role: "champion",
    engagement_level: "silent",
    last_seen_on_call: "call_ns_003",
    last_seen_timestamp: "2026-02-18T15:42:00.000Z",
    sentiment_trend: "declining",
    key_concerns: ["internal rollout load", "CFO approval path"],
    valid_from: "2026-03-04T15:00:00.000Z",
    valid_to: null
  },
  {
    contact_id: "contact_marcus",
    deal_id: "deal_northstar_expansion",
    tenant_id: "tenant_novaridge",
    role: "economic_buyer",
    engagement_level: "low",
    last_seen_on_call: "call_ns_002",
    last_seen_timestamp: "2026-02-11T15:18:00.000Z",
    sentiment_trend: "neutral",
    key_concerns: ["budget freeze", "implementation timing"],
    valid_from: "2026-03-04T15:00:00.000Z",
    valid_to: null
  },
  {
    contact_id: "contact_avi",
    deal_id: "deal_northstar_expansion",
    tenant_id: "tenant_novaridge",
    role: "technical_buyer",
    engagement_level: "medium",
    last_seen_on_call: "call_ns_005",
    last_seen_timestamp: "2026-03-04T15:33:00.000Z",
    sentiment_trend: "neutral",
    key_concerns: ["data warehouse sync", "single sign-on"],
    valid_from: "2026-03-04T15:00:00.000Z",
    valid_to: null
  },
  {
    contact_id: "contact_priya",
    deal_id: "deal_atlas_renewal",
    tenant_id: "tenant_novaridge",
    role: "champion",
    engagement_level: "high",
    last_seen_on_call: "call_at_003",
    last_seen_timestamp: "2026-02-26T17:48:00.000Z",
    sentiment_trend: "positive",
    key_concerns: ["legal turnaround"],
    valid_from: "2026-02-26T17:00:00.000Z",
    valid_to: null
  },
  {
    contact_id: "contact_daniel",
    deal_id: "deal_atlas_renewal",
    tenant_id: "tenant_novaridge",
    role: "economic_buyer",
    engagement_level: "high",
    last_seen_on_call: "call_at_003",
    last_seen_timestamp: "2026-02-26T17:40:00.000Z",
    sentiment_trend: "positive",
    key_concerns: ["board packet timing"],
    valid_from: "2026-02-26T17:00:00.000Z",
    valid_to: null
  },
  {
    contact_id: "contact_mina",
    deal_id: "deal_atlas_renewal",
    tenant_id: "tenant_novaridge",
    role: "technical_buyer",
    engagement_level: "medium",
    last_seen_on_call: "call_at_002",
    last_seen_timestamp: "2026-02-19T17:35:00.000Z",
    sentiment_trend: "neutral",
    key_concerns: ["SOC 2 evidence", "data retention"],
    valid_from: "2026-02-19T17:00:00.000Z",
    valid_to: null
  }
] satisfies ContactMemory[];
