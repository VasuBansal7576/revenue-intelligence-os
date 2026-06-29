import type {
  CallEvent,
  CausalChain,
  CausalLink,
  ContactMemory,
  DealContext,
  DealMemory,
  MemoryNode
} from "@causal-deal/types";

export interface MemoryStore {
  writeDealMemory(memory: DealMemory): Promise<MemoryNode<DealMemory>>;
  writeContactMemory(memory: ContactMemory): Promise<MemoryNode<ContactMemory>>;
  writeCallEvent(event: CallEvent): Promise<MemoryNode<CallEvent>>;
  writeCausalLink(link: CausalLink): Promise<void>;
  queryDealContext(params: {
    deal_id: string;
    tenant_id: string;
    as_of?: string;
  }): Promise<DealContext>;
  queryCausalChain(params: {
    deal_id: string;
    tenant_id: string;
    from_node_id?: string;
    max_hops?: number;
  }): Promise<CausalChain>;
}
