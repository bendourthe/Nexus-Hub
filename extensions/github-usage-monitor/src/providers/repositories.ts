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
        // Not cached: a 404 here is often a transient permission condition (a token
        // without repository read access), and caching it would make one bad refresh
        // permanent for the session.
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

/** Distinct repository names across a snapshot's line items. */
export function repositoryNamesIn(breakdowns: readonly { repositoryName: string | null }[]): string[] {
  return [...new Set(breakdowns.map((row) => row.repositoryName).filter((name): name is string => name !== null && name.length > 0))];
}
