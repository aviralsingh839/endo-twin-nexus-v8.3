/* ENDO-TWIN NEXUS research portal — progressive enhancement (2026-09)
 *
 * Accessibility contract for this file:
 *  - Nothing here is required to read the page. With JS disabled the content is
 *    fully visible, every link works, and the nav is a plain link list.
 *  - Content is never left hidden: the scroll-reveal only arms itself when
 *    IntersectionObserver exists, motion is not reduced, and it force-reveals
 *    everything if the observer never fires.
 *  - Anchors keep their native behaviour (focus move, :target, history) so
 *    keyboard and screen-reader users are not displaced. We only add
 *    scroll-margin via CSS and close the mobile menu.
 *  - State is exposed with aria-* attributes, and colour is never the only cue.
 */
(function () {
  'use strict';

  var reduceMotion = window.matchMedia
    ? window.matchMedia('(prefers-reduced-motion: reduce)')
    : { matches: false };

  var STORAGE_KEY = 'endo-twin-text-scale';
  var SCALES = ['normal', 'large', 'xlarge'];

  /* ------------------------------------------------------------ text size */
  function applyTextScale(scale) {
    if (SCALES.indexOf(scale) === -1) scale = 'normal';
    if (scale === 'normal') {
      document.documentElement.removeAttribute('data-text-scale');
    } else {
      document.documentElement.setAttribute('data-text-scale', scale);
    }
    var buttons = document.querySelectorAll('[data-text-scale]');
    for (var i = 0; i < buttons.length; i++) {
      var isActive = buttons[i].getAttribute('data-text-scale') === scale;
      buttons[i].setAttribute('aria-pressed', isActive ? 'true' : 'false');
    }
    return scale;
  }

  function initTextScale() {
    var buttons = document.querySelectorAll('[data-text-scale]');
    if (!buttons.length) return;

    var stored = null;
    try { stored = window.localStorage.getItem(STORAGE_KEY); } catch (e) { /* private mode */ }
    applyTextScale(stored || 'normal');

    for (var i = 0; i < buttons.length; i++) {
      (function (button) {
        button.addEventListener('click', function () {
          var applied = applyTextScale(button.getAttribute('data-text-scale'));
          try { window.localStorage.setItem(STORAGE_KEY, applied); } catch (e) { /* ignore */ }
          announce('Text size set to ' + button.textContent.trim() + '.');
        });
      })(buttons[i]);
    }

    // Announce the restored preference to assistive tech on load.
    if (stored && stored !== 'normal') {
      announce('Text size preference ' + stored + ' restored.');
    }
  }

  /* ------------------------------------------------- polite live announcer */
  var liveRegion = null;
  function announce(message) {
    if (!message) return;
    if (!liveRegion) {
      liveRegion = document.createElement('p');
      liveRegion.setAttribute('aria-live', 'polite');
      liveRegion.setAttribute('role', 'status');
      liveRegion.className = 'visually-hidden';
      document.body.appendChild(liveRegion);
    }
    liveRegion.textContent = message;
  }

  /* ------------------------------------------------------------ navigation */
  function initNav() {
    var toggle = document.querySelector('.nav-toggle');
    var links = document.getElementById('site-links');
    if (!toggle || !links) return;

    function setOpen(open) {
      links.classList.toggle('is-open', open);
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    }

    toggle.addEventListener('click', function () {
      setOpen(links.className.indexOf('is-open') === -1);
    });

    // Escape closes the menu and returns focus to the control that opened it.
    document.addEventListener('keydown', function (event) {
      if (event.key !== 'Escape' && event.key !== 'Esc') return;
      if (links.className.indexOf('is-open') === -1) return;
      setOpen(false);
      toggle.focus();
    });

    // A click outside the header dismisses the open menu.
    document.addEventListener('click', function (event) {
      if (links.className.indexOf('is-open') === -1) return;
      if (toggle.contains(event.target) || links.contains(event.target)) return;
      setOpen(false);
    });

    // Leaving the mobile breakpoint resets the toggle so a later resize is clean.
    if (window.matchMedia) {
      var wide = window.matchMedia('(min-width: 981px)');
      var onChange = function (event) { if (event.matches) setOpen(false); };
      if (wide.addEventListener) wide.addEventListener('change', onChange);
      else if (wide.addListener) wide.addListener(onChange);
    }
  }

  /* ------------------------------------------------------------- scroll spy */
  function initScrollSpy() {
    var sections = document.querySelectorAll('main section[id]');
    var navLinks = document.querySelectorAll('.nav-links a[href^="#"]');
    if (!sections.length || !navLinks.length) return;

    var byId = {};
    for (var i = 0; i < navLinks.length; i++) {
      byId[navLinks[i].getAttribute('href').slice(1)] = navLinks[i];
    }

    function clear() {
      for (var id in byId) {
        if (Object.prototype.hasOwnProperty.call(byId, id)) {
          byId[id].removeAttribute('aria-current');
        }
      }
    }

    function setCurrent(id) {
      clear();
      if (byId[id]) byId[id].setAttribute('aria-current', 'true');
    }

    if (!('IntersectionObserver' in window)) return;

    var visible = {};
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        visible[entry.target.id] = entry.isIntersecting;
      });
      // Pick the topmost section currently intersecting the viewport band.
      var best = null;
      for (var i = 0; i < sections.length; i++) {
        if (visible[sections[i].id]) { best = sections[i].id; break; }
      }
      if (best) setCurrent(best);
    }, { rootMargin: '-20% 0px -70% 0px', threshold: 0 });

    for (var j = 0; j < sections.length; j++) observer.observe(sections[j]);
  }

  /* --------------------------------------------------------- scroll reveal */
  function initReveal() {
    var targets = document.querySelectorAll(
      '.card, .tech-card, .app-card, .flow-step, .timeline-item'
    );
    if (!targets.length) return;

    function revealAll() {
      for (var i = 0; i < targets.length; i++) {
        targets[i].classList.add('is-revealed');
      }
    }

    // Reduced motion, or no observer support: show everything, no animation.
    if (reduceMotion.matches || !('IntersectionObserver' in window)) {
      revealAll();
      return;
    }

    document.documentElement.classList.add('has-reveal');

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-revealed');
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.05, rootMargin: '0px 0px -5% 0px' });

    for (var i = 0; i < targets.length; i++) observer.observe(targets[i]);

    // Safety net: if anything goes wrong, unhide the page rather than trap it.
    window.setTimeout(revealAll, 2500);

    // Honour a mid-session switch to "reduce motion".
    if (reduceMotion.addEventListener) {
      reduceMotion.addEventListener('change', function (event) {
        if (event.matches) {
          revealAll();
          document.documentElement.classList.remove('has-reveal');
        }
      });
    }
  }

  /* ----------------------------------------------------------------- boot */
  function boot() {
    initTextScale();
    initNav();
    initScrollSpy();
    initReveal();

    // Scientific integrity note, kept out of the rendered page.
    if (window.console && window.console.log) {
      window.console.log(
        'ENDO-TWIN NEXUS — research prototype, not a medical device. ' +
        'MEASURED / CLINICALLY_ENTERED / IMAGE_DERIVED / MODEL_INFERRED / DEMO_DATA / UNKNOWN.'
      );
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
