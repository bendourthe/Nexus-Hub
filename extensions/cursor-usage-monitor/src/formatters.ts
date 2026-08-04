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

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2
  }).format(value);
}
