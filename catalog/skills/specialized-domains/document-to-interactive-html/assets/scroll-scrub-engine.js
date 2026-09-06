/**
 * scroll-scrub-engine.js - a zero-dependency scroll-scrubbed cinematic stage.
 *
 * Scrolling drives a continuous camera movement through a document's own
 * sections: each section owns a clip (or a still), and page scroll maps to that
 * clip's `currentTime` rather than to a discrete reveal.
 *
 * ADAPT THIS, do not paste it. It is a working reference implementation, and the
 * protocol it implements - the size/cost gate, the asset boundary, the seam rule,
 * the accessibility floor - is in `references/scroll-scrub.md`. Read that first;
 * this file is the mechanism, not the policy.
 *
 * Design constraints, all load-bearing:
 *
 *   1. ZERO dependencies. Vanilla DOM and CSS only. No eval, no cookies, no
 *      WebSocket, no fetch to any host.
 *   2. Clips load from `data:` URIs or Blob object URLs, so the authored `.html`
 *      stays ONE FILE. HTTP byte-range serving of sibling files is not the
 *      primary path and must not become one - a page that needs `clip-01.mp4`
 *      beside it is not a self-contained output.
 *   3. STILLS-ONLY IS THE BASE MODE, video is the enhancement. Under
 *      `prefers-reduced-motion: reduce` no video element is created and no clip
 *      is decoded - not muted, not paused, not created. Built this way round
 *      because a reduced-motion path bolted on afterwards is the one that breaks.
 *   4. Namespaced. Every class is `ss-`; styles are injected into the
 *      caller-supplied container, never into the document at large.
 *   5. No vendor, product, or upstream repository name appears anywhere in this
 *      file - identifiers, comments, or strings.
 *
 * Usage:
 *
 *   ScrollScrub.mount(document.querySelector('#stage'), {
 *     sections: [
 *       { id: 'intro',  clip: 'data:video/mp4;base64,...', still: 'data:image/webp;base64,...',
 *         scroll: 1.5, linger: 0.25 },
 *       { id: 'method', still: 'data:image/webp;base64,...', scroll: 1.0 }
 *     ],
 *     seamFade: 0.2,        // seconds of cross-dissolve at each seam
 *     atmosphere: false,    // optional particle layer; forced off under reduce/coarse
 *     driver: 'scroll'      // 'scroll' (default) or 'step' (slide mode)
 *   });
 *
 * `scroll` is how much viewport-height a section consumes; `linger` is the
 * fraction of that distance during which the clip barely advances, so the
 * reader can actually read the copy instead of watching it slide past.
 *
 * Drivers. Under `driver: 'scroll'` page scroll is the input, exactly as
 * described above. Under `driver: 'step'` (a `nav=slides` deck) the engine
 * attaches NO scroll listener and the caller drives the camera instead:
 *
 *   var stage = ScrollScrub.mount(el, { sections: [...], driver: 'step' });
 *   // from the deck's fragment handler, one call per camera keyframe:
 *   stage.goTo(sectionIndex, progress);                     // tweened
 *   stage.goTo(sectionIndex, progress, { instant: true });  // settled cut
 *
 * Everything downstream of the driver - linger, seam crossfade, seek
 * coalescing, the stills-only reduced-motion path - is shared. The engine
 * never listens for keys itself: input ownership stays with the slide
 * runtime, per `references/slide-navigation.md`. An interrupted tween
 * retargets from the currently-shown state (fast-forward semantics - the
 * end state is authoritative, inputs are never dropped or double-applied),
 * and under reduced motion every goTo is an instant cut.
 */

(function (global) {
  'use strict';

  var PREFIX = 'ss-';
  var STYLE_ID = PREFIX + 'styles';

  var CSS = [
    '.' + PREFIX + 'stage{position:relative;isolation:isolate}',
    '.' + PREFIX + 'viewport{position:sticky;top:0;height:100vh;overflow:hidden}',
    '.' + PREFIX + 'layer{position:absolute;inset:0;width:100%;height:100%;',
    '  object-fit:cover;opacity:0;transition:opacity var(--' + PREFIX + 'fade,200ms) linear;',
    '  will-change:opacity}',
    '.' + PREFIX + 'layer.' + PREFIX + 'on{opacity:1}',
    '.' + PREFIX + 'track{position:relative;z-index:1}',
    '.' + PREFIX + 'copy{position:relative;z-index:2}',
    '@media (prefers-reduced-motion: reduce){',
    '  .' + PREFIX + 'layer{transition-duration:1ms}',
    '}'
  ].join('');

  function injectStyles(container) {
    var root = container.ownerDocument;
    if (root.getElementById(STYLE_ID)) return;
    var style = root.createElement('style');
    style.id = STYLE_ID;
    style.textContent = CSS;
    (root.head || container).appendChild(style);
  }

  function prefersReducedMotion(view) {
    try {
      return view.matchMedia('(prefers-reduced-motion: reduce)').matches;
    } catch (err) {
      // No matchMedia (very old or synthetic environment): assume the SAFE
      // answer. Guessing "no preference" would start decoding video for someone
      // who asked for stillness.
      return true;
    }
  }

  function isCoarsePointer(view) {
    try {
      return view.matchMedia('(pointer: coarse)').matches;
    } catch (err) {
      return false;
    }
  }

  function clamp01(value) {
    return value < 0 ? 0 : value > 1 ? 1 : value;
  }

  /**
   * Remap raw 0..1 section progress so a `linger` fraction in the middle barely
   * advances the clip. Without this the copy scrolls past under a moving camera
   * and nobody reads it.
   */
  function applyLinger(progress, linger) {
    if (!linger || linger <= 0) return progress;
    var hold = Math.min(0.9, linger);
    var lead = (1 - hold) / 2;
    if (progress < lead) return (progress / lead) * lead;
    if (progress > 1 - lead) return 1 - lead + ((progress - (1 - lead)) / lead) * lead;
    // Inside the hold window: advance only slightly.
    return lead + ((progress - lead) / hold) * 0.02;
  }

  function ScrollScrub(container, config) {
    this.container = container;
    this.view = container.ownerDocument.defaultView || global;
    this.config = config || {};
    this.sections = (this.config.sections || []).slice();
    this.reduced = prefersReducedMotion(this.view);
    this.coarse = isCoarsePointer(this.view);
    // Atmosphere is a nice-to-have that costs battery and vestibular comfort, so
    // it is off under reduced motion and on touch devices regardless of config.
    this.atmosphere = !!this.config.atmosphere && !this.reduced && !this.coarse;
    this.driver = this.config.driver === 'step' ? 'step' : 'scroll';
    this.layers = [];
    this.active = -1;
    this.frame = null;
    this.primed = false;
    this._onScroll = null;
    this._onFirstTouch = null;
    this._tweenFrame = null;
    this._shown = { index: 0, progress: 0 };
  }

  ScrollScrub.prototype.mount = function () {
    if (!this.container || !this.sections.length) return this;
    injectStyles(this.container);
    this.container.classList.add(PREFIX + 'stage');

    var doc = this.container.ownerDocument;
    var viewport = doc.createElement('div');
    viewport.className = PREFIX + 'viewport';
    viewport.setAttribute('aria-hidden', 'true'); // decorative; copy lives outside
    var fade = this.config.seamFade;
    if (typeof fade === 'number' && fade >= 0) {
      viewport.style.setProperty('--' + PREFIX + 'fade', Math.round(fade * 1000) + 'ms');
    }

    for (var i = 0; i < this.sections.length; i++) {
      this.layers.push(this._buildLayer(doc, this.sections[i]));
      viewport.appendChild(this.layers[i].el);
    }
    this.container.insertBefore(viewport, this.container.firstChild);

    if (this.driver === 'scroll') {
      this._onScroll = this._schedule.bind(this);
      this.view.addEventListener('scroll', this._onScroll, { passive: true });
      this.view.addEventListener('resize', this._onScroll, { passive: true });
    }
    if (!this.reduced) this._armPriming();
    if (this.driver === 'scroll') {
      this._update();
    } else {
      this.goTo(0, 0, { instant: true });
    }
    return this;
  };

  /**
   * One layer per section. Under reduced motion a `<video>` is never created -
   * not created and paused, not created muted: not created. That is the only
   * form of the guarantee that cannot regress by accident.
   */
  ScrollScrub.prototype._buildLayer = function (doc, section) {
    var useVideo = !this.reduced && !!section.clip;
    var el;
    if (useVideo) {
      el = doc.createElement('video');
      el.muted = true;            // required for programmatic play on mobile
      el.defaultMuted = true;
      el.playsInline = true;
      el.setAttribute('playsinline', '');
      el.setAttribute('muted', '');
      el.preload = 'auto';
      if (section.still) el.poster = section.still;
      el.src = section.clip;      // a data: URI or a Blob object URL
    } else {
      el = doc.createElement('img');
      el.decoding = 'async';
      el.alt = '';
      if (section.still) el.src = section.still;
    }
    el.className = PREFIX + 'layer';
    return { el: el, section: section, video: useVideo, seeking: false, pending: null };
  };

  /**
   * iOS will not let a script seek or play a video until the user has interacted,
   * so prime every clip once on the first touch. Priming is a play/pause pair on
   * a muted element - it starts no playback the reader can perceive.
   */
  ScrollScrub.prototype._armPriming = function () {
    var self = this;
    this._onFirstTouch = function () {
      if (self.primed) return;
      self.primed = true;
      for (var i = 0; i < self.layers.length; i++) {
        var layer = self.layers[i];
        if (!layer.video) continue;
        try {
          var promise = layer.el.play();
          if (promise && typeof promise.then === 'function') {
            promise.then(function () {}, function () {});
          }
          layer.el.pause();
        } catch (err) {
          // A refused prime is not fatal; the layer falls back to its poster.
        }
      }
      self.view.removeEventListener('touchstart', self._onFirstTouch);
      self.view.removeEventListener('pointerdown', self._onFirstTouch);
    };
    this.view.addEventListener('touchstart', this._onFirstTouch, { passive: true });
    this.view.addEventListener('pointerdown', this._onFirstTouch, { passive: true });
  };

  // Coalesce scroll events onto one animation frame. A touch device fires scroll
  // far faster than a video can seek, and queueing every event makes the scrub
  // stutter in a way that reads as a broken page.
  ScrollScrub.prototype._schedule = function () {
    if (this.frame !== null) return;
    var self = this;
    this.frame = this.view.requestAnimationFrame(function () {
      self.frame = null;
      self._update();
    });
  };

  ScrollScrub.prototype._update = function () {
    var doc = this.container.ownerDocument;
    var tracks = this.container.querySelectorAll('.' + PREFIX + 'track > [data-' + PREFIX + 'section]');
    var viewportHeight = this.view.innerHeight || doc.documentElement.clientHeight;
    var current = -1;
    var progress = 0;

    for (var i = 0; i < tracks.length && i < this.layers.length; i++) {
      var box = tracks[i].getBoundingClientRect();
      if (box.top <= viewportHeight * 0.5 && box.bottom > viewportHeight * 0.5) {
        current = i;
        progress = clamp01((viewportHeight * 0.5 - box.top) / Math.max(1, box.height));
        break;
      }
    }
    if (current < 0) current = this.active < 0 ? 0 : this.active;

    if (current !== this.active) {
      for (var j = 0; j < this.layers.length; j++) {
        this.layers[j].el.classList.toggle(PREFIX + 'on', j === current);
      }
      this.active = current;
    }
    this._seek(this.layers[current], progress);
  };

  ScrollScrub.prototype._seek = function (layer, rawProgress) {
    if (!layer) return;
    var eased = applyLinger(rawProgress, layer.section.linger);
    if (!layer.video) {
      // Stills path: a gentle scale is the whole effect. No decode, no seek.
      layer.el.style.transform = 'scale(' + (1 + eased * 0.06).toFixed(4) + ')';
      return;
    }
    var duration = layer.el.duration;
    if (!duration || !isFinite(duration)) return;
    var target = eased * duration;
    if (layer.seeking) {
      // Keep only the newest target; superseded seeks are dropped rather than
      // queued, which is what keeps a fast scroll from falling behind.
      layer.pending = target;
      return;
    }
    this._commitSeek(layer, target);
  };

  ScrollScrub.prototype._commitSeek = function (layer, target) {
    var self = this;
    layer.seeking = true;
    var done = function () {
      layer.el.removeEventListener('seeked', done);
      layer.seeking = false;
      if (layer.pending !== null) {
        var next = layer.pending;
        layer.pending = null;
        self._commitSeek(layer, next);
      }
    };
    layer.el.addEventListener('seeked', done);
    try {
      layer.el.currentTime = target;
    } catch (err) {
      layer.el.removeEventListener('seeked', done);
      layer.seeking = false;
    }
  };

  /**
   * Step-driver API: move the camera to (sectionIndex, progress). The deck's
   * fragment handler maps each camera keyframe onto one goTo target. Same
   * downstream path as the scroll driver (_seek applies linger and the video
   * path's own seek coalescing), so the camera language is identical in both
   * modes. Callable under driver 'scroll' too (e.g. an anchor jump), where the
   * next scroll event simply takes over again.
   */
  ScrollScrub.prototype.goTo = function (index, progress, opts) {
    if (!this.layers.length) return this;
    opts = opts || {};
    index = Math.max(0, Math.min(this.layers.length - 1, index | 0));
    progress = clamp01(typeof progress === 'number' ? progress : 0);

    // Fast-forward semantics: an in-flight tween is cancelled and the new tween
    // retargets from wherever the camera visually is. End state stays
    // authoritative; no input is dropped or double-applied.
    if (this._tweenFrame !== null) {
      this.view.cancelAnimationFrame(this._tweenFrame);
      this._tweenFrame = null;
    }

    var crossing = index !== this._shown.index;
    if (crossing || this.active !== index) {
      // The seam crossfade (the CSS opacity transition on the layer class)
      // handles the visual handover, exactly as a scroll-driven change would.
      // `this.active !== index` also covers the very first goTo after mount,
      // where nothing is painted yet (active starts at -1) but _shown already
      // points at section 0 - without it the initial layer never turns on.
      for (var j = 0; j < this.layers.length; j++) {
        this.layers[j].el.classList.toggle(PREFIX + 'on', j === index);
      }
      this.active = index;
    }
    var layer = this.layers[index];
    // Entering a new section the camera starts from that section's near edge
    // in the direction of travel; within a section, from the shown state.
    var from = crossing ? (index > this._shown.index ? 0 : 1) : this._shown.progress;

    if (opts.instant || this.reduced) {
      this._shown = { index: index, progress: progress };
      this._seek(layer, progress);
      return this;
    }

    var duration = typeof opts.duration === 'number' ? opts.duration
      : (typeof this.config.stepDuration === 'number' ? this.config.stepDuration : 600);
    var start = null;
    var self = this;
    this._shown.index = index;
    var tick = function (now) {
      if (start === null) start = now;
      var t = clamp01(duration <= 0 ? 1 : (now - start) / duration);
      // Ease-in-out cubic: the temporal shape a scrub over the same segment
      // would have had, so stepping and scrolling read as the same camera.
      var eased = t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
      var value = from + (progress - from) * eased;
      self._shown.progress = value;
      self._seek(layer, value);
      if (t < 1) {
        self._tweenFrame = self.view.requestAnimationFrame(tick);
      } else {
        self._tweenFrame = null;
      }
    };
    this._tweenFrame = this.view.requestAnimationFrame(tick);
    return this;
  };

  ScrollScrub.prototype.destroy = function () {
    if (this._onScroll) {
      this.view.removeEventListener('scroll', this._onScroll);
      this.view.removeEventListener('resize', this._onScroll);
    }
    if (this._onFirstTouch) {
      this.view.removeEventListener('touchstart', this._onFirstTouch);
      this.view.removeEventListener('pointerdown', this._onFirstTouch);
    }
    if (this.frame !== null) this.view.cancelAnimationFrame(this.frame);
    if (this._tweenFrame !== null) this.view.cancelAnimationFrame(this._tweenFrame);
    for (var i = 0; i < this.layers.length; i++) {
      var el = this.layers[i].el;
      if (el.parentNode) el.parentNode.removeChild(el);
    }
    this.layers = [];
    return this;
  };

  var api = {
    mount: function (container, config) {
      return new ScrollScrub(container, config).mount();
    },
    // Exposed for tests and for callers that want to inspect the resolved mode
    // before building assets.
    prefersReducedMotion: prefersReducedMotion,
    applyLinger: applyLinger,
    PREFIX: PREFIX
  };

  if (typeof module === 'object' && module.exports) {
    module.exports = api;
  } else {
    global.ScrollScrub = api;
  }
})(typeof globalThis !== 'undefined' ? globalThis : this);
