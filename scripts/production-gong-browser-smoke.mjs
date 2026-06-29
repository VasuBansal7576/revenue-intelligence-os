import { mkdir, writeFile } from "node:fs/promises";
import { dirname } from "node:path";

const FETCH_TIMEOUT_MS = 5000;

const ROUTES = [
  { path: "/deals", heading: "Deals" },
  { path: "/accounts", heading: "Accounts" },
  { path: "/calls", heading: "Calls" },
  { path: "/forecast", heading: "Forecast" },
  { path: "/coaching", heading: "Coaching" },
  { path: "/engage", heading: "Engage" },
  { path: "/assistant", heading: "Assistant" },
  { path: "/admin", heading: "Admin" },
  { path: "/ingestion", heading: "Ingestion" },
  { path: "/deals/deal_northstar_expansion", heading: "Operator Console" }
];

function usage() {
  return "Usage: node scripts/production-gong-browser-smoke.mjs --base-url <url> --mode demo|setup-required --out <path>";
}

function parseArgs(argv) {
  const args = new Map();
  for (let index = 2; index < argv.length; index += 2) {
    const key = argv[index];
    const value = argv[index + 1];
    if (!key?.startsWith("--") || value === undefined) throw new Error(usage());
    args.set(key.slice(2), value);
  }
  const baseUrl = args.get("base-url");
  const mode = args.get("mode");
  const out = args.get("out");
  if (!baseUrl || !out || (mode !== "demo" && mode !== "setup-required")) throw new Error(usage());
  return { baseUrl, mode, out };
}

function includesHeading(html, heading) {
  return html.includes(`<h1>${heading}</h1>`) || html.includes(`<h2>${heading}</h2>`);
}

async function checkRoute(baseUrl, route, mode) {
  const url = new URL(route.path, baseUrl).toString();
  let status = 0;
  let html = "";
  let error = null;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    const response = await fetch(url, { redirect: "follow", signal: controller.signal });
    status = response.status;
    html = await response.text();
  } catch (caught) {
    error = caught instanceof Error ? caught.message : String(caught);
  } finally {
    clearTimeout(timeout);
  }

  const configurationRequired = html.includes("Configuration required");
  const headingPresent = mode === "demo" ? includesHeading(html, route.heading) : configurationRequired;
  const ok = status === 200 && headingPresent && (mode === "setup-required" || !configurationRequired) && error === null;
  return {
    path: route.path,
    expectedHeading: route.heading,
    status,
    ok,
    headingPresent,
    configurationRequired,
    error
  };
}

async function main() {
  const { baseUrl, mode, out } = parseArgs(process.argv);
  const routes = [];
  for (const route of ROUTES) {
    routes.push(await checkRoute(baseUrl, route, mode));
  }
  const setupRequired = mode === "setup-required" && routes.every((route) => route.status === 200 && route.configurationRequired);
  const ok = routes.every((route) => route.ok) && (mode === "demo" || setupRequired);
  const report = {
    mode,
    baseUrl,
    ok,
    setupRequired,
    routes,
    generatedAt: new Date().toISOString()
  };
  await mkdir(dirname(out), { recursive: true });
  await writeFile(out, `${JSON.stringify(report, null, 2)}\n`);
  if (!ok) {
    console.error(JSON.stringify(report, null, 2));
    process.exitCode = 1;
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});
