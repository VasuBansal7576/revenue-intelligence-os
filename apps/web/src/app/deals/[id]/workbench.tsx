import type { CallEvent, DealBriefing, DealContext, DealTimelineResponse } from "@causal-deal/types";
import Link from "next/link";
import type { ReactNode } from "react";

import { BriefingPanel } from "./briefing-panel";
import { EvidencePanel } from "./evidence-panel";
import { confidencePercent, dealMemoryNodeId, formatDateTime, formatMoney, nodeDomId, signalTone } from "./format";
import { GraphPanel } from "./graph-panel";
import { Badge } from "./ui";

function ScoreRow({ label, value }: { readonly label: string; readonly value: string }) {
  return (
    <div className="score-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Panel({ title, eyebrow, children }: { readonly title: string; readonly eyebrow: string; readonly children: ReactNode }) {
  return (
    <section className="panel" aria-labelledby={`${eyebrow}-title`}>
      <div className="panel-header">
        <p>{eyebrow}</p>
        <h2 id={`${eyebrow}-title`}>{title}</h2>
      </div>
      <div className="panel-body">{children}</div>
    </section>
  );
}

function DealList({ contexts, selectedDealId }: { readonly contexts: readonly DealContext[]; readonly selectedDealId: string }) {
  return (
    <nav className="deal-list" aria-label="Deals">
      {contexts.map((context) => {
        const isSelected = context.deal.id === selectedDealId;
        return (
          <Link className={`deal-row ${isSelected ? "deal-row-selected" : ""}`} href={`/deals/${context.deal.id}`} key={context.deal.id}>
            <div>
              <h3>{context.deal.account_name}</h3>
              <p>{context.deal.name}</p>
            </div>
            <div className="deal-row-meta">
              <Badge tone={context.deal.status === "healthy" ? "success" : "warning"}>{context.deal.status}</Badge>
              <span>{formatMoney(context.deal.amount_usd)}</span>
            </div>
          </Link>
        );
      })}
    </nav>
  );
}

function MemoryReplay({ dealId, timeline }: { readonly dealId: string; readonly timeline: DealTimelineResponse }) {
  const replay = timeline.point_in_time;
  return (
    <div className="briefing-section">
      <div className="badge-row">
        <Badge tone={replay ? "production" : "info"}>{replay ? "AS-OF REPLAY" : "CURRENT"}</Badge>
        <span>{replay ? formatDateTime(replay.as_of) : "Live latest memory"}</span>
        {replay ? <Link href={`/deals/${dealId}`}>Return current</Link> : null}
      </div>
      <ol className="memory-replay">
        {timeline.snapshots.map((memory) => (
          <li key={dealMemoryNodeId(memory)}>
            <div>
              <strong>{memory.stage}</strong>
              <code>
                <a href={`#${nodeDomId(dealMemoryNodeId(memory))}`}>{formatDateTime(memory.valid_from)}</a>
                {" -> "}
                {memory.valid_to ? formatDateTime(memory.valid_to) : "current"}
              </code>
            </div>
            <div className="deal-row-meta">
              <Badge tone={signalTone(memory.active_objections[0] ?? memory.stage)}>{confidencePercent(memory.champion_confidence)}</Badge>
              <Link href={`/deals/${dealId}?as_of=${encodeURIComponent(memory.valid_from)}`}>Replay</Link>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}

function CallTimeline({ calls }: { readonly calls: readonly CallEvent[] }) {
  return (
    <ol className="timeline">
      {calls.map((call) => {
        const objectionTypes = call.objections_raised.map((objection) => objection.type);
        const competitors = call.competitive_mentions.map((mention) => mention.competitor_name);
        return (
          <li className="timeline-item" key={call.call_id}>
            <div className="timeline-stamp">
              <span>{formatDateTime(call.timestamp)}</span>
              <code>{call.call_id}</code>
            </div>
            <h3>{call.summary}</h3>
            <div className="badge-row">
              <Badge tone="info">{call.champion_behavior.signal_type}</Badge>
              {objectionTypes.map((type) => (
                <Badge key={type} tone={signalTone(type)}>
                  {type}
                </Badge>
              ))}
              {competitors.map((competitor) => (
                <Badge key={competitor} tone="warning">
                  {competitor}
                </Badge>
              ))}
            </div>
          </li>
        );
      })}
    </ol>
  );
}

export function DealWorkbench({
  briefing,
  contexts,
  selectedContext,
  timeline
}: {
  readonly briefing: DealBriefing;
  readonly contexts: readonly DealContext[];
  readonly selectedContext: DealContext;
  readonly timeline: DealTimelineResponse;
}) {
  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p>Causal Deal Intelligence</p>
          <h1>Operator Console</h1>
        </div>
        <div className="topbar-meta">
          <Badge tone="production">PRODUCTION</Badge>
          <span>{selectedContext.tenant.name}</span>
          <code>{selectedContext.tenant.id}</code>
        </div>
      </header>

      <div className="console-grid">
        <Panel eyebrow="timeline" title="Deal Replay">
          <DealList contexts={contexts} selectedDealId={selectedContext.deal.id} />
          <MemoryReplay dealId={selectedContext.deal.id} timeline={timeline} />
          <CallTimeline calls={selectedContext.call_events} />
        </Panel>

        <Panel eyebrow="briefing" title="Cited Briefing">
          <div className="score-grid">
            <ScoreRow label="Champion confidence" value={confidencePercent(selectedContext.deal_memory.champion_confidence)} />
            <ScoreRow label="Budget confirmed" value={selectedContext.deal_memory.budget_confirmed ? "Yes" : "No"} />
            <ScoreRow label="Technical validation" value={selectedContext.deal_memory.technical_validated ? "Passed" : "Pending"} />
            <ScoreRow label="Last call" value={selectedContext.deal_memory.last_call_id} />
          </div>
          <BriefingPanel briefing={briefing} context={selectedContext} />
        </Panel>

        <Panel eyebrow="graph" title="Causal Graph">
          <GraphPanel context={selectedContext} />
        </Panel>

        <Panel eyebrow="evidence" title="Evidence Inspector">
          <EvidencePanel context={selectedContext} timeline={timeline} />
        </Panel>
      </div>
    </main>
  );
}
