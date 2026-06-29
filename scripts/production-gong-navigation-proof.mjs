// allow: SIZE_OK — self-contained Chrome CDP proof script avoids adding Playwright just for nav evidence.
import { spawn } from "node:child_process";
import { mkdir, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { setTimeout as sleep } from "node:timers/promises";
import { createServer } from "node:net";

const NAV_ITEMS = [
  ["Deals", "/deals"],
  ["Accounts", "/accounts"],
  ["Calls", "/calls"],
  ["Forecast", "/forecast"],
  ["Coaching", "/coaching"],
  ["Engage", "/engage"],
  ["Assistant", "/assistant"],
  ["Admin", "/admin"],
  ["Ingestion", "/ingestion"]
];

const VIEWPORTS = [
  { name: "desktop", width: 1440, height: 1000, mobile: false, deviceScaleFactor: 1 },
  { name: "mobile", width: 390, height: 844, mobile: true, deviceScaleFactor: 2 }
];

const DEFAULT_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

function usage() {
  return "Usage: node scripts/production-gong-navigation-proof.mjs --base-url <url> --out <path> --screenshots-dir <dir>";
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
  const out = args.get("out");
  const screenshotsDir = args.get("screenshots-dir");
  if (!baseUrl || !out || !screenshotsDir) throw new Error(usage());
  return { baseUrl, out, screenshotsDir };
}

async function freePort() {
  return new Promise((resolve, reject) => {
    const server = createServer();
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      server.close(() => resolve(address.port));
    });
  });
}

async function fetchJson(url, init = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 1000);
  try {
    const response = await fetch(url, { ...init, signal: controller.signal });
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
    return await response.json();
  } finally {
    clearTimeout(timeout);
  }
}

async function waitForChrome(port) {
  const versionUrl = `http://127.0.0.1:${port}/json/version`;
  for (let attempt = 0; attempt < 80; attempt += 1) {
    try {
      return await fetchJson(versionUrl);
    } catch {
      await sleep(100);
    }
  }
  throw new Error("Chrome DevTools endpoint did not become ready");
}

async function openPage(port) {
  return fetchJson(`http://127.0.0.1:${port}/json/new?${encodeURIComponent("about:blank")}`, { method: "PUT" });
}

function connectCdp(webSocketDebuggerUrl) {
  const socket = new WebSocket(webSocketDebuggerUrl);
  const pending = new Map();
  const events = new Map();
  let nextId = 1;

  const opened = new Promise((resolve, reject) => {
    socket.addEventListener("open", resolve, { once: true });
    socket.addEventListener("error", reject, { once: true });
  });

  socket.addEventListener("message", (event) => {
    const message = JSON.parse(String(event.data));
    if (message.id && pending.has(message.id)) {
      const { resolve, reject, timeout } = pending.get(message.id);
      clearTimeout(timeout);
      pending.delete(message.id);
      if (message.error) reject(new Error(message.error.message));
      else resolve(message.result ?? {});
      return;
    }
    if (message.method && events.has(message.method)) {
      for (const listener of events.get(message.method)) listener(message.params ?? {});
    }
  });

  function send(method, params = {}) {
    const id = nextId;
    nextId += 1;
    socket.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        pending.delete(id);
        reject(new Error(`CDP timeout: ${method}`));
      }, 5000);
      pending.set(id, { resolve, reject, timeout });
    });
  }

  function on(method, listener) {
    if (!events.has(method)) events.set(method, new Set());
    events.get(method).add(listener);
    return () => events.get(method).delete(listener);
  }

  async function close() {
    for (const { reject, timeout } of pending.values()) {
      clearTimeout(timeout);
      reject(new Error("CDP socket closed"));
    }
    pending.clear();
    socket.close();
  }

  return { opened, send, on, close };
}

async function evaluate(page, expression) {
  const result = await page.send("Runtime.evaluate", {
    expression,
    awaitPromise: true,
    returnByValue: true
  });
  if (result.exceptionDetails) throw new Error(`Evaluation failed: ${expression}`);
  return result.result?.value;
}

async function waitForPath(page, path) {
  for (let attempt = 0; attempt < 80; attempt += 1) {
    const state = await evaluate(
      page,
      `(() => ({
        pathname: location.pathname,
        headings: Array.from(document.querySelectorAll("h1,h2")).map((node) => node.textContent.trim()).filter(Boolean),
        configurationRequired: (document.body?.innerText ?? "").includes("Configuration required")
      }))()`
    );
    if (state.pathname === path && state.headings.length > 0) return state;
    await sleep(100);
  }
  return evaluate(page, `(() => ({ pathname: location.pathname, headings: [], configurationRequired: (document.body?.innerText ?? "").includes("Configuration required") }))()`);
}

async function capture(page, path) {
  const screenshot = await page.send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
  await writeFile(path, Buffer.from(screenshot.data, "base64"));
}

async function visibleLinks(page) {
  return evaluate(
    page,
    `(() => Array.from(document.querySelectorAll('nav[aria-label="Primary"] a')).map((link) => {
      const rect = link.getBoundingClientRect();
      const style = getComputedStyle(link);
      return {
        label: link.textContent.trim(),
        href: link.getAttribute("href"),
        visible: rect.width > 0 && rect.height > 0 && rect.bottom > 0 && rect.right > 0 && rect.top < innerHeight && rect.left < innerWidth && style.display !== "none" && style.visibility !== "hidden",
        rect: { x: Math.round(rect.x), y: Math.round(rect.y), width: Math.round(rect.width), height: Math.round(rect.height) }
      };
    }))()`
  );
}

async function linkTarget(page, label) {
  return evaluate(
    page,
    `(() => {
      const link = Array.from(document.querySelectorAll('nav[aria-label="Primary"] a')).find((candidate) => candidate.textContent.trim() === ${JSON.stringify(label)});
      if (!link) return null;
      const rect = link.getBoundingClientRect();
      const style = getComputedStyle(link);
      return {
        href: link.getAttribute("href"),
        visible: rect.width > 0 && rect.height > 0 && rect.bottom > 0 && rect.right > 0 && rect.top < innerHeight && rect.left < innerWidth && style.display !== "none" && style.visibility !== "hidden",
        x: Math.round(rect.left + rect.width / 2),
        y: Math.round(rect.top + rect.height / 2)
      };
    })()`
  );
}

async function click(page, point, mobile) {
  if (mobile) {
    await page.send("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: [{ x: point.x, y: point.y }] });
    await page.send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
    return;
  }
  await page.send("Input.dispatchMouseEvent", { type: "mouseMoved", x: point.x, y: point.y, button: "none" });
  await page.send("Input.dispatchMouseEvent", { type: "mousePressed", x: point.x, y: point.y, button: "left", clickCount: 1 });
  await page.send("Input.dispatchMouseEvent", { type: "mouseReleased", x: point.x, y: point.y, button: "left", clickCount: 1 });
}

async function runViewport(page, baseUrl, screenshotsDir, viewport) {
  await page.send("Emulation.setDeviceMetricsOverride", {
    width: viewport.width,
    height: viewport.height,
    mobile: viewport.mobile,
    deviceScaleFactor: viewport.deviceScaleFactor
  });
  await page.send("Emulation.setTouchEmulationEnabled", { enabled: viewport.mobile });
  await page.send("Page.navigate", { url: new URL("/deals", baseUrl).toString() });
  const startState = await waitForPath(page, "/deals");
  const startScreenshot = join(screenshotsDir, `nav-${viewport.name}-start.png`);
  await capture(page, startScreenshot);
  const links = await visibleLinks(page);
  const clicks = [];

  for (const [label, path] of NAV_ITEMS) {
    const target = await linkTarget(page, label);
    if (!target?.visible) {
      clicks.push({ label, path, clicked: false, arrived: false, visible: false, href: target?.href ?? null });
      continue;
    }
    await click(page, target, viewport.mobile);
    const state = await waitForPath(page, path);
    clicks.push({
      label,
      path,
      clicked: true,
      arrived: state.pathname === path,
      visible: target.visible,
      href: target.href,
      headings: state.headings,
      configurationRequired: state.configurationRequired
    });
  }

  const finalScreenshot = join(screenshotsDir, `nav-${viewport.name}-final.png`);
  await capture(page, finalScreenshot);
  return {
    viewport,
    startState,
    navLinks: links,
    clicks,
    screenshots: [startScreenshot, finalScreenshot],
    ok:
      links.length === NAV_ITEMS.length &&
      links.every((link) => link.visible) &&
      clicks.every((item) => item.clicked && item.arrived && item.visible && item.configurationRequired === false)
  };
}

async function main() {
  const { baseUrl, out, screenshotsDir } = parseArgs(process.argv);
  const chrome = process.env.CHROME_BIN ?? DEFAULT_CHROME;
  const userDataDir = join(tmpdir(), `production-gong-chrome-${process.pid}`);
  const port = await freePort();
  await mkdir(dirname(out), { recursive: true });
  await mkdir(screenshotsDir, { recursive: true });

  const chromeProcess = spawn(chrome, [
    "--headless=new",
    "--disable-gpu",
    "--no-first-run",
    "--no-default-browser-check",
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${userDataDir}`,
    "about:blank"
  ]);

  let page;
  try {
    const version = await waitForChrome(port);
    const target = await openPage(port);
    page = connectCdp(target.webSocketDebuggerUrl);
    await page.opened;
    await page.send("Page.enable");
    await page.send("Runtime.enable");
    await page.send("DOM.enable");

    const viewports = [];
    for (const viewport of VIEWPORTS) {
      viewports.push(await runViewport(page, baseUrl, screenshotsDir, viewport));
    }

    const report = {
      ok: viewports.every((viewport) => viewport.ok),
      baseUrl,
      chrome,
      chromeVersion: version.Browser,
      generatedAt: new Date().toISOString(),
      expectedNavigation: NAV_ITEMS.map(([label, path]) => ({ label, path })),
      viewports
    };
    await writeFile(out, `${JSON.stringify(report, null, 2)}\n`);
    if (!report.ok) {
      console.error(JSON.stringify(report, null, 2));
      process.exitCode = 1;
    }
  } finally {
    await page?.close().catch(() => {});
    chromeProcess.kill("SIGTERM");
    await sleep(200);
    await rm(userDataDir, { recursive: true, force: true });
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});
