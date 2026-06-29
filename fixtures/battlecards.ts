import type { Battlecard } from "@causal-deal/types";

export const battlecards = [
  {
    id: "battlecard_callpilot",
    tenant_id: "tenant_novaridge",
    competitor_name: "CallPilot",
    our_strengths: [
      "Causal memory links objections to prior deal events.",
      "Point-in-time replay shows what the team knew before a proposal was sent.",
      "Fixture and live modes expose the data boundary clearly."
    ],
    their_weaknesses: [
      "Discount-led renewal motion can preserve stale workflows.",
      "Transcript search does not explain why the deal state changed.",
      "Weak account memory when the economic buyer re-enters late."
    ],
    traps_to_avoid: [
      "Do not frame the answer as cheaper call recording.",
      "Do not claim customer evidence unless source citations are present.",
      "Do not recommend discount matching without cited evidence."
    ],
    win_themes: [
      "Recover the business case from causal evidence.",
      "Show why the incumbent discount appeared now.",
      "Make next action cite Memory and Knowledge nodes."
    ],
    version: 1,
    active: true
  },
  {
    id: "battlecard_status_quo",
    tenant_id: "tenant_novaridge",
    competitor_name: "Status Quo",
    our_strengths: [
      "Connects champion behavior, budget risk, and technical validation in one graph.",
      "Preserves valid-time deal state instead of overwriting CRM fields."
    ],
    their_weaknesses: [
      "Manual CRM notes lose the order of events.",
      "Managers cannot replay why a recommendation was made."
    ],
    traps_to_avoid: [
      "Do not bury the evidence behind a generic AI summary."
    ],
    win_themes: [
      "Timestamped proof beats stale pipeline opinion.",
      "Every recommendation must cite a node."
    ],
    version: 1,
    active: true
  }
] satisfies Battlecard[];
