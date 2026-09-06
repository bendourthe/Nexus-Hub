import type { Money, Quantity } from "./types";

export function escapeHtml(value: string): string {
  return value
    .replace(/&/gu, "&amp;")
    .replace(/</gu, "&lt;")
    .replace(/>/gu, "&gt;")
    .replace(/"/gu, "&quot;")
    .replace(/'/gu, "&#39;");
}

export function formatQuantity(quantity: Quantity | null): string {
  if (quantity === null) {
    return "Not reported";
  }
  return `${formatNumber(quantity.value)} ${quantity.unit}`;
}

export function formatMoney(money: Money | null): string {
  if (money === null) {
    return "Not reported";
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: money.currency,
    maximumFractionDigits: 2
  }).format(money.amount);
}

/**
 * Renders a percentage with up to one decimal, trailing `.0` trimmed.
 *
 * Plain rounding turned the dashboard's own 1.7% pool into "2%", which overstates
 * a nearly-untouched allowance. One decimal keeps a small pool honest while an
 * integer still reads as an integer.
 */
export function formatPercent(percent: number): string {
  const clamped = Math.max(0, percent);
  return `${new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 1
  }).format(clamped)}%`;
}

/**
 * Formats a billing-cycle date in UTC. The cycle boundary is a calendar date on
 * Cursor's side, so rendering it in the host's local zone could show the previous
 * day west of UTC and make the reset note disagree with the dashboard.
 */
export function formatCalendarDate(value: string | null): string {
  if (value === null) {
    return "an unreported date";
  }
  const parsed = Date.parse(value);
  if (!Number.isFinite(parsed)) {
    return "an unreported date";
  }
  return new Date(parsed).toLocaleDateString("en-US", {
    timeZone: "UTC",
    year: "numeric",
    month: "long",
    day: "numeric"
  });
}

/**
 * The annotation that keeps the on-demand pool from reading as a personal cap.
 * The reset date comes from the payload's billing cycle, never a hardcoded day.
 */
export function formatSharedSpendNote(resetsAt: string | null): string {
  return `This spend limit is shared across your team, not a personal allowance. It resets ${formatCalendarDate(resetsAt)}.`;
}

/**
 * The on-demand bar's geometry only. Returns null when a fraction would be
 * meaningless: no spend, no limit, mismatched currencies, or a non-positive
 * denominator. Mixing currencies here would be the money equivalent of the
 * unit-mismatch the included-usage meters already refuse.
 */
export function spendFractionOfLimit(
  spend: Money | null,
  limit: Money | null
): number | null {
  if (spend === null || limit === null) {
    return null;
  }
  if (spend.currency !== limit.currency || !(limit.amount > 0)) {
    return null;
  }
  return (spend.amount / limit.amount) * 100;
}

/**
 * On-demand is currency against a spend limit, so its label stays in currency and
 * is never collapsed into a percentage of tokens.
 */
export function formatSpendAgainstLimit(
  spend: Money | null,
  limit: Money | null
): string {
  if (spend === null) {
    return "Not reported";
  }
  const spentText = formatMoney(spend);
  if (limit === null) {
    return `${spentText} spent; limit not reported`;
  }
  if (spend.currency !== limit.currency) {
    return `${spentText} spent; limit ${formatMoney(limit)} uses a different currency`;
  }
  return `${spentText} of ${formatMoney(limit)}`;
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2
  }).format(value);
}
