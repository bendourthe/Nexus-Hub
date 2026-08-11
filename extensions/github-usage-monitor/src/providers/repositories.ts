/**
 * Repository visibility and account plan lookups.
 *
 * These two facts are what make an honest percentage possible, and neither is
 * carried by the billing endpoints:
 *
 *   - **Visibility** separates free public-repository usage from the private usage
 *     that actually draws down the allowance. Without it, gross consumption is the
 *     only available numerator, and gross overstated the truth roughly tenfold on
 *     the account this was measured against.
 *   - **Plan name** is the only automatic route to a denominator, since no endpoint
 *     serves an entitlement.
 *
 * PRIVACY. Only two fields are read from a repository: its name and whether it is
 * private. No file content, no commits, no issues. The lookup exists to answer one
 * boolean question per repository and nothing else.
 */

import type { RepositoryVisibility, VisibilityMap } from "./drawdown";

export interface RepositoryFetchOptions {
  token: string;
  owner: string;
  signal?: AbortSignal;
}

export type JsonFetch = (
  path: string,
  token: string,
  signal?: AbortSignal
) => Promise<{ ok: true; value: unknown } | { ok: false; status: number }>;

/**
 * Caches visibility for the session.
 *
 * A repository's visibility rarely changes and a month's usage typically touches a
 * handful of repositories, so caching turns an N-request fan-out into an N-once
 * cost. The bound below is the guard against the pathological account: without it,
 * a month touching hundreds of repositories would issue hundreds of requests on
 * every refresh and could exhaust the rate limit for everything else the user does.
 */
export class RepositoryVisibilityCache {
  private readonly cache = new Map<string, RepositoryVisibility>();

  public constructor(
    private readonly fetchJson: JsonFetch,
    /**
     * Maximum lookups per resolve pass. Exceeding it leaves the remainder unresolved
     * rather than failing: an unresolved repository is excluded from the drawdown,
     * which understates, and an understated bar is the safe direction.
     */
    private readonly maxLookupsPerPass = 50
  ) {}

  public get(repositoryName: string): RepositoryVisibility | undefined {
    return this.cache.get(repositoryName);
  }

  public snapshot(): VisibilityMap {
    return Object.fromEntries(this.cache);
  }

  /** Resolves every name not already cached, up to the per-pass bound. */
  public async resolve(names: readonly string[], options: RepositoryFetchOptions): Promise<VisibilityMap> {
    const pending = [...new Set(names)].filter((name) => !this.cache.has(name));
    for (const name of pending.slice(0, this.maxLookupsPerPass)) {
      const slug = name.includes("/") ? name : `${options.owner}/${name}`;
      const result = await this.fetchJson(`/repos/${slug}`, options.token, options.signal);
      if (!result.ok) {
        // A 404 identifies a PRIVATE repository, and this is the whole reason the
        // extension needs no `repo` scope. This endpoint answers for any public
        // repository without special permission; it returns 404 - not 403 - for a
        // private one the credential cannot see. Every repository appearing in this
        // owner's billing belongs to this owner, so "billed to me but invisible to
        // an unprivileged read" means private.
        //
        // A deleted or renamed repository also 404s and would be counted as private,
        // which slightly OVERSTATES the drawdown. That is the safe direction for a
        // usage monitor: warning early beats missing a limit. Any other status is
        // left unresolved rather than guessed, and an unresolved repository still
        // withholds the percentage entirely.
        if (result.status === 404) this.cache.set(name, "private");
        continue;
      }
      const record = result.value as { private?: unknown } | null;
      this.cache.set(name, record?.private === true ? "private" : "public");
    }
    return this.snapshot();
  }
}

/**
 * Reads `plan.name` from `GET /user`.
 *
 * This is the whole of the automatic denominator path. The response's `plan` object
 * carries only `name`, `space`, `private_repos`, and `collaborators` - no usage
 * entitlement of any kind - so the name is matched against GitHub's published
 * per-plan table rather than read as a number.
 */
export async function fetchAccountPlanName(
  fetchJson: JsonFetch,
  token: string,
  signal?: AbortSignal
): Promise<string | null> {
  const result = await fetchJson("/user", token, signal);
  if (!result.ok) return null;
  const record = result.value as { plan?: { name?: unknown } } | null;
  return typeof record?.plan?.name === "string" ? record.plan.name : null;
}

/**
 * The endpoint whose `plan.name` describes the OWNER being billed.
 *
 * `GET /user` describes the signed-in person, which is the wrong subject whenever
 * the billing owner is an organization. Observed 2026-08-11 against SupiraMedical:
 * the panel reported the organization's usage while the denominator was being
 * sought from a personal GitHub Free plan. It failed visibly rather than silently
 * only by accident - `GET /user` omits the `plan` object entirely unless the token
 * carries the `user` scope, and binding for organization billing swaps `user` for
 * `repo`. So the plan vanished, every denominator went unknown, and the panel said
 * "No allowance is known" for two metrics whose figures the plan table already had.
 *
 * Both failures have the same fix: ask about the owner, not about the reader.
 */
export function planPathFor(owner: { scope: string; name: string }): string | null {
  if (owner.scope === "user") return "/user";
  if (owner.scope === "organization") return `/orgs/${encodeURIComponent(owner.name)}`;
  // No enterprise endpoint serves a plan name. Null rather than a guess: an
  // unrecognized plan yields no denominator, which is the honest outcome.
  return null;
}

/**
 * `plan.name` for the owner actually being billed.
 *
 * `GET /orgs/{org}` returns its `plan` object only to an organization owner, and
 * returns the organization's own plan (`team`, `enterprise`, `free`) rather than the
 * caller's. A member who cannot see it gets null, which reads through to "no
 * allowance established" - correct, because that member genuinely cannot verify one.
 */
export async function fetchOwnerPlanName(
  fetchJson: JsonFetch,
  token: string,
  owner: { scope: string; name: string },
  signal?: AbortSignal
): Promise<string | null> {
  const path = planPathFor(owner);
  if (path === null) return null;
  const result = await fetchJson(path, token, signal);
  if (!result.ok) return null;
  const record = result.value as { plan?: { name?: unknown } } | null;
  return typeof record?.plan?.name === "string" ? record.plan.name : null;
}

/** What the organization's Copilot subscription says about seats and plan. */
export interface CopilotSubscription {
  planType: "business" | "enterprise";
  /** Assigned Copilot licenses, which is what the credit pool is multiplied by. */
  seats: number;
}

/**
 * Reads the organization's Copilot subscription from `GET /orgs/{org}/copilot/billing`.
 *
 * `seat_breakdown.total` is the assigned-licence count, which is the multiplier
 * GitHub bills against. Deliberately NOT the Team subscription's seat count: the
 * organization measured on 2026-08-11 had 9 Team licences but 7 billable Copilot
 * licences, and only 7 reproduces the 21,000 credits its own billing page shows.
 *
 * Null on every failure - no Copilot subscription (404), a caller who is not an
 * organization owner (403), an unrecognized plan type, or a missing seat count.
 * A composed denominator with a guessed term is worse than no denominator.
 */
export async function fetchCopilotSubscription(
  fetchJson: JsonFetch,
  token: string,
  owner: { scope: string; name: string },
  signal?: AbortSignal
): Promise<CopilotSubscription | null> {
  if (owner.scope !== "organization") return null;
  const result = await fetchJson(`/orgs/${encodeURIComponent(owner.name)}/copilot/billing`, token, signal);
  if (!result.ok) return null;
  const record = (typeof result.value === "object" && result.value !== null ? result.value : {}) as {
    plan_type?: unknown;
    seat_breakdown?: { total?: unknown } | null;
  };
  const planType = typeof record.plan_type === "string" ? record.plan_type.trim().toLowerCase() : "";
  if (planType !== "business" && planType !== "enterprise") return null;
  const seats = record.seat_breakdown?.total;
  if (typeof seats !== "number" || !Number.isInteger(seats) || seats <= 0) return null;
  return { planType, seats };
}

/**
 * Distinct repository names across a snapshot's line items.
 *
 * Tests `typeof` rather than `!== null`. A breakdown written by extension 0.1.0
 * carries no `repositoryName` at all, and `undefined` passes a null check before
 * throwing on `.length` - the same absence-tolerance class as the v3.16.3 BG-3
 * crash. Cached state outlives the version that wrote it.
 */
export function repositoryNamesIn(breakdowns: readonly { repositoryName?: string | null }[]): string[] {
  return [...new Set(breakdowns.map((row) => row.repositoryName).filter((name): name is string => typeof name === "string" && name.length > 0))];
}
