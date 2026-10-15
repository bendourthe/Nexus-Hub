---
name: browser-testing-with-devtools
description: "Uses browser DevTools to test, debug, and verify frontend behavior during development -- covering network inspection, console debugging, performance profiling, accessibility auditing, and storage inspection. Use when debugging a frontend issue, verifying that a change has the expected browser-level effect, or testing without a full E2E framework. Trigger phrases: check in the browser, use DevTools, browser debugging, inspect network, check console errors, browser testing, verify in browser."
summary_l0: "Test and debug frontend behavior using browser DevTools for network, console, performance, and accessibility"
overview_l1: "This skill covers systematic browser DevTools usage for frontend testing and debugging -- distinct from E2E automation frameworks. Use it when investigating a bug that only reproduces in the browser, verifying network requests and responses, checking for console errors or warnings, profiling render performance, auditing accessibility, or inspecting storage state. Key capabilities include Network panel analysis, Console log interpretation, Elements inspector for DOM/CSS debugging, Lighthouse auditing, Application panel for cookies/localStorage, and Performance panel for flame charts. The expected output is a confirmed diagnosis or verified behavior change observable in the browser, not just passing unit tests. Trigger phrases: check in the browser, use Chrome DevTools, browser debugging, inspect the request, check console, verify it works in the browser."
---

# Browser Testing with DevTools

Test and verify frontend behavior directly in the browser. Some bugs only live there.

## When to Use This Skill

Use when:
- A bug reproduces in the browser but not in unit tests
- Verifying that an API call is made with the correct request/response shape
- Checking for console errors or warnings introduced by a change
- Auditing performance, accessibility, or security headers on a page
- Inspecting cookies, localStorage, or session storage state
- Profiling slow renders or layout shifts

**When NOT to use:** For automated regression testing across many user flows, use `e2e-testing-automation`. DevTools is for development-time investigation and verification, not CI-gated automation.

## DevTools Quick Reference

### Opening DevTools

| Browser | Shortcut |
|---|---|
| Chrome / Edge | `F12` or `Ctrl+Shift+I` (Windows/Linux), `Cmd+Option+I` (Mac) |
| Firefox | `F12` or `Ctrl+Shift+I` |
| Safari | `Cmd+Option+I` (enable in Preferences → Advanced → Show Develop menu first) |

---

## Network Panel: Verify API Calls

Use to confirm requests are made, responses are correct, and errors are surfaced.

**Checklist:**
- [ ] Open Network panel before triggering the action (requests made before it opens are not captured)
- [ ] Filter by `Fetch/XHR` to isolate API calls from asset loads
- [ ] Click the request → Headers tab: verify method, URL, request headers (auth tokens, Content-Type)
- [ ] Click the request → Payload tab: verify request body matches expected schema
- [ ] Click the request → Response tab: verify response body and status code
- [ ] Check timing: is the request slow? Which phase (DNS, Connection, TTFB, Download)?
- [ ] Check for CORS errors: preflight OPTIONS request failing → check server CORS headers

**Common issues to look for:**
- `401 Unauthorized` -- auth token not sent or expired
- `CORS error` -- missing or wrong `Access-Control-Allow-Origin` header
- `400 Bad Request` -- request body schema mismatch; check Payload tab vs. API spec
- `ERR_BLOCKED_BY_CLIENT` -- adblocker or privacy extension blocking the request

---

## Console Panel: Catch Errors and Warnings

**Checklist:**
- [ ] Filter to `Errors` first -- these are breaking issues
- [ ] Filter to `Warnings` -- these are often deprecations, missing keys, or a11y violations
- [ ] Check for unhandled Promise rejections -- they appear as errors with no stack boundary
- [ ] Check for React/Vue/Svelte component warnings: missing props, key warnings, invalid DOM nesting
- [ ] Run `console.clear()` before reproducing the bug to isolate relevant messages

**Useful console commands:**
```javascript
// Inspect an element's event listeners
getEventListeners(document.getElementById('my-btn'))

// Monitor all events on an element
monitorEvents(document.getElementById('my-btn'), 'click')

// Copy an object to clipboard
copy(JSON.stringify(window.__store__?.getState()))
```

---

## Elements Panel: Debug DOM and CSS

**Checklist:**
- [ ] Verify the DOM structure matches expected semantic HTML (no missing elements)
- [ ] Check computed styles on an element: which rule is actually applied? Is something being overridden?
- [ ] Check Accessibility tab (within Elements): is the `role`, `name`, and `state` correct for screen readers?
- [ ] Edit CSS live in the Styles pane to prototype a fix before writing it
- [ ] Use `Ctrl+F` in the Elements panel to search for specific attributes or text

---

## Lighthouse: Audit Performance, Accessibility, SEO

**How to run:**
1. Open DevTools → Lighthouse tab
2. Select categories: Performance, Accessibility, Best Practices, SEO
3. Select device: Mobile (harder) or Desktop
4. Click "Analyze page load"

**Minimum scores before shipping a production feature:**
- Performance: ≥ 70
- Accessibility: ≥ 90 (aim for 100)
- Best Practices: ≥ 90
- SEO: ≥ 80

**Common accessibility violations to fix immediately:**
- Missing `alt` attributes on images
- Low color contrast (< 4.5:1 for normal text)
- Buttons without accessible names
- Form inputs missing `<label>` elements
- Heading levels skipped (e.g., h1 → h3, no h2)

---

## Application Panel: Inspect Storage

**Checklist:**
- [ ] Cookies: verify auth tokens are set with `HttpOnly`, `Secure`, `SameSite=Strict`
- [ ] localStorage / sessionStorage: check that sensitive data is not stored here (tokens, PII)
- [ ] Service Worker: verify the correct version is active; clear if stale cache is suspected
- [ ] Cache Storage: check if outdated cached responses are serving old data

---

## Performance Panel: Profile Render Issues

Use when a page or interaction feels slow.

1. Open Performance panel → click record
2. Reproduce the slow interaction
3. Stop recording
4. Look for:
   - **Long tasks** (red triangles, > 50ms on main thread) -- these block interactivity
   - **Layout shifts** (purple bars) -- elements moving after initial render (CLS)
   - **Scripting time** (yellow) -- JS execution taking too long
   - **Rendering time** (purple) -- style recalculation or layout thrashing

**Quick fixes for common findings:**
- Long tasks from JS: code-split, defer non-critical scripts
- Layout thrashing: avoid reading layout properties (offsetWidth, getBoundingClientRect) in loops
- CLS: set explicit width/height on images and media elements

---

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Unit tests pass, so it works" | Unit tests don't run in a browser. Network timing, CORS, auth headers, and DOM behavior are only visible in the browser. |
| "I'll check it in the browser later" | "Later" rarely happens before shipping. Verify in the browser during development, not after a bug report. |
| "The console warning is harmless" | Warnings are debt. React key warnings cause incorrect rendering at scale. A11y warnings are bugs for screen reader users. |
| "Lighthouse score is just a number" | It correlates directly with real user experience and SEO ranking. A score of 45 on Performance is a user-facing problem. |

## Verification

- [ ] Network panel confirms the expected API calls are made with the correct headers and body
- [ ] Console panel shows no new errors or unhandled rejections introduced by the change
- [ ] Lighthouse accessibility score is ≥ 90 on the modified page
- [ ] Manual keyboard navigation: all interactive elements are reachable and operable
- [ ] No sensitive data (tokens, PII) visible in localStorage or sessionStorage

## Related Skills

- [[functional-verification]] -- owns artifact-level exercise and its evidence record; this skill supplies browser observations and diagnostics.
- [[frontend-ui-engineering]] -- accessibility and responsive design practices
- [[e2e-testing-automation]] -- automate browser flows with Playwright or Cypress
- [[performance-review]] -- systematic performance bottleneck identification
- [[security-review]] -- check security headers and CSP configuration
