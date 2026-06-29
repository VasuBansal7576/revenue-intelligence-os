import type { DealContext, DealTimelineResponse } from "@causal-deal/types";

import { callEventNodeId, causalLinkNodeId, contactMemoryNodeId, dealMemoryNodeId, formatDateTime, nodeDomId, signalTone } from "./format";
import { Badge } from "./ui";

export function EvidencePanel({ context, timeline }: { readonly context: DealContext; readonly timeline: DealTimelineResponse }) {
  return (
    <div className="evidence-inspector">
      <section className="briefing-section">
        <h2>Memory Nodes</h2>
        <ul className="node-list">
          {timeline.snapshots.map((memory) => (
            <li className="node-card" id={nodeDomId(dealMemoryNodeId(memory))} key={dealMemoryNodeId(memory)}>
              <div>
                <strong>{memory.stage}</strong>
                <code>
                  {formatDateTime(memory.valid_from)}
                  {" -> "}
                  {memory.valid_to ? formatDateTime(memory.valid_to) : "current"}
                </code>
              </div>
              <span>{memory.next_step_agreed}</span>
              <div className="badge-row">
                {memory.active_objections.map((objection) => (
                  <Badge key={objection} tone={signalTone(objection)}>
                    {objection}
                  </Badge>
                ))}
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section className="briefing-section">
        <h2>Contact Memory</h2>
        <ul className="node-list">
          {context.contact_memories.map((memory) => (
            <li className="node-card" id={nodeDomId(contactMemoryNodeId(memory))} key={contactMemoryNodeId(memory)}>
              <div>
                <strong>{memory.role}</strong>
                <code>{contactMemoryNodeId(memory)}</code>
              </div>
              <span>{memory.sentiment_trend}</span>
              <div className="badge-row">
                <Badge tone="info">{memory.engagement_level}</Badge>
                {memory.key_concerns.map((concern) => (
                  <Badge key={concern} tone={signalTone(concern)}>
                    {concern}
                  </Badge>
                ))}
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section className="briefing-section">
        <h2>Call Evidence</h2>
        <ul className="node-list">
          {context.call_events.map((call) => (
            <li className="node-card" id={nodeDomId(callEventNodeId(call))} key={callEventNodeId(call)}>
              <div>
                <strong>{call.call_id}</strong>
                <code>{formatDateTime(call.timestamp)}</code>
              </div>
              <span>{call.summary}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="briefing-section">
        <h2>Causal Links</h2>
        <ul className="node-list">
          {context.causal_links.map((link) => (
            <li className="node-card" id={nodeDomId(causalLinkNodeId(link))} key={causalLinkNodeId(link)}>
              <div>
                <strong>{link.link_type}</strong>
                <code>{causalLinkNodeId(link)}</code>
              </div>
              <span>
                <a href={`#${nodeDomId(link.from_node_id)}`}>{link.from_node_id}</a>
                {" -> "}
                <a href={`#${nodeDomId(link.to_node_id)}`}>{link.to_node_id}</a>
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section className="briefing-section">
        <h2>Knowledge Nodes</h2>
        <ul className="node-list">
          {context.knowledge_nodes.map((node) => (
            <li className="node-card" id={nodeDomId(node.id)} key={node.id}>
              <div>
                <strong>{node.kind}</strong>
                <code>{node.id}</code>
              </div>
              <span>{node.record.tenant_id}</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
