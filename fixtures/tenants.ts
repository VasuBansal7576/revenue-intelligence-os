import type { Tenant } from "@causal-deal/types";

export const tenants = [
  {
    id: "tenant_novaridge",
    name: "Nova Ridge Software",
    domain: "novaridge.example",
    environment: "test"
  }
] satisfies Tenant[];
