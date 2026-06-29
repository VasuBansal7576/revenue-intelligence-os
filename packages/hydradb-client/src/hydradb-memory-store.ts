import type { KnowledgeStore } from "./knowledge-store";
import type { MemoryStore } from "./memory-store";

export type HydraDbAdapterBoundaryDriver = {
  readonly memory: MemoryStore;
  readonly knowledge: KnowledgeStore;
};

export type HydraDbStorePair = {
  readonly memoryStore: MemoryStore;
  readonly knowledgeStore: KnowledgeStore;
};

export function createHydraDbStores(driver: HydraDbAdapterBoundaryDriver): HydraDbStorePair {
  return {
    memoryStore: driver.memory,
    knowledgeStore: driver.knowledge
  };
}
