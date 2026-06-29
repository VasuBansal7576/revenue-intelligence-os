import { apiConfig, apiUrl, fetchJson } from "./api";

export type RecordMap = Readonly<Record<string, unknown>>;

type SetupRequiredData = {
  readonly kind: "setup_required";
  readonly message: string;
};

type EndpointSpec = {
  readonly label: string;
  readonly path: string;
  readonly method?: "GET" | "POST";
  readonly body?: RecordMap;
  readonly heading: string;
};

export type RouteSpec = {
  readonly title: string;
  readonly eyebrow: string;
  readonly summary: string;
  readonly endpoints: readonly EndpointSpec[];
  readonly titleFields: readonly string[];
  readonly metaFields: readonly string[];
  readonly detailFields: readonly string[];
};

type SectionData = {
  readonly heading: string;
  readonly items: readonly RecordMap[];
};

type RouteData =
  | {
      readonly kind: "ready";
      readonly sections: readonly SectionData[];
    }
  | SetupRequiredData;

export const routeKeys = ["deals", "accounts", "calls", "forecast", "coaching", "engage", "assistant", "admin", "ingestion"] as const;

export type RevenueRouteKey = (typeof routeKeys)[number];

const ROUTES: Record<RevenueRouteKey, RouteSpec> = {
  deals: {
    title: "Deals",
    eyebrow: "pipeline",
    summary: "Tenant-authenticated deal records with stage, value, owner, and replay links.",
    endpoints: [{ label: "deals", path: "/deals", heading: "Deal Library" }],
    titleFields: ["account_name", "name", "id"],
    metaFields: ["stage", "owner_name", "status"],
    detailFields: ["amount_usd", "close_date"]
  },
  accounts: {
    title: "Accounts",
    eyebrow: "accounts",
    summary: "Account book backed by provider-shaped account records.",
    endpoints: [{ label: "accounts", path: "/accounts", heading: "Account Library" }],
    titleFields: ["name", "domain", "id"],
    metaFields: ["segment", "health", "owner_user_id"],
    detailFields: ["renewal_date", "domain"]
  },
  calls: {
    title: "Calls",
    eyebrow: "call library",
    summary: "Call events available for coaching, inspection, and causal evidence.",
    endpoints: [{ label: "calls", path: "/calls", heading: "Recent Calls" }],
    titleFields: ["summary", "title", "call_id", "id"],
    metaFields: ["deal_id", "timestamp", "duration_seconds"],
    detailFields: ["participants", "outcome"]
  },
  forecast: {
    title: "Forecast",
    eyebrow: "forecast",
    summary: "Forecast summary plus submitted forecast records from the authenticated tenant.",
    endpoints: [
      { label: "forecast summary", path: "/forecast/summary", heading: "Forecast Summary" },
      { label: "forecast submissions", path: "/forecast/submissions", heading: "Submissions" }
    ],
    titleFields: ["forecast_category", "period", "id"],
    metaFields: ["submitted_by_user_id", "submitted_at", "weighted_forecast_amount"],
    detailFields: ["commit_amount_usd", "best_case_amount_usd", "pipeline_amount_usd"]
  },
  coaching: {
    title: "Coaching",
    eyebrow: "coaching",
    summary: "Manager scorecards and rep risk rows tied back to calls and deals.",
    endpoints: [
      { label: "coaching scorecards", path: "/coaching/scorecards", heading: "Scorecards" },
      { label: "coaching rep", path: "/coaching/reps/user_maya", heading: "Rep Detail" }
    ],
    titleFields: ["name", "id", "rep_id", "call_id"],
    metaFields: ["overall_score", "reviewed_at", "role_name"],
    detailFields: ["strengths", "improvement_areas", "risk_rows"]
  },
  engage: {
    title: "Engage",
    eyebrow: "engagement",
    summary: "Read-only engagement tasks created from call and deal evidence.",
    endpoints: [{ label: "engagement tasks", path: "/engage/tasks", heading: "Task Queue" }],
    titleFields: ["title", "id"],
    metaFields: ["priority", "status", "owner_user_id"],
    detailFields: ["due_date", "deal_id", "source_call_id"]
  },
  assistant: {
    title: "Assistant",
    eyebrow: "assistant",
    summary: "Citation-backed assistant answer from the local demo tenant.",
    endpoints: [
      {
        label: "assistant query",
        path: "/assistant/query",
        method: "POST",
        body: { question: "why is Northstar risky?" },
        heading: "Cited Answer"
      }
    ],
    titleFields: ["question", "id"],
    metaFields: ["runtime", "created_at"],
    detailFields: ["answer", "citations"]
  },
  admin: {
    title: "Admin",
    eyebrow: "admin",
    summary: "Users, settings, audit events, and export previews without SSO claims.",
    endpoints: [
      { label: "admin users", path: "/admin/users", heading: "Users" },
      { label: "admin settings", path: "/admin/settings", heading: "Settings" },
      { label: "audit events", path: "/audit/events", heading: "Audit Events" },
      { label: "exports", path: "/exports", heading: "Exports" }
    ],
    titleFields: ["name", "key", "action", "export_type", "id"],
    metaFields: ["role_name", "status", "updated_at", "occurred_at"],
    detailFields: ["email", "value", "target_id", "download_url"]
  },
  ingestion: {
    title: "Ingestion",
    eyebrow: "ingestion",
    summary: "Authenticated call records that downstream ingestion jobs write into the evidence spine.",
    endpoints: [{ label: "ingestion calls", path: "/calls", heading: "Call Evidence" }],
    titleFields: ["summary", "call_id", "id"],
    metaFields: ["timestamp", "deal_id", "duration_seconds"],
    detailFields: ["participants", "commitments_made", "objections_raised"]
  }
};

export function routeSpec(route: RevenueRouteKey): RouteSpec {
  return ROUTES[route];
}

export function isRecord(value: unknown): value is RecordMap {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isRecordArray(value: unknown): value is readonly RecordMap[] {
  return Array.isArray(value) && value.every(isRecord);
}

function isListResponse(value: unknown): value is Readonly<{ readonly items: readonly RecordMap[] }> {
  return isRecord(value) && isRecordArray(value["items"]);
}

function sectionItems(value: unknown): readonly RecordMap[] | null {
  if (isListResponse(value)) return value.items;
  if (isRecord(value)) {
    if (isRecord(value["rep"]) && isRecordArray(value["risk_rows"])) return [value["rep"], ...value["risk_rows"]];
    return [value];
  }
  return null;
}

export async function loadRevenueRoute(route: RevenueRouteKey): Promise<RouteData> {
  const config = apiConfig();
  if (config.kind === "setup_required") return config;

  const spec = ROUTES[route];
  const sections: SectionData[] = [];
  for (const endpoint of spec.endpoints) {
    const url = apiUrl(config, endpoint.path);
    if (typeof url !== "string") return url;
    const result = await fetchJson(
      url,
      endpoint.label,
      config,
      endpoint.method === "POST" ? { method: "POST", body: JSON.stringify(endpoint.body ?? {}), contentType: "application/json" } : {}
    );
    if (result.kind === "setup_required") return result;
    const items = sectionItems(result.data);
    if (items === null) {
      return {
        kind: "setup_required",
        message: `Production API did not return valid ${endpoint.label} data.`
      };
    }
    sections.push({ heading: endpoint.heading, items });
  }
  return { kind: "ready", sections };
}
