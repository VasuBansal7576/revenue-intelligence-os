import type { CallEvent, CausalLink } from "@causal-deal/types";

export const callEvents = [
  {
    call_id: "call_ns_001",
    deal_id: "deal_northstar_expansion",
    tenant_id: "tenant_novaridge",
    timestamp: "2026-02-04T15:00:00.000Z",
    duration_seconds: 2360,
    participants: ["contact_elena", "contact_avi"],
    objections_raised: [],
    commitments_made: [
      {
        type: "technical_validation_plan",
        made_by_contact_id: "contact_elena",
        due_date: "2026-02-07",
        verbatim: "I can get Avi into the validation plan this week."
      }
    ],
    sentiment_shifts: [],
    competitive_mentions: [],
    champion_behavior: {
      contact_id: "contact_elena",
      signal_type: "active_advocacy",
      evidence_quote: "This would take the weekly ops review from manual to automatic."
    },
    summary: "Elena framed the expansion as an operations priority and pulled Avi into technical validation."
  },
  {
    call_id: "call_ns_002",
    deal_id: "deal_northstar_expansion",
    tenant_id: "tenant_novaridge",
    timestamp: "2026-02-11T15:00:00.000Z",
    duration_seconds: 1815,
    participants: ["contact_elena", "contact_marcus", "contact_avi"],
    objections_raised: [
      {
        type: "implementation_timing",
        verbatim_quote: "The team cannot absorb another deployment before quarter end.",
        contact_id: "contact_marcus",
        severity: "medium"
      }
    ],
    commitments_made: [
      {
        type: "cfo_review",
        made_by_contact_id: "contact_marcus",
        due_date: "2026-02-18",
        verbatim: "Send me the rollout plan and I will review the budget path."
      }
    ],
    sentiment_shifts: [
      {
        contact_id: "contact_marcus",
        from: "neutral",
        to: "negative",
        timestamp_in_call: 902,
        trigger_quote: "I need to see this not distract the logistics migration."
      }
    ],
    competitive_mentions: [],
    champion_behavior: {
      contact_id: "contact_elena",
      signal_type: "passive",
      evidence_quote: "Elena deferred the budget question to Marcus."
    },
    summary: "Marcus entered as economic buyer and introduced timing risk around quarter-end deployment."
  },
  {
    call_id: "call_ns_003",
    deal_id: "deal_northstar_expansion",
    tenant_id: "tenant_novaridge",
    timestamp: "2026-02-18T15:00:00.000Z",
    duration_seconds: 2040,
    participants: ["contact_elena", "contact_avi"],
    objections_raised: [
      {
        type: "integration_risk",
        verbatim_quote: "If the warehouse sync is brittle, support will blame my team.",
        contact_id: "contact_avi",
        severity: "medium"
      }
    ],
    commitments_made: [
      {
        type: "sandbox_review",
        made_by_contact_id: "contact_avi",
        due_date: "2026-02-25",
        verbatim: "I will run the sandbox review if you send the SSO notes today."
      }
    ],
    sentiment_shifts: [
      {
        contact_id: "contact_elena",
        from: "positive",
        to: "neutral",
        timestamp_in_call: 1440,
        trigger_quote: "I need to see Marcus stay with us on this."
      }
    ],
    competitive_mentions: [],
    champion_behavior: {
      contact_id: "contact_elena",
      signal_type: "passive",
      evidence_quote: "Elena stopped volunteering internal next steps after Marcus missed the call."
    },
    summary: "Technical validation moved forward, but Elena's advocacy softened after Marcus skipped the review."
  },
  {
    call_id: "call_ns_004",
    deal_id: "deal_northstar_expansion",
    tenant_id: "tenant_novaridge",
    timestamp: "2026-02-25T15:00:00.000Z",
    duration_seconds: 1680,
    participants: ["contact_avi"],
    objections_raised: [],
    commitments_made: [
      {
        type: "security_notes",
        made_by_contact_id: "contact_avi",
        due_date: "2026-02-28",
        verbatim: "I will send the security notes, but I do not own budget."
      }
    ],
    sentiment_shifts: [],
    competitive_mentions: [],
    champion_behavior: {
      contact_id: "contact_elena",
      signal_type: "silence",
      evidence_quote: "Elena declined the invite and did not name a replacement."
    },
    summary: "Only Avi attended. The champion was absent and no business owner committed to next steps."
  },
  {
    call_id: "call_ns_005",
    deal_id: "deal_northstar_expansion",
    tenant_id: "tenant_novaridge",
    timestamp: "2026-03-04T15:00:00.000Z",
    duration_seconds: 1972,
    participants: ["contact_avi"],
    objections_raised: [
      {
        type: "budget_freeze",
        verbatim_quote: "Marcus paused new spend until the logistics migration clears.",
        contact_id: "contact_avi",
        severity: "high"
      },
      {
        type: "competitor_discount",
        verbatim_quote: "Procurement asked whether the incumbent discount is safer for now.",
        contact_id: "contact_avi",
        severity: "high"
      }
    ],
    commitments_made: [
      {
        type: "revised_rollout_plan",
        made_by_contact_id: "contact_avi",
        due_date: "2026-03-07",
        verbatim: "Send a smaller rollout plan and I will forward it."
      }
    ],
    sentiment_shifts: [
      {
        contact_id: "contact_avi",
        from: "neutral",
        to: "negative",
        timestamp_in_call: 611,
        trigger_quote: "I am not sure who is still pushing this internally."
      }
    ],
    competitive_mentions: [
      {
        competitor_name: "CallPilot",
        context: "Procurement asked about extending the incumbent at a discount.",
        sentiment: "positive"
      }
    ],
    champion_behavior: {
      contact_id: "contact_elena",
      signal_type: "silence",
      evidence_quote: "Elena has not replied to the revised proposal thread."
    },
    summary: "The deal moved into stall risk: champion silence preceded budget freeze and incumbent discount pressure."
  },
  {
    call_id: "call_at_001",
    deal_id: "deal_atlas_renewal",
    tenant_id: "tenant_novaridge",
    timestamp: "2026-02-05T17:00:00.000Z",
    duration_seconds: 1880,
    participants: ["contact_priya", "contact_daniel"],
    objections_raised: [],
    commitments_made: [
      {
        type: "renewal_business_case",
        made_by_contact_id: "contact_priya",
        due_date: "2026-02-10",
        verbatim: "I will update the renewal case with the adoption numbers."
      }
    ],
    sentiment_shifts: [],
    competitive_mentions: [],
    champion_behavior: {
      contact_id: "contact_priya",
      signal_type: "active_advocacy",
      evidence_quote: "Priya said she would present the renewal case herself."
    },
    summary: "Atlas renewal opened with Daniel confirming budget and Priya owning the internal case."
  },
  {
    call_id: "call_at_002",
    deal_id: "deal_atlas_renewal",
    tenant_id: "tenant_novaridge",
    timestamp: "2026-02-19T17:00:00.000Z",
    duration_seconds: 2140,
    participants: ["contact_priya", "contact_mina"],
    objections_raised: [
      {
        type: "security_review",
        verbatim_quote: "We need the SOC 2 bridge letter before signature.",
        contact_id: "contact_mina",
        severity: "medium"
      }
    ],
    commitments_made: [
      {
        type: "security_questionnaire",
        made_by_contact_id: "contact_mina",
        due_date: "2026-02-23",
        verbatim: "Send the packet and I will clear the security questionnaire."
      }
    ],
    sentiment_shifts: [],
    competitive_mentions: [],
    champion_behavior: {
      contact_id: "contact_priya",
      signal_type: "active_advocacy",
      evidence_quote: "Priya asked Mina to keep the review on the renewal timeline."
    },
    summary: "Security review became the only active objection and Priya kept the process moving."
  },
  {
    call_id: "call_at_003",
    deal_id: "deal_atlas_renewal",
    tenant_id: "tenant_novaridge",
    timestamp: "2026-02-26T17:00:00.000Z",
    duration_seconds: 1755,
    participants: ["contact_priya", "contact_daniel"],
    objections_raised: [],
    commitments_made: [
      {
        type: "legal_redlines",
        made_by_contact_id: "contact_daniel",
        due_date: "2026-03-03",
        verbatim: "Procurement will return redlines by Tuesday."
      }
    ],
    sentiment_shifts: [
      {
        contact_id: "contact_daniel",
        from: "neutral",
        to: "positive",
        timestamp_in_call: 804,
        trigger_quote: "This is already in the board packet."
      }
    ],
    competitive_mentions: [],
    champion_behavior: {
      contact_id: "contact_priya",
      signal_type: "active_advocacy",
      evidence_quote: "Priya confirmed she added the renewal to Daniel's board packet."
    },
    summary: "The renewal advanced to legal with budget confirmed and the security objection resolved."
  }
] satisfies CallEvent[];

export const causalLinks = [
  {
    tenant_id: "tenant_novaridge",
    deal_id: "deal_northstar_expansion",
    from_node_id: "call_ns_003:champion_behavior",
    to_node_id: "call_ns_004:champion_behavior",
    link_type: "commitment_broken_triggered_trust_loss",
    confidence: 0.68,
    evidence_call_id: "call_ns_004",
    created_at: "2026-02-25T16:00:00.000Z"
  },
  {
    tenant_id: "tenant_novaridge",
    deal_id: "deal_northstar_expansion",
    from_node_id: "call_ns_004:champion_behavior",
    to_node_id: "call_ns_005:budget_freeze",
    link_type: "champion_silence_triggered_budget_objection",
    confidence: 0.81,
    evidence_call_id: "call_ns_005",
    created_at: "2026-03-04T16:00:00.000Z"
  },
  {
    tenant_id: "tenant_novaridge",
    deal_id: "deal_northstar_expansion",
    from_node_id: "call_ns_005:competitive_mentions",
    to_node_id: "call_ns_005:competitor_discount",
    link_type: "competitor_mention_triggered_pricing_concern",
    confidence: 0.74,
    evidence_call_id: "call_ns_005",
    created_at: "2026-03-04T16:01:00.000Z"
  },
  {
    tenant_id: "tenant_novaridge",
    deal_id: "deal_northstar_expansion",
    from_node_id: "call_ns_002:economic_buyer_presence",
    to_node_id: "call_ns_004:deal_stall",
    link_type: "economic_buyer_absence_triggered_stall",
    confidence: 0.7,
    evidence_call_id: "call_ns_004",
    created_at: "2026-02-25T16:02:00.000Z"
  },
  {
    tenant_id: "tenant_novaridge",
    deal_id: "deal_atlas_renewal",
    from_node_id: "call_at_002:security_review",
    to_node_id: "call_at_003:legal_review",
    link_type: "technical_objection_resolved_by_validation",
    confidence: 0.77,
    evidence_call_id: "call_at_003",
    created_at: "2026-02-26T18:00:00.000Z"
  }
] satisfies CausalLink[];

export const callTranscripts = {
  call_ns_001: "Elena: This would take the weekly ops review from manual to automatic. Avi should join the validation plan this week.",
  call_ns_002: "Marcus: The team cannot absorb another deployment before quarter end. Send me the rollout plan and I will review the budget path.",
  call_ns_003: "Avi: If the warehouse sync is brittle, support will blame my team. Elena: I need to see Marcus stay with us on this.",
  call_ns_004: "Avi: I will send the security notes, but I do not own budget. Elena declined the invite and did not name a replacement.",
  call_ns_005: "Avi: Marcus paused new spend until the logistics migration clears. Procurement asked whether the incumbent discount is safer for now.",
  call_at_001: "Priya: I will update the renewal case with the adoption numbers. Daniel: Budget is already planned.",
  call_at_002: "Mina: We need the SOC 2 bridge letter before signature. Priya: Let's keep this on the renewal timeline.",
  call_at_003: "Daniel: Procurement will return redlines by Tuesday. This is already in the board packet."
} as const;
