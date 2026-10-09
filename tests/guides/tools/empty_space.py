"""The empty-space measure behind v4.13.10 DoD 10, shared by the layout tests.

A section's content box (inside its padding) is laid on an 8 px grid. A cell is empty when
no visible text run, image, SVG, canvas, video, form control, or box with a visible
background or border touches it. ``largest_empty_rect`` returns the largest all-empty
rectangle as width and height in CSS pixels. Baseline and thresholds:
docs/releases/v4/v4.13/development/v4.13.10-inventory.md.
"""

from __future__ import annotations

CELL = 8

#: DoD 10: a section fails when an empty rectangle is at least this share of the content
#: width wide AND at least this many pixels tall.
THRESHOLDS = {1280: (0.25, 160), 390: (0.50, 120)}

EMPTY_RECT_JS = r"""
(el) => {
  const CELL = 8;
  const visible = (n) => {
    const cs = getComputedStyle(n);
    return cs.display !== 'none' && cs.visibility !== 'hidden' && parseFloat(cs.opacity) > 0.01;
  };
  const painted = (n) => {
    const tag = n.tagName.toLowerCase();
    if (['img','svg','canvas','video','input','button','select','textarea','picture','hr'].includes(tag)) return true;
    const cs = getComputedStyle(n);
    const bg = cs.backgroundColor;
    const hasBg = (bg && bg !== 'transparent' && !/rgba\([^)]*,\s*0\)$/.test(bg)) || cs.backgroundImage !== 'none';
    const hasBorder = ['Top','Right','Bottom','Left'].some(s => parseFloat(cs['border' + s + 'Width']) > 0 && cs['border' + s + 'Style'] !== 'none');
    return hasBg || hasBorder;
  };
  const cs = getComputedStyle(el), b = el.getBoundingClientRect();
  const L = b.left + parseFloat(cs.paddingLeft) + parseFloat(cs.borderLeftWidth);
  const R = b.right - parseFloat(cs.paddingRight) - parseFloat(cs.borderRightWidth);
  const T = b.top + parseFloat(cs.paddingTop) + parseFloat(cs.borderTopWidth);
  const B = b.bottom - parseFloat(cs.paddingBottom) - parseFloat(cs.borderBottomWidth);
  const cols = Math.max(1, Math.floor((R - L) / CELL)), rows = Math.max(1, Math.floor((B - T) / CELL));
  const grid = Array.from({length: rows}, () => new Uint8Array(cols));
  const mark = (r) => {
    const c0 = Math.max(0, Math.floor((r.left - L) / CELL)), c1 = Math.min(cols - 1, Math.floor((r.right - L - 0.01) / CELL));
    const r0 = Math.max(0, Math.floor((r.top - T) / CELL)), r1 = Math.min(rows - 1, Math.floor((r.bottom - T - 0.01) / CELL));
    for (let y = r0; y <= r1; y++) for (let x = c0; x <= c1; x++) grid[y][x] = 1;
  };
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    if (n.nodeType === 3) {
      if (n.textContent.trim() && n.parentElement && visible(n.parentElement)) {
        const rg = document.createRange(); rg.selectNodeContents(n);
        for (const rr of rg.getClientRects()) if (rr.width > 0 && rr.height > 0) mark(rr);
      }
    } else if (visible(n) && painted(n)) {
      const r = n.getBoundingClientRect();
      if (r.width > 0 && r.height > 0) mark(r);
    }
  }
  const h = new Array(cols).fill(0);
  let best = {w: 0, h: 0};
  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < cols; x++) h[x] = grid[y][x] ? 0 : h[x] + 1;
    const st = [];
    for (let x = 0; x <= cols; x++) {
      const cur = x === cols ? 0 : h[x];
      let start = x;
      while (st.length && st[st.length - 1][1] >= cur) {
        const [i, hh] = st.pop();
        if (hh * (x - i) > best.w * best.h) best = {w: x - i, h: hh};
        start = i;
      }
      st.push([start, cur]);
    }
  }
  return {contentWidth: R - L, width: best.w * CELL, height: best.h * CELL};
}
"""


def largest_empty_rect(locator) -> dict:
    """Measure the element behind a Playwright locator: content width and the largest empty rectangle."""
    return locator.evaluate(EMPTY_RECT_JS)


def too_empty(result: dict, viewport_width: int) -> bool:
    """True when the result breaks DoD 10 at that viewport width (1280 or 390)."""
    share, height = THRESHOLDS[viewport_width]
    return result["width"] >= share * result["contentWidth"] and result["height"] >= height
