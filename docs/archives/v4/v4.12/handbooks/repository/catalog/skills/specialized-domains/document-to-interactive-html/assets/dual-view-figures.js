/* Independent figure interactions for either view; canonical data stays untouched. */
(() => {
  'use strict';
  document.addEventListener('click', event => {
    const reset = event.target.closest('[data-dv-figure-reset]');
    if (reset) {
      const figure = reset.closest('figure');
      const zoom = figure.querySelector('[data-dv-zoom]');
      zoom.value = '1';
      zoom.dispatchEvent(new Event('input', { bubbles: true }));
      figure.querySelectorAll('[data-dv-series][aria-pressed="false"]').forEach(button => button.click());
      figure.querySelectorAll('[data-dv-zoom-view]').forEach(view => view.scrollTo(0, 0));
    }
    const toggle = event.target.closest('[data-dv-series]');
    if (toggle) {
      const figure = toggle.closest('[data-dv-figure]');
      const visible = toggle.getAttribute('aria-pressed') !== 'true';
      toggle.setAttribute('aria-pressed', String(visible));
      figure.querySelectorAll('[data-dv-series-marks]').forEach(group => {
        if (group.dataset.dvSeriesMarks === toggle.dataset.dvSeries) group.style.display = visible ? '' : 'none';
      });
    }
    const region = event.target.closest('[data-dv-region]');
    if (region) {
      const figure = region.closest('[data-dv-map]');
      figure.querySelector('[data-dv-map-status]').textContent = region.dataset.dvRegion;
      figure.querySelectorAll('[data-region]').forEach(node => {
        node.dataset.selected = String(node.dataset.region === region.dataset.dvRegion);
      });
    }
    const enlarge = event.target.closest('[data-dv-enlarge]');
    if (enlarge) {
      const image = enlarge.querySelector('img').cloneNode(true);
      image.removeAttribute('id');
      const dialog = document.createElement('dialog');
      dialog.className = 'dv-enlargement';
      dialog.setAttribute('aria-label', image.alt || 'Enlarged image');
      const close = document.createElement('button');
      close.textContent = 'Close image';
      close.addEventListener('click', () => dialog.close());
      dialog.append(image, close);
      (enlarge.closest('[data-dv-deck]') || document.body).append(dialog);
      dialog.addEventListener('close', () => { dialog.remove(); enlarge.focus({ preventScroll: true }); }, { once: true });
      dialog.showModal();
      close.focus();
    }
  });
  document.addEventListener('input', event => {
    if (event.target.matches('[data-dv-zoom]')) {
      const svg = event.target.closest('figure').querySelector('[data-dv-zoom-view] > svg');
      svg.style.maxWidth = 'none';
      svg.style.width = `${Number(event.target.value) * 100}%`;
      svg.style.maxHeight = Number(event.target.value) === 1 ? '' : 'none';
      return;
    }
    if (!event.target.matches('[data-dv-map-search]')) return;
    const query = event.target.value.toLocaleLowerCase();
    const figure = event.target.closest('[data-dv-map]');
    let count = 0;
    figure.querySelectorAll('[data-dv-region]').forEach(region => {
      region.hidden = !region.dataset.dvRegion.toLocaleLowerCase().includes(query);
      if (!region.hidden) count += 1;
    });
    figure.querySelector('[data-dv-map-status]').textContent = `${count} matching regions`;
  });
})();
