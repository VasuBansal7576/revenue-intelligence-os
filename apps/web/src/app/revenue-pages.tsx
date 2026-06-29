import Link from "next/link";
import type { ReactNode } from "react";

import { formatDateTime, formatMoney } from "./deals/[id]/format";
import { Badge } from "./deals/[id]/ui";
import { isRecord, loadRevenueRoute, routeSpec, type RecordMap, type RevenueRouteKey, type RouteSpec } from "./revenue-route-data";

function textValue(value: unknown): string {
  if (typeof value === "string") {
    if (/^\d{4}-\d{2}-\d{2}T/.test(value) && !Number.isNaN(Date.parse(value))) return formatDateTime(value);
    return value;
  }
  if (typeof value === "number") {
    if (value >= 1000) return formatMoney(value);
    return String(value);
  }
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (Array.isArray(value)) return `${value.length} records`;
  if (isRecord(value)) return `${Object.keys(value).length} fields`;
  if (value === null) return "None";
  return "";
}

function firstText(record: RecordMap, fields: readonly string[]): string {
  for (const field of fields) {
    const text = textValue(record[field]);
    if (text) return text;
  }
  return "Record";
}

function fieldTexts(record: RecordMap, fields: readonly string[]): readonly string[] {
  return fields.map((field) => textValue(record[field])).filter((value) => value.length > 0);
}

function statusText(record: RecordMap): string | null {
  for (const field of ["status", "health", "priority", "forecast_category"]) {
    const value = record[field];
    if (typeof value === "string") return value;
  }
  return null;
}

function badgeTone(value: string) {
  const normalized = value.toLowerCase();
  if (["healthy", "ready", "done", "active"].includes(normalized)) return "success";
  if (["high", "at_risk", "stalling", "blocked", "failed", "disabled"].includes(normalized)) return "danger";
  if (["medium", "pending", "open", "best_case"].includes(normalized)) return "warning";
  return "info";
}

function detailHref(route: RevenueRouteKey, record: RecordMap): string | null {
  if (route !== "deals") return null;
  const id = record["id"];
  return typeof id === "string" ? `/deals/${encodeURIComponent(id)}` : null;
}

function RecordRow({ route, spec, record }: { readonly route: RevenueRouteKey; readonly spec: RouteSpec; readonly record: RecordMap }) {
  const title = firstText(record, spec.titleFields);
  const meta = fieldTexts(record, spec.metaFields);
  const details = fieldTexts(record, spec.detailFields);
  const status = statusText(record);
  const href = detailHref(route, record);
  const body = (
    <>
      <div className="route-row-head">
        <h3>{title}</h3>
        {status ? <Badge tone={badgeTone(status)}>{status}</Badge> : null}
      </div>
      <div className="route-row-meta">
        {meta.map((item) => (
          <span key={item}>{item}</span>
        ))}
      </div>
      {details.length > 0 ? (
        <div className="route-row-detail">
          {details.map((item) => (
            <code key={item}>{item}</code>
          ))}
        </div>
      ) : null}
    </>
  );
  return href ? (
    <Link className="route-row" href={href}>
      {body}
    </Link>
  ) : (
    <article className="route-row">{body}</article>
  );
}

function SetupRequired({ message }: { readonly message: string }) {
  return (
    <main className="app-shell route-shell">
      <section className="panel setup-panel">
        <div className="panel-header">
          <p>setup</p>
          <h1>Configuration required</h1>
        </div>
        <div className="panel-body">
          <p>{message}</p>
        </div>
      </section>
    </main>
  );
}

function RouteSection({ children, title }: { readonly children: ReactNode; readonly title: string }) {
  return (
    <section className="panel route-panel" aria-labelledby={`${title.toLowerCase().replace(/[^a-z0-9]+/g, "-")}-title`}>
      <div className="panel-header">
        <p>data</p>
        <h2 id={`${title.toLowerCase().replace(/[^a-z0-9]+/g, "-")}-title`}>{title}</h2>
      </div>
      <div className="panel-body">{children}</div>
    </section>
  );
}

export async function RevenueRoutePage({ route }: { readonly route: RevenueRouteKey }) {
  const spec = routeSpec(route);
  const data = await loadRevenueRoute(route);
  if (data.kind === "setup_required") return <SetupRequired message={data.message} />;

  const count = data.sections.reduce((total, section) => total + section.items.length, 0);
  return (
    <main className="app-shell route-shell">
      <header className="route-hero">
        <div>
          <p>{spec.eyebrow}</p>
          <h1>{spec.title}</h1>
          <span>{spec.summary}</span>
        </div>
        <div className="route-hero-meta">
          <Badge tone="production">TENANT AUTH</Badge>
          <strong>{count}</strong>
          <span>records</span>
        </div>
      </header>

      <div className="route-grid">
        {data.sections.map((section) => (
          <RouteSection key={section.heading} title={section.heading}>
            <div className="route-list">
              {section.items.map((item) => (
                <RecordRow key={firstText(item, ["id", "call_id", "question", "key"])} record={item} route={route} spec={spec} />
              ))}
            </div>
          </RouteSection>
        ))}
      </div>
    </main>
  );
}
