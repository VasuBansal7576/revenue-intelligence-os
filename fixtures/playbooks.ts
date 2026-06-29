import type { Playbook } from "@causal-deal/types";

export const playbooks = [
  {
    id: "playbook_proposal_risk",
    tenant_id: "tenant_novaridge",
    stage: "Proposal",
    title: "Proposal stage stall recovery",
    content: "When a proposal stalls after champion silence, re-open the business case with the economic buyer. Anchor the next action to a smaller rollout, named risk owner, and executive date.",
    objection_handlers: [
      {
        objection_type: "budget_freeze",
        guidance: "Bring the economic buyer back into the thread with a reduced rollout and explicit cost-of-delay math.",
        evidence_required: ["last economic buyer attendance", "current champion engagement", "active migration or budget freeze trigger"]
      },
      {
        objection_type: "competitor_discount",
        guidance: "Do not match the discount first. Show the risk of staying with the incumbent against the stated operations priority.",
        evidence_required: ["competitor name", "current business priority", "technical validation status"]
      }
    ],
    version: 1,
    active: true
  },
  {
    id: "playbook_legal_review",
    tenant_id: "tenant_novaridge",
    stage: "Legal Review",
    title: "Renewal legal close path",
    content: "When budget is confirmed and legal is the only active path, keep the champion and economic buyer aligned on redline date, board packet, and procurement owner.",
    objection_handlers: [
      {
        objection_type: "security_review",
        guidance: "Package SOC 2 evidence, retention policy, and security questionnaire status into the legal handoff.",
        evidence_required: ["security owner", "questionnaire status", "redline due date"]
      }
    ],
    version: 1,
    active: true
  }
] satisfies Playbook[];
