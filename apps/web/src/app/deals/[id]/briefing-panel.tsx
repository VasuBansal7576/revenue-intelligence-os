import type { DealBriefing, DealContext, NextBestAction } from "@causal-deal/types";

import { confidencePercent, formatDateTime, nodeDomId, signalTone } from "./format";
import { Badge } from "./ui";

function CitationLink({ id }: { readonly id: string }) {
  return (
    <code>
      <a href={`#${nodeDomId(id)}`}>{id}</a>
    </code>
  );
}

function ActionCitations({ action }: { readonly action: NextBestAction }) {
  return (
    <div className="badge-row">
      {action.cited_memory_node_id ? <CitationLink id={action.cited_memory_node_id} /> : null}
      {action.cited_knowledge_node_id ? <CitationLink id={action.cited_knowledge_node_id} /> : null}
    </div>
  );
}

export function BriefingPanel({ briefing, context }: { readonly briefing: DealBriefing; readonly context: DealContext }) {
  return (
    <div className="briefing">
      <article className="briefing-head">
        <div>
          <p>{context.deal.account_name}</p>
          <h1>{context.deal.name}</h1>
        </div>
        <Badge tone={context.deal.status === "healthy" ? "success" : "warning"}>{context.deal.stage}</Badge>
      </article>

      <section className="briefing-section">
        <h2>Status Summary</h2>
        <p>{briefing.status_summary}</p>
        <div className="badge-row">
          <Badge tone="info">{confidencePercent(briefing.confidence)}</Badge>
          <code>{formatDateTime(briefing.generated_at)}</code>
        </div>
      </section>

      <section className="briefing-section">
        <h2>Causal Diagnosis</h2>
        <ul className="evidence-list">
          {briefing.causal_diagnosis.map((diagnosis) => (
            <li key={diagnosis.description}>
              <strong>{diagnosis.description}</strong>
              <span>
                {diagnosis.causal_chain.map((nodeId, index) => (
                  <span key={`${diagnosis.description}-${nodeId}`}>
                    {index > 0 ? " -> " : ""}
                    <a href={`#${nodeDomId(nodeId)}`}>{nodeId}</a>
                  </span>
                ))}
              </span>
              <div className="badge-row">
                {diagnosis.evidence_node_ids.map((nodeId) => (
                  <CitationLink id={nodeId} key={nodeId} />
                ))}
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section className="briefing-section">
        <h2>Risk Flags</h2>
        <ul className="evidence-list">
          {briefing.risk_flags.map((risk) => (
            <li key={`${risk.flag}-${risk.evidence_node_id}`}>
              <div className="badge-row">
                <strong>{risk.flag}</strong>
                <Badge tone={signalTone(risk.severity)}>{risk.severity}</Badge>
              </div>
              <CitationLink id={risk.evidence_node_id} />
            </li>
          ))}
        </ul>
      </section>

      <section className="briefing-section">
        <h2>Next Actions</h2>
        <ul className="action-list">
          {briefing.next_best_actions.map((action) => (
            <li key={`${action.action}-${action.cited_memory_node_id ?? action.cited_knowledge_node_id}`}>
              <strong>{action.action}</strong>
              <span>{action.rationale}</span>
              <ActionCitations action={action} />
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
