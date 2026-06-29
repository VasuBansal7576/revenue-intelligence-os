import type { KnowledgeNode, KnowledgeRecord } from "@causal-deal/types";

export interface KnowledgeStore {
  writeKnowledgeRecord(record: KnowledgeRecord): Promise<KnowledgeNode>;
  queryRelevantKnowledge(params: {
    tenant_id: string;
    deal_stage: string;
    objection_types?: string[];
    competitor_names?: string[];
  }): Promise<KnowledgeNode[]>;
}
