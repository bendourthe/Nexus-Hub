import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import type * as vscode from "vscode";
import { afterEach, describe, expect, it } from "vitest";
import { __resetLog } from "../src/log";
import { CopilotUsageProvider, fetchSeatOrganizations, mapSeatOrganizations } from "../src/providers/copilot";
import { NOT_CONNECTED_HINT, NO_PERSONAL_QUOTA_HINT, getRecommendation, noPercentHint } from "../src/recommendations";
import { headlineOf } from "../src/types";
import {
  CONNECT_CHOICE,
  CopilotOrganizationProvider,
  NO_SEAT_ORGANIZATION,
  OPEN_GITHUB,
  ORG_READ_SCOPES,
  ORG_ROUTE_SECRET_KEY,
  ORG_TOKEN_SECRET_KEY,
  OTHER_ORGANIZATION,
  TOKEN_FIX_MESSAGE,
  TOKEN_PROMPT,
  chooseOrganization,
  connectOrganization,
  disconnectMessage,
  disconnectOrganization,
  organizationRoute,
  tokenCreationUrl,
} from "../src/providers/copilotOrganization";
import { StatusBarManager } from "../src/statusBarManager";
import { UsageController } from "../src/usageController";
import { UsageService } from "../src/usageService";
import { UsageStore } from "../src/usageStore";
import { FakeSecretStorage, ORG_TOKEN, WORK_TOKEN, createMemento, fixture, jsonResponse, routedFetch } from "./helpers";
import {
  __resetStubState,
  __setStubConfig,
  configurationUpdates,
  createdStatusBarItems,
  inputBoxAnswers,
  inputBoxCalls,
  messageAnswers,
  messageOptions,
  openedExternal,
  outputLines,
  quickPickAnswers,
  quickPickCalls,
  shownMessages,
} from "./vscode-stub";

/**
 * v4.13.8 Phase 6 (T337-T339, T341): Connect finds the organization from the
 * seat, tries the token-free `read:org` route first, and falls back to a guided
 * read-only token. No write scope is ever requested.
 */
const OCT_2 = Date.UTC(2026, 9, 2, 0, 5);
const ORG = "acme-co";
const SEAT_ORG = "example-org";

/** An auth stub that answers silent and interactive requests per scope set. */
function scopedAuth(sessions: { seat?: string; readOrg?: string }) {
  const calls: Array<{ scopes: string[]; options: Record<string, unknown> }> = [];
  const auth = {
    calls,
    async getSession(_provider: string, scopes: readonly string[], options: Record<string, unknown> = {}) {
      calls.push({ scopes: [...scopes], options: { ...options } });
      const token = scopes.includes("read:org") ? sessions.readOrg : sessions.seat;
      return token ? ({ id: "s", accessToken: token, account: { id: "a", label: "example-user" }, scopes } as vscode.AuthenticationSession) : undefined;
    },
  };
  return auth;
}

/** A fetch where the seat lists `orgs`, and each org endpoint answers per credential. */
function orgFetch(statusFor: (authorization: string | undefined) => number, seat = "copilot-internal-user.business-member.json") {
  return routedFetch((url, authorization) => {
    if (url.pathname === "/copilot_internal/user") {
      return jsonResponse(fixture(seat));
    }
    const status = statusFor(authorization);
    if (status !== 200) {
      return jsonResponse({ message: "nope" }, status);
    }
    return jsonResponse(fixture(url.pathname.endsWith("/copilot/billing") ? "copilot-billing.json" : "ai-credit-usage.json"));
  });
}

afterEach(() => {
  __resetStubState();
  __resetLog();
});

describe("organization auto-detection (T337)", () => {
  it("reads only valid logins from the seat's organization_list, without ids", () => {
    expect(mapSeatOrganizations(fixture("copilot-internal-user.business-member.json"))).toEqual([{ login: SEAT_ORG, name: SEAT_ORG }]);
    expect(mapSeatOrganizations(fixture("copilot-internal-user.personal.json"))).toEqual([]);
    expect(
      mapSeatOrganizations({
        organization_list: [
          { id: 1, login: "acme-co", name: "Acme Inc" },
          { id: 2, login: "ACME-CO", name: "duplicate" },
          { id: 3, login: "bad org" },
          { id: 4, login: "-leading" },
          { id: 5 },
          "acme",
        ],
      }),
    ).toEqual([{ login: "acme-co", name: "Acme Inc" }]);
    expect(mapSeatOrganizations(null)).toEqual([]);
  });

  it("fetches the list silently with the signed-in session, and returns [] on any failure", async () => {
    const auth = scopedAuth({ seat: WORK_TOKEN });
    const fake = orgFetch(() => 200);
    expect(await fetchSeatOrganizations(auth, fake.fetch)).toEqual([{ login: SEAT_ORG, name: SEAT_ORG }]);
    expect(auth.calls[0].options).toEqual({ createIfNone: false, silent: true });
    expect(await fetchSeatOrganizations(scopedAuth({}), fake.fetch)).toEqual([]);
    const failing = routedFetch(() => jsonResponse({}, 500));
    expect(await fetchSeatOrganizations(auth, failing.fetch)).toEqual([]);
  });

  it("one organization: preselects it and asks to confirm", async () => {
    messageAnswers.push(CONNECT_CHOICE);
    expect(await chooseOrganization([{ login: ORG, name: "Acme Inc" }])).toBe(ORG);
    expect(shownMessages[0].message).toContain("Connect Acme Inc (acme-co)?");
    expect(messageOptions[0]).toMatchObject({ modal: true });
    expect(inputBoxCalls).toHaveLength(0);
  });

  it("one organization: Other organization falls back to typing, and dismissing cancels", async () => {
    messageAnswers.push(OTHER_ORGANIZATION);
    inputBoxAnswers.push(" other-org ");
    expect(await chooseOrganization([{ login: ORG, name: ORG }])).toBe("other-org");
    messageAnswers.push(undefined);
    expect(await chooseOrganization([{ login: ORG, name: ORG }])).toBeUndefined();
  });

  it("several organizations: a quick pick of name (login), plus Other organization", async () => {
    const orgs = [
      { login: ORG, name: "Acme Inc" },
      { login: "beta", name: "beta" },
    ];
    quickPickAnswers.push(1);
    expect(await chooseOrganization(orgs)).toBe("beta");
    const labels = (quickPickCalls[0].items as Array<{ label: string }>).map((i) => i.label);
    expect(labels).toEqual(["Acme Inc (acme-co)", "beta", OTHER_ORGANIZATION]);
    quickPickAnswers.push(2);
    inputBoxAnswers.push("gamma");
    expect(await chooseOrganization(orgs)).toBe("gamma");
    quickPickAnswers.push(undefined);
    expect(await chooseOrganization(orgs)).toBeUndefined();
  });

  it("no organization: typed entry with a one-line explanation and login validation", async () => {
    inputBoxAnswers.push(ORG);
    expect(await chooseOrganization([])).toBe(ORG);
    expect(String(inputBoxCalls[0].prompt)).toContain(NO_SEAT_ORGANIZATION.trim());
    const validate = inputBoxCalls[0].validateInput as (v: string) => string | undefined;
    expect(validate("acme-co")).toBeUndefined();
    expect(validate("bad org")).toContain("organization login");
  });
});

describe("route selection (T338)", () => {
  it("token-free: read:org 200/200 connects with no token stored, and refreshes reuse the session silently", async () => {
    const secrets = new FakeSecretStorage();
    const auth = scopedAuth({ seat: WORK_TOKEN, readOrg: WORK_TOKEN });
    const fake = orgFetch((a) => (a === `Bearer ${WORK_TOKEN}` ? 200 : 403));
    messageAnswers.push(CONNECT_CHOICE);
    expect(await connectOrganization(secrets.asSecretStorage(), fake.fetch, auth, OCT_2)).toBe("connected");

    expect(secrets.stored).toEqual([{ key: ORG_ROUTE_SECRET_KEY, value: "vscode-session" }]);
    expect(secrets.values.has(ORG_TOKEN_SECRET_KEY)).toBe(false);
    expect(configurationUpdates).toEqual([{ section: "copilotUsage", key: "organization", value: SEAT_ORG, target: 1 }]);
    expect(auth.calls.find((c) => c.scopes.includes("read:org"))?.options).toEqual({ createIfNone: true });
    expect(outputLines.join("\n")).toContain("token-free route, copilot/billing 200, ai_credit/usage 200");
    expect(openedExternal).toEqual([]);
    expect(await organizationRoute(secrets.asSecretStorage())).toBe("vscode-session");

    __setStubConfig("copilotUsage", "organization", SEAT_ORG);
    const result = await new CopilotOrganizationProvider(secrets.asSecretStorage(), fake.fetch, auth).fetchUsage(OCT_2);
    expect(result.success).toBe(true);
    expect(auth.calls.at(-1)).toEqual({ scopes: [...ORG_READ_SCOPES], options: { createIfNone: false, silent: true } });
  });

  it("403 on the token-free route falls back to the guided token, logging each status code", async () => {
    const secrets = new FakeSecretStorage();
    const auth = scopedAuth({ seat: WORK_TOKEN, readOrg: WORK_TOKEN });
    const fake = orgFetch((a) => (a === `Bearer ${ORG_TOKEN}` ? 200 : 403));
    messageAnswers.push(CONNECT_CHOICE, OPEN_GITHUB);
    inputBoxAnswers.push(` ${ORG_TOKEN} `);
    expect(await connectOrganization(secrets.asSecretStorage(), fake.fetch, auth, OCT_2)).toBe("connected");

    const logs = outputLines.join("\n");
    expect(logs).toContain("token-free route, copilot/billing 403, ai_credit/usage 403");
    expect(logs).toContain("token route, copilot/billing 200, ai_credit/usage 200");
    expect(openedExternal).toEqual([tokenCreationUrl(SEAT_ORG)]);
    expect(secrets.stored).toEqual([{ key: ORG_TOKEN_SECRET_KEY, value: ORG_TOKEN }]);
    expect(secrets.values.has(ORG_ROUTE_SECRET_KEY)).toBe(false);
    expect(await organizationRoute(secrets.asSecretStorage())).toBe("token");
    // Both endpoints were checked with the pasted token.
    const tokenCalls = fake.calls.filter((c) => c.authorization === `Bearer ${ORG_TOKEN}`).map((c) => new URL(c.url).pathname);
    expect(tokenCalls).toEqual([`/orgs/${SEAT_ORG}/copilot/billing`, `/organizations/${SEAT_ORG}/settings/billing/ai_credit/usage`]);
  });

  it.each([401, 404])("%i on the token-free route also falls back to the guided token", async (status) => {
    const secrets = new FakeSecretStorage();
    const auth = scopedAuth({ seat: WORK_TOKEN, readOrg: WORK_TOKEN });
    const fake = orgFetch((a) => (a === `Bearer ${ORG_TOKEN}` ? 200 : status));
    messageAnswers.push(CONNECT_CHOICE, OPEN_GITHUB);
    inputBoxAnswers.push(ORG_TOKEN);
    expect(await connectOrganization(secrets.asSecretStorage(), fake.fetch, auth, OCT_2)).toBe("connected");
    expect(outputLines.join("\n")).toContain(`token-free route, copilot/billing ${status}`);
    expect(secrets.stored).toEqual([{ key: ORG_TOKEN_SECRET_KEY, value: ORG_TOKEN }]);
  });

  it.each([429, 500, 503])("%i on the token-free route stops without pushing the owner to a token", async (status) => {
    const secrets = new FakeSecretStorage();
    const auth = scopedAuth({ seat: WORK_TOKEN, readOrg: WORK_TOKEN });
    messageAnswers.push(CONNECT_CHOICE, OPEN_GITHUB);
    const fake = orgFetch(() => status);
    expect(await connectOrganization(secrets.asSecretStorage(), fake.fetch, auth, OCT_2)).toBe("unreachable");
    expect(openedExternal).toEqual([]);
    expect(inputBoxCalls).toHaveLength(0);
    expect(secrets.stored).toEqual([]);
    expect(shownMessages.at(-1)?.message).toContain("could not answer right now");
  });

  it("a declined consent prompt is not an error: it offers the narrower guided token instead", async () => {
    const secrets = new FakeSecretStorage();
    const fake = orgFetch((a) => (a === `Bearer ${ORG_TOKEN}` ? 200 : 403));
    messageAnswers.push(CONNECT_CHOICE, OPEN_GITHUB);
    inputBoxAnswers.push(ORG_TOKEN);
    expect(await connectOrganization(secrets.asSecretStorage(), fake.fetch, scopedAuth({ seat: WORK_TOKEN }), OCT_2)).toBe("connected");
    expect(outputLines.join("\n")).toContain("consent prompt was declined");
    expect(shownMessages.filter((m) => m.level === "error")).toEqual([]);
    // The declined session was never sent: every organization call carries the pasted token.
    const orgCalls = fake.calls.filter((c) => !c.url.endsWith("/copilot_internal/user"));
    expect(orgCalls.length).toBe(2);
    expect(orgCalls.every((c) => c.authorization === `Bearer ${ORG_TOKEN}`)).toBe(true);
    expect(secrets.stored).toEqual([{ key: ORG_TOKEN_SECRET_KEY, value: ORG_TOKEN }]);
  });

  it("never requests a write scope", async () => {
    const auth = scopedAuth({ seat: WORK_TOKEN, readOrg: WORK_TOKEN });
    messageAnswers.push(CONNECT_CHOICE, OPEN_GITHUB);
    inputBoxAnswers.push(ORG_TOKEN);
    await connectOrganization(new FakeSecretStorage().asSecretStorage(), orgFetch(() => 403).fetch, auth, OCT_2);
    const scopes = auth.calls.flatMap((c) => c.scopes);
    expect(scopes).toContain("read:org");
    for (const write of ["manage_billing:copilot", "admin:org", "write:org"]) {
      expect(scopes).not.toContain(write);
    }
  });

  it("a network failure on the token-free route stops, without asking for a token", async () => {
    const auth = scopedAuth({ seat: WORK_TOKEN, readOrg: WORK_TOKEN });
    const fake = routedFetch((url) => (url.pathname === "/copilot_internal/user" ? jsonResponse(fixture("copilot-internal-user.business-member.json")) : "throw"));
    messageAnswers.push(CONNECT_CHOICE);
    const secrets = new FakeSecretStorage();
    expect(await connectOrganization(secrets.asSecretStorage(), fake.fetch, auth, OCT_2)).toBe("unreachable");
    expect(inputBoxCalls).toHaveLength(0);
    expect(secrets.stored).toEqual([]);
  });
});

describe("guided read-only token (T339)", () => {
  /** A personal seat (no organization listed), whose read:org session the organization refuses. */
  const refusedSession = () => scopedAuth({ readOrg: WORK_TOKEN });
  const sessionRefused = (status: number) => (a: string | undefined) => (a === `Bearer ${WORK_TOKEN}` ? 403 : status);

  it("pre-fills GitHub's token page with the documented parameters and a 366-day expiry", () => {
    expect(tokenCreationUrl(ORG)).toBe(
      "https://github.com/settings/personal-access-tokens/new" +
        "?name=Copilot+Usage+Monitor" +
        "&description=Read-only+Copilot+AI-credit+pool+for+the+VS+Code+Copilot+Usage+Monitor" +
        "&target_name=acme-co" +
        "&expires_in=366" +
        "&organization_administration=read" +
        "&organization_copilot_seat_management=read",
    );
    expect(tokenCreationUrl("a b&c=d")).toContain("&target_name=a+b%26c%3Dd&");
    expect(tokenCreationUrl(ORG)).not.toContain("write");
  });

  it("walks three steps: Open GitHub, Generate token then Copy, paste", async () => {
    const secrets = new FakeSecretStorage();
    messageAnswers.push(OPEN_GITHUB);
    inputBoxAnswers.push(ORG, ORG_TOKEN);
    const fake = orgFetch((a) => (a === `Bearer ${ORG_TOKEN}` ? 200 : 403), "copilot-internal-user.personal.json");
    expect(await connectOrganization(secrets.asSecretStorage(), fake.fetch, refusedSession(), OCT_2)).toBe("connected");
    const guide = messageOptions.find((o) => typeof o?.detail === "string");
    expect(guide).toMatchObject({ modal: true });
    expect(String(guide?.detail)).toContain("Step 1: Open GitHub.");
    expect(String(guide?.detail)).toContain("Step 2: Click Generate token, then Copy.");
    expect(String(guide?.detail)).toContain("Step 3: Paste it");
    const tokenBox = inputBoxCalls[1];
    expect(tokenBox.password).toBe(true);
    expect(tokenBox.prompt).toBe(TOKEN_PROMPT);
    expect(TOKEN_PROMPT).toContain("secret storage");
    expect(TOKEN_PROMPT).toContain("api.github.com");
    expect(shownMessages.at(-1)?.message).toContain("organization connected");
  });

  it.each([
    [401, "rejected", "GitHub rejected the token"],
    [403, "access-denied", TOKEN_FIX_MESSAGE],
    [404, "access-denied", TOKEN_FIX_MESSAGE],
    [500, "unreachable", "could not verify the token"],
  ])("stores nothing when the check returns %i, and names the fix", async (status, outcome, message) => {
    const secrets = new FakeSecretStorage();
    messageAnswers.push(OPEN_GITHUB);
    inputBoxAnswers.push(ORG, ORG_TOKEN);
    const fake = orgFetch(sessionRefused(status), "copilot-internal-user.personal.json");
    expect(await connectOrganization(secrets.asSecretStorage(), fake.fetch, refusedSession(), OCT_2)).toBe(outcome);
    expect(secrets.stored).toEqual([]);
    expect(configurationUpdates).toEqual([]);
    expect(shownMessages.at(-1)?.level).toBe("warning");
    expect(shownMessages.at(-1)?.message).toContain(message);
  });

  it("names all three plain-words fixes for a refused token", () => {
    expect(TOKEN_FIX_MESSAGE).toContain("resource owner is the organization, not your personal account");
    expect(TOKEN_FIX_MESSAGE).toContain("Administration and GitHub Copilot Business are both set to read-only");
    expect(TOKEN_FIX_MESSAGE).toContain("Pending requests");
  });

  it.each([
    ["the organization prompt", [], [undefined]],
    ["the Open GitHub step", [undefined], [ORG]],
    ["the paste box", [OPEN_GITHUB], [ORG, undefined]],
    ["an empty paste", [OPEN_GITHUB], [ORG, "   "]],
  ])("stores nothing when the user cancels at %s", async (_step, messages, inputs) => {
    const secrets = new FakeSecretStorage();
    messageAnswers.push(...(messages as Array<string | undefined>));
    inputBoxAnswers.push(...(inputs as Array<string | undefined>));
    const fake = orgFetch(sessionRefused(200), "copilot-internal-user.personal.json");
    expect(await connectOrganization(secrets.asSecretStorage(), fake.fetch, refusedSession(), OCT_2)).toBe("cancelled");
    // No call carries the pasted token: only the refused token-free check may have run.
    expect(fake.calls.filter((c) => c.authorization === `Bearer ${ORG_TOKEN}`)).toHaveLength(0);
    expect(secrets.stored).toEqual([]);
    expect(configurationUpdates).toEqual([]);
  });
});

describe("disconnect", () => {
  it("removes the token-free marker and says where to remove read:org", async () => {
    const secrets = new FakeSecretStorage();
    secrets.values.set(ORG_ROUTE_SECRET_KEY, "vscode-session");
    expect(await disconnectOrganization(secrets.asSecretStorage())).toBe("vscode-session");
    expect(secrets.deleted).toEqual([ORG_TOKEN_SECRET_KEY, ORG_ROUTE_SECRET_KEY]);
    expect(await organizationRoute(secrets.asSecretStorage())).toBe("none");
    expect(disconnectMessage("vscode-session")).toContain("Authorized OAuth Apps");
    expect(disconnectMessage("token")).toContain("token deleted");
    expect(disconnectMessage("none")).not.toContain("token");
  });
});

describe("end to end: Connect, refresh, Disconnect (Phase 6 verification expectation)", () => {
  it("token-free 200/200 stores no secret, the status bar shows the pool's month percentage, and Disconnect returns --% (month)", async () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "copilot-connect-"));
    try {
      const auth = scopedAuth({ seat: WORK_TOKEN, readOrg: WORK_TOKEN });
      const fake = routedFetch((url, authorization) => {
        if (url.pathname === "/copilot_internal/user") return jsonResponse(fixture("copilot-internal-user.business-member.json"));
        if (authorization !== `Bearer ${WORK_TOKEN}`) return jsonResponse({}, 403);
        return jsonResponse(fixture(url.pathname.endsWith("/copilot/billing") ? "copilot-billing.json" : "ai-credit-usage.near-limit.synthetic.json"));
      });
      const secrets = new FakeSecretStorage();
      const store = new UsageStore(createMemento());
      const statusBar = new StatusBarManager(store, "copilot-usage.dashboard");
      const statePath = path.join(dir, "copilot.json");
      const controller = new UsageController(
        store,
        new UsageService(new CopilotUsageProvider(auth, fake.fetch), new CopilotOrganizationProvider(secrets.asSecretStorage(), fake.fetch, auth)),
        statusBar,
        statePath,
      );
      const text = (): string => String(createdStatusBarItems[0].text);

      await controller.refresh(OCT_2);
      expect(text()).toContain("Copilot: --% (month)");

      messageAnswers.push(CONNECT_CHOICE);
      expect(await connectOrganization(secrets.asSecretStorage(), fake.fetch, auth, OCT_2)).toBe("connected");
      expect(secrets.values.has(ORG_TOKEN_SECRET_KEY)).toBe(false);
      await controller.refresh(OCT_2);
      expect(text()).toContain("Copilot: 99.25% (month)");
      const state = fs.readFileSync(statePath, "utf-8");
      expect(state).toContain('"percent": 99.25');
      expect(state).not.toContain(SEAT_ORG);

      await disconnectOrganization(secrets.asSecretStorage());
      await controller.organizationRemoved();
      expect(text()).toContain("Copilot: --% (month)");
      expect([...secrets.values.keys()]).toEqual([]);
    } finally {
      fs.rmSync(dir, { recursive: true, force: true });
    }
  });
});

describe("hints and recommendations never show a credit count", () => {
  const seat = (planLabel: string) => ({ planLabel, quotas: [], primary: null, creditsUsed: 12.5, resetsAt: null });

  it("an organization seat is told about Connect; a personal plan with no quota is not", () => {
    const business = { personal: seat("Copilot Business"), lastUpdated: 0, dataSource: "api" as const };
    const individual = { personal: seat("Copilot individual plan"), lastUpdated: 0, dataSource: "api" as const };
    expect(headlineOf(business)).toMatchObject({ kind: "no-percent", reason: "not-connected" });
    expect(headlineOf(individual)).toMatchObject({ kind: "no-percent", reason: "no-personal-quota" });
    expect(getRecommendation(business).message).toBe(NOT_CONNECTED_HINT);
    expect(getRecommendation(individual).message).toBe(NO_PERSONAL_QUOTA_HINT);
    expect(noPercentHint(individual.personal)).not.toContain("organization");
  });

  it.each(["Copilot Business", "Copilot Enterprise", "Copilot individual plan", "GitHub Copilot"])(
    "recommendation output for %s holds no used-credit figure",
    (planLabel) => {
      const recommendation = getRecommendation({ personal: seat(planLabel), lastUpdated: 0, dataSource: "api" });
      const text = [recommendation.message, ...recommendation.tips].join(" ");
      expect(text).not.toMatch(/credits used/i);
      expect(text).not.toContain("12.5");
    },
  );
});
