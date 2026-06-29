import type {
  DealBriefing,
  DealContext,
  DealTimelineResponse
} from "@causal-deal/types";
import { apiConfig, apiUrl, fetchJson } from "../../api";
import { isDealBriefing, isDealContext, isTimeline } from "./api-contracts";

type ReadyDealWorkbenchData = {
  readonly kind: "ready";
  readonly contexts: readonly DealContext[];
  readonly selectedContext: DealContext;
  readonly timeline: DealTimelineResponse;
  readonly briefing: DealBriefing;
};

type SetupRequiredData = {
  readonly kind: "setup_required";
  readonly message: string;
};

export type DealWorkbenchData = ReadyDealWorkbenchData | SetupRequiredData;

function isIsoDateTime(value: string): boolean {
  return /^\d{4}-\d{2}-\d{2}T/.test(value) && !Number.isNaN(Date.parse(value));
}

export async function loadDealWorkbench(selectedDealId: string, asOf?: string): Promise<DealWorkbenchData> {
  if (asOf && !isIsoDateTime(asOf)) {
    return {
      kind: "setup_required",
      message: "Invalid as_of query parameter; use an ISO timestamp."
    };
  }

  const config = apiConfig();
  if (config.kind === "setup_required") return config;

  const dealPathId = encodeURIComponent(selectedDealId);
  const contextUrl = apiUrl(config, `/deals/${dealPathId}/context`);
  const timelineUrl = apiUrl(config, `/deals/${dealPathId}/timeline`, asOf ? new URLSearchParams([["as_of", asOf]]) : undefined);
  const briefingUrl = apiUrl(config, `/intelligence/deal/${dealPathId}`);
  if (typeof contextUrl !== "string") return contextUrl;
  if (typeof timelineUrl !== "string") return timelineUrl;
  if (typeof briefingUrl !== "string") return briefingUrl;

  const [context, timeline, briefing] = await Promise.all([
    fetchJson(contextUrl, "deal context", config),
    fetchJson(timelineUrl, "deal timeline", config),
    fetchJson(briefingUrl, "deal intelligence", config)
  ]);

  if (context.kind === "setup_required") return context;
  if (timeline.kind === "setup_required") return timeline;
  if (briefing.kind === "setup_required") return briefing;

  if (!isDealContext(context.data) || !isTimeline(timeline.data) || !isDealBriefing(briefing.data)) {
    return {
      kind: "setup_required",
      message: "Production API did not return valid deal workbench data."
    };
  }

  return {
    kind: "ready",
    contexts: [context.data],
    selectedContext: context.data,
    timeline: timeline.data,
    briefing: briefing.data
  };
}
