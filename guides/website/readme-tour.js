/* Deterministic tour overlay shared by the local preview and GIF renderer. */
(function () {
  "use strict";
  let serial = 0;
  function mount(root) {
    const layer = document.createElement("div"), id = "readme-tour-mask-" + serial++;
    layer.className = "tour-layer";
    layer.setAttribute("aria-hidden", "true");
    layer.innerHTML = `<svg class="tour-shade"><defs><mask id="${id}"><rect width="100%" height="100%" fill="white"/><rect class="tour-hole" fill="black" rx="7"/></mask></defs><rect width="100%" height="100%" fill="#000" fill-opacity=".58" mask="url(#${id})"/><rect class="tour-outline" fill="none" stroke="#4adbe6" stroke-opacity=".8" rx="7"/></svg><div class="tour-cursor"><svg viewBox="0 0 24 30"><path d="M3 2v23l6-6 4 9 4-2-4-9h8z" fill="white" stroke="#111" stroke-width="1.7"/></svg><i></i></div>`;
    root.style.position = "relative";
    root.append(layer);
    let previous = null;
    function focus(target, options = {}) {
      const base = root.getBoundingClientRect();
      const box = typeof target === "string" ? root.querySelector(target)?.getBoundingClientRect() : target?.getBoundingClientRect ? target.getBoundingClientRect() : target;
      if (!box) { layer.hidden = true; return; }
      layer.hidden = false;
      const x = Math.max(1, box.x - base.x - 6), y = Math.max(1, box.y - base.y - 6);
      const width = Math.max(0, Math.min(box.width + 12, base.width - x - 1)), height = Math.max(0, Math.min(box.height + 12, base.height - y - 1));
      for (const selector of [".tour-hole", ".tour-outline"]) {
        const node = layer.querySelector(selector);
        for (const [key, value] of Object.entries({ x, y, width, height })) node.setAttribute(key, value);
      }
      const destination = options.point || { x: box.x - base.x + Math.min(box.width * .6, box.width - 12), y: box.y - base.y + Math.min(box.height * .6, 40) };
      const from = options.from || previous || { x: base.width * .8, y: base.height * .8 };
      const t = options.progress ?? 1, ease = t * t * (3 - 2 * t);
      const cursor = layer.querySelector(".tour-cursor");
      cursor.hidden = options.cursor === false;
      cursor.style.transform = `translate(${from.x + (destination.x - from.x) * ease}px,${from.y + (destination.y - from.y) * ease}px)`;
      cursor.classList.toggle("is-click", !!options.click);
      if (t === 1) previous = destination;
      return { destination, from };
    }
    return { focus, hide() { layer.hidden = true; }, layer };
  }
  window.ReadmeTour = { mount };
})();
