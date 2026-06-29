type SetupRequiredData = {
  readonly kind: "setup_required";
  readonly message: string;
};

const FETCH_TIMEOUT_MS = 5000;

export type ApiConfig =
  | {
      readonly kind: "ready";
      readonly apiBaseUrl: string;
      readonly tenantId: string;
      readonly authToken: string;
    }
  | SetupRequiredData;

export type ApiResult =
  | {
      readonly kind: "ok";
      readonly data: unknown;
    }
  | SetupRequiredData;

export function apiConfig(): ApiConfig {
  const apiBaseUrl = process.env.CDI_API_BASE_URL;
  const tenantId = process.env.CDI_TENANT_ID;
  const authToken = process.env.CDI_AUTH_TOKEN;
  if (!apiBaseUrl || !tenantId || !authToken) {
    return {
      kind: "setup_required",
      message: "Set CDI_API_BASE_URL, CDI_TENANT_ID, and CDI_AUTH_TOKEN to load production deal data."
    };
  }
  return { kind: "ready", apiBaseUrl, tenantId, authToken };
}

export function apiUrl(config: Extract<ApiConfig, { readonly kind: "ready" }>, path: string, query?: URLSearchParams): string | SetupRequiredData {
  try {
    const baseUrl = config.apiBaseUrl.endsWith("/") ? config.apiBaseUrl : `${config.apiBaseUrl}/`;
    const url = new URL(path.replace(/^\//, ""), baseUrl);
    url.searchParams.set("tenant_id", config.tenantId);
    query?.forEach((value, key) => url.searchParams.set(key, value));
    return url.toString();
  } catch (error) {
    if (error instanceof TypeError) {
      return {
        kind: "setup_required",
        message: "CDI_API_BASE_URL must be an absolute API URL."
      };
    }
    throw error;
  }
}

export async function fetchJson(
  url: string,
  label: string,
  config: Extract<ApiConfig, { readonly kind: "ready" }>,
  init: Readonly<{ method?: "GET" | "POST"; body?: string; contentType?: string }> = {}
): Promise<ApiResult> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  let response: Response;
  try {
    response = await fetch(url, {
      method: init.method ?? "GET",
      headers: {
        Authorization: `Bearer ${config.authToken}`,
        "X-Tenant-Id": config.tenantId,
        ...(init.contentType ? { "Content-Type": init.contentType } : {})
      },
      body: init.body,
      cache: "no-store",
      signal: controller.signal
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      return {
        kind: "setup_required",
        message: `Production API timed out for ${label}.`
      };
    }
    if (error instanceof TypeError) {
      return {
        kind: "setup_required",
        message: `Production API request failed for ${label}.`
      };
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
  if (!response.ok) {
    return {
      kind: "setup_required",
      message: `Production API returned ${response.status} for ${label}.`
    };
  }
  try {
    return { kind: "ok", data: await response.json() };
  } catch (error) {
    if (error instanceof SyntaxError) {
      return {
        kind: "setup_required",
        message: `Production API returned invalid JSON for ${label}.`
      };
    }
    throw error;
  }
}
