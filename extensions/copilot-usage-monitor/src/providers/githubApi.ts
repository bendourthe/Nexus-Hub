/**
 * The only network seam in the extension. Every request goes to
 * https://api.github.com and nowhere else: URLs are built here from fixed paths,
 * the origin is checked before a request leaves, and redirects are refused so an
 * Authorization header can never follow one to another host.
 */
export const GITHUB_API_ORIGIN = "https://api.github.com";
const REQUEST_TIMEOUT_MS = 30_000;
const USER_AGENT = "nexus-hub-copilot-usage-monitor";

export type FetchLike = (input: string, init: RequestInit) => Promise<Response>;

export type GitHubResponse =
  | { kind: "response"; status: number; statusText: string; rateLimited: boolean; body: unknown; parsed: boolean }
  | { kind: "network-error" };

/** Build an api.github.com URL from a fixed path and optional query. */
export function githubApiUrl(pathname: string, query: Record<string, string> = {}): URL {
  const url = new URL(pathname, GITHUB_API_ORIGIN);
  for (const [key, value] of Object.entries(query)) {
    url.searchParams.set(key, value);
  }
  return url;
}

/**
 * GET a GitHub API URL with the given Authorization value. The value is only
 * placed in the request header; it is not logged, stored, or returned.
 */
export async function githubGet(
  url: URL,
  authorization: string,
  extraHeaders: Record<string, string>,
  fetchImpl: FetchLike,
): Promise<GitHubResponse> {
  if (url.origin !== GITHUB_API_ORIGIN) {
    return { kind: "network-error" };
  }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  let response: Response;
  try {
    response = await fetchImpl(url.toString(), {
      method: "GET",
      headers: { Authorization: authorization, "User-Agent": USER_AGENT, ...extraHeaders },
      redirect: "error",
      signal: controller.signal,
    });
  } catch {
    return { kind: "network-error" };
  } finally {
    clearTimeout(timer);
  }
  // GitHub signals a primary rate limit with 403 and x-ratelimit-remaining: 0.
  const rateLimited =
    response.status === 429 ||
    (response.status === 403 && response.headers?.get?.("x-ratelimit-remaining") === "0");
  let body: unknown = undefined;
  let parsed = false;
  if (response.ok) {
    try {
      body = await response.json();
      parsed = true;
    } catch {
      parsed = false;
    }
  }
  return { kind: "response", status: response.status, statusText: response.statusText, rateLimited, body, parsed };
}
