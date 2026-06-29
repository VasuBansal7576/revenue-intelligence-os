import type { Battlecard, CausalLink, ICPDefinition, KnowledgeNode, Playbook } from "@causal-deal/types";
import type { FixtureStoreState } from "./fixture-store-state";

export function knowledgeNodesFor(
  state: FixtureStoreState,
  tenantId: string,
  dealStage: string,
  objectionTypes: string[],
  competitorNames: string[]
): KnowledgeNode[] {
  const playbookNodes: KnowledgeNode<Playbook>[] = state.playbooks
    .filter((playbook) => playbook.tenant_id === tenantId && playbook.active && playbook.stage === dealStage)
    .filter((playbook) => {
      if (objectionTypes.length === 0) return true;
      return playbook.objection_handlers.some((handler) => objectionTypes.includes(handler.objection_type));
    })
    .map((playbook) => ({
      id: playbook.id,
      tenant_id: playbook.tenant_id,
      kind: "Playbook",
      record: playbook
    }));

  const battlecardNodes: KnowledgeNode<Battlecard>[] = state.battlecards
    .filter((battlecard) => battlecard.tenant_id === tenantId && battlecard.active)
    .filter((battlecard) => competitorNames.includes(battlecard.competitor_name))
    .map((battlecard) => ({
      id: battlecard.id,
      tenant_id: battlecard.tenant_id,
      kind: "Battlecard",
      record: battlecard
    }));

  const icpNodes: KnowledgeNode<ICPDefinition>[] = state.icpDefinitions
    .filter((icpDefinition) => icpDefinition.tenant_id === tenantId && icpDefinition.active)
    .map((icpDefinition) => ({
      id: icpDefinition.id,
      tenant_id: icpDefinition.tenant_id,
      kind: "ICPDefinition",
      record: icpDefinition
    }));

  return [...playbookNodes, ...battlecardNodes, ...icpNodes];
}

export function causalLinksForDeal(state: FixtureStoreState, dealId: string, tenantId: string): CausalLink[] {
  const evidenceCallIds = new Set(
    state.callEvents
      .filter((event) => event.deal_id === dealId && event.tenant_id === tenantId)
      .map((event) => event.call_id)
  );
  return state.causalLinks.filter(
    (link) => link.deal_id === dealId && link.tenant_id === tenantId && evidenceCallIds.has(link.evidence_call_id)
  );
}

function causalLinkKey(link: CausalLink): string {
  return `${link.from_node_id}\n${link.to_node_id}\n${link.link_type}\n${link.evidence_call_id}`;
}

export function traverseCausalLinks(links: CausalLink[], fromNodeId: string | undefined, maxHops: number): CausalLink[] {
  if (!fromNodeId) return links.slice(0, maxHops);

  const result: CausalLink[] = [];
  const seen = new Set<string>();
  let frontier = new Set([fromNodeId]);

  for (let hop = 0; hop < maxHops; hop += 1) {
    const nextFrontier = new Set<string>();

    for (const link of links) {
      const key = causalLinkKey(link);
      if (!frontier.has(link.from_node_id) || seen.has(key)) continue;

      result.push(link);
      seen.add(key);
      nextFrontier.add(link.to_node_id);
    }

    if (nextFrontier.size === 0) break;
    frontier = nextFrontier;
  }

  return result;
}
