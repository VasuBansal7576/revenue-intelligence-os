import type { CausalLink, DealContext } from "@causal-deal/types";

import { callEventNodeId, confidencePercent, contactMemoryNodeId, formatDateTime, nodeDomId } from "./format";

function EdgeList({ links }: { readonly links: CausalLink[] }) {
  return (
    <ol className="edge-list">
      {links.map((link) => (
        <li key={`${link.from_node_id}-${link.to_node_id}`}>
          <strong>{link.link_type}</strong>
          <span>
            <a href={`#${nodeDomId(link.from_node_id)}`}>{link.from_node_id}</a>
          </span>
          <span>
            <a href={`#${nodeDomId(link.to_node_id)}`}>{link.to_node_id}</a>
          </span>
          <code>
            <a href={`#${nodeDomId(link.evidence_call_id)}`}>{link.evidence_call_id}</a>
            {" / "}
            {confidencePercent(link.confidence)}
          </code>
        </li>
      ))}
    </ol>
  );
}

export function GraphPanel({ context }: { readonly context: DealContext }) {
  const contactNames = new Map(context.contacts.map((contact) => [contact.id, contact.name]));
  const graphCalls = context.call_events.filter((call) =>
    context.causal_links.some((link) => link.evidence_call_id === call.call_id)
  );

  return (
    <div className="graph-stack">
      <div className="graph-node graph-node-deal">
        <span>Deal</span>
        <strong>{context.deal.account_name}</strong>
        <code>{context.deal.id}</code>
      </div>

      <div className="graph-node-grid">
        {context.contact_memories.map((memory) => (
          <div className="graph-node" id={nodeDomId(contactMemoryNodeId(memory))} key={memory.contact_id}>
            <span>{memory.role}</span>
            <strong>{contactNames.get(memory.contact_id) ?? memory.contact_id}</strong>
            <code>{memory.engagement_level}</code>
          </div>
        ))}
      </div>

      <div className="graph-node-grid">
        {graphCalls.map((call) => (
          <div className="graph-node" id={nodeDomId(callEventNodeId(call))} key={call.call_id}>
            <span>CallEvent</span>
            <strong>{call.call_id}</strong>
            <code>{formatDateTime(call.timestamp)}</code>
          </div>
        ))}
      </div>

      <EdgeList links={context.causal_links} />
    </div>
  );
}
