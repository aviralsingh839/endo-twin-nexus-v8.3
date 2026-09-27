/* ============================================================
   ENDO-TWIN NEXUS — utilities, icons, DOM helpers
   ============================================================ */
const U = (() => {

  /* ---------- seeded deterministic RNG (so demo charts are stable) ---------- */
  function rng(seed) {
    let s = 0;
    const str = String(seed);
    for (let i = 0; i < str.length; i++) s = (s * 31 + str.charCodeAt(i)) >>> 0;
    if (!s) s = 42;
    return function () {
      s ^= s << 13; s >>>= 0;
      s ^= s >> 17;
      s ^= s << 5; s >>>= 0;
      return s / 4294967296;
    };
  }

  /** Smooth pseudo-physiological series */
  function series(seed, n, base, amp, drift = 0) {
    const r = rng(seed);
    const out = [];
    let v = base;
    for (let i = 0; i < n; i++) {
      v += (r() - 0.5) * amp * 0.6 + (base + drift * i - v) * 0.12;
      out.push(+(v + Math.sin(i / (4 + (seed.length || 4) % 5)) * amp * 0.25).toFixed(2));
    }
    return out;
  }

  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const rand = (r, a, b) => a + r() * (b - a);
  const pick = (r, arr) => arr[Math.floor(r() * arr.length) % arr.length];
  const round = (v, d = 1) => +Number(v).toFixed(d);
  const sum = a => a.reduce((x, y) => x + y, 0);
  const avg = a => (a.length ? sum(a) / a.length : 0);

  /* ---------- DOM ---------- */
  function el(html) {
    const t = document.createElement('template');
    t.innerHTML = html.trim();
    return t.content.firstElementChild;
  }
  const esc = s => String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  /* ---------- dates ---------- */
  const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const DAYS = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  function fmtDate(d) {
    d = new Date(d);
    return `${DAYS[d.getDay()]}, ${String(d.getDate()).padStart(2,'0')} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`;
  }
  function fmtShort(d) {
    d = new Date(d);
    return `${String(d.getDate()).padStart(2,'0')} ${MONTHS[d.getMonth()]}`;
  }
  function fmtTime(d) {
    d = new Date(d);
    let h = d.getHours(); const m = String(d.getMinutes()).padStart(2, '0');
    const ap = h >= 12 ? 'PM' : 'AM'; h = h % 12 || 12;
    return `${h}:${m} ${ap}`;
  }
  function greeting(d = new Date()) {
    const h = d.getHours();
    if (h < 12) return 'Good Morning';
    if (h < 17) return 'Good Afternoon';
    if (h < 21) return 'Good Evening';
    return 'Good Night';
  }
  function daysAgo(n) { const d = new Date(); d.setDate(d.getDate() - n); return d; }
  function initials(name) {
    return String(name || '?').trim().split(/\s+/).map(w => w[0]).slice(0, 2).join('').toUpperCase();
  }
  function uid(prefix = 'ID') {
    return prefix + '-' + Math.random().toString(36).slice(2, 7).toUpperCase();
  }

  /* ---------- icons (stroke style, 24x24 viewbox) ---------- */
  const P = {
    dashboard: '<rect x="3" y="3" width="7" height="8" rx="2"/><rect x="14" y="3" width="7" height="5" rx="2"/><rect x="14" y="11" width="7" height="10" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/>',
    pulse: '<path d="M3 12h4l2.5-6 3.5 12 2.5-6H21"/>',
    watch: '<rect x="6" y="6" width="12" height="12" rx="4"/><path d="M9 6V3h6v3M9 18v3h6v-3"/>',
    log: '<path d="M5 4h11l3 3v13a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1z"/><path d="M8 11h8M8 15h5"/>',
    calendar: '<rect x="3" y="5" width="18" height="16" rx="3"/><path d="M8 3v4M16 3v4M3 10h18"/>',
    brain: '<path d="M9 4a3 3 0 0 0-3 3 3 3 0 0 0-1 5.8V16a3 3 0 0 0 3 3h1V4z"/><path d="M15 4a3 3 0 0 1 3 3 3 3 0 0 1 1 5.8V16a3 3 0 0 1-3 3h-1V4z"/>',
    twin: '<circle cx="12" cy="8" r="3.4"/><path d="M5.5 20a6.5 6.5 0 0 1 13 0"/><path d="M19 4.5l1.5 1.5L19 7.5M5 4.5L3.5 6 5 7.5"/>',
    predict: '<path d="M3 17l5-6 4 3 5-7"/><path d="M17 7h4v4"/>',
    trends: '<path d="M4 19V5"/><path d="M4 15l5-5 4 4 7-8"/>',
    compare: '<path d="M12 3v18"/><path d="M6 8L3 12l3 4M18 8l3 4-3 4"/>',
    heartbeat: '<path d="M20.8 6.6a5 5 0 0 0-8.8-1.6A5 5 0 0 0 3.2 6.6C1.9 9.6 4 13 12 20c8-7 10.1-10.4 8.8-13.4z"/>',
    leaf: '<path d="M5 19c8 2 14-3 14-13-7-1-13 2-13 8 0 2 .5 3.6 1 4.2"/><path d="M5 19c2-4 5-6 9-8"/>',
    moon: '<path d="M20 14.5A8.5 8.5 0 0 1 9.5 4 8.5 8.5 0 1 0 20 14.5z"/>',
    pill: '<rect x="3.5" y="9" width="17" height="7" rx="3.5" transform="rotate(-45 12 12)"/><path d="M9 9l6 6"/>',
    goal: '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3.4"/><path d="M12 4V2M12 22v-2M4 12H2M22 12h-2"/>',
    report: '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4"/><path d="M9 13h6M9 17h4"/>',
    share: '<circle cx="18" cy="5" r="2.6"/><circle cx="6" cy="12" r="2.6"/><circle cx="18" cy="19" r="2.6"/><path d="M8.4 10.8l7.2-4.2M8.4 13.2l7.2 4.2"/>',
    map: '<path d="M9 4L3 6v14l6-2 6 2 6-2V4l-6 2-6-2z"/><path d="M9 4v14M15 6v14"/>',
    users: '<circle cx="9" cy="8" r="3.2"/><path d="M3 20a6 6 0 0 1 12 0"/><path d="M16 5.5a3 3 0 0 1 0 5.5M17 20a6 6 0 0 0-2.2-4.6"/>',
    book: '<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M4 19a2 2 0 0 1 2-2h13"/>',
    event: '<path d="M12 3l2.5 5.2 5.5.8-4 3.9 1 5.6-5-2.7-5 2.7 1-5.6-4-3.9 5.5-.8z"/>',
    user: '<circle cx="12" cy="8" r="3.6"/><path d="M5 20a7 7 0 0 1 14 0"/>',
    settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 14a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-2.7 1.1V20a2 2 0 1 1-4 0v-.1A1.6 1.6 0 0 0 7.5 18.4l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1A1.6 1.6 0 0 0 4 12.9H4a2 2 0 1 1 0-4h.1A1.6 1.6 0 0 0 5.6 6.2l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1A1.6 1.6 0 0 0 11 4V4a2 2 0 1 1 4 0v.1a1.6 1.6 0 0 0 2.7 1.1l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0 1.1 2.7H22a2 2 0 1 1 0 4h-.1a1.6 1.6 0 0 0-1.5 1z"/>',
    shield: '<path d="M12 3l8 3v6c0 5-3.4 8.3-8 9-4.6-.7-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8v.01"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    edit: '<path d="M4 20h4l10-10-4-4L4 16z"/><path d="M13.5 6.5l4 4"/>',
    trash: '<path d="M4 7h16M10 11v6M14 11v6"/><path d="M6 7l1 13h10l1-13M9 7V4h6v3"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>',
    check: '<path d="M4 12.5l5 5 11-11"/>',
    close: '<path d="M6 6l12 12M18 6L6 18"/>',
    chevR: '<path d="M9 6l6 6-6 6"/>',
    chevL: '<path d="M15 6l-6 6 6 6"/>',
    arrowR: '<path d="M5 12h14M13 6l6 6-6 6"/>',
    arrowUp: '<path d="M12 19V5M6 11l6-6 6 6"/>',
    bell: '<path d="M18 8a6 6 0 1 0-12 0c0 7-2 8-2 8h16s-2-1-2-8"/><path d="M13.7 20a2 2 0 0 1-3.4 0"/>',
    temp: '<path d="M10 14V5a2 2 0 1 1 4 0v9a4 4 0 1 1-4 0z"/>',
    drop: '<path d="M12 3s6 6.5 6 10.5A6 6 0 0 1 6 13.5C6 9.5 12 3 12 3z"/>',
    zap: '<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',
    run: '<circle cx="15" cy="5" r="2"/><path d="M8 21l3-5-3-3 1-5 4 2 3 1"/><path d="M6 12l3-2M17 14l-3-1"/>',
    stethoscope: '<path d="M6 3v5a4 4 0 0 0 8 0V3"/><path d="M6 3H4M14 3h2"/><path d="M10 12v2a5 5 0 0 0 5 5 3 3 0 0 0 3-3v-1"/><circle cx="18" cy="12" r="2"/>',
    hospital: '<path d="M3 21V8l9-5 9 5v13"/><path d="M12 12v5M9.5 14.5h5"/>',
    scan: '<path d="M3 8V5a2 2 0 0 1 2-2h3M21 8V5a2 2 0 0 0-2-2h-3M3 16v3a2 2 0 0 0 2 2h3M21 16v3a2 2 0 0 1-2 2h-3"/><path d="M7 12h10"/>',
    chart: '<path d="M4 20h16"/><rect x="5" y="11" width="3" height="6"/><rect x="10.5" y="7" width="3" height="10"/><rect x="16" y="13" width="3" height="4"/>',
    flask: '<path d="M9 3h6M10 3v6L4.5 18a2 2 0 0 0 1.7 3h11.6a2 2 0 0 0 1.7-3L14 9V3"/><path d="M7.5 15h9"/>',
    db: '<ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
    note: '<path d="M5 4h14v11l-5 5H5z"/><path d="M14 20v-5h5"/><path d="M8 9h8M8 13h4"/>',
    msg: '<path d="M21 12a8 8 0 0 1-8 8H5l-2 2V12a8 8 0 0 1 16 0z"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    audit: '<path d="M5 3h9l5 5v13H5z"/><path d="M14 3v5h5"/><path d="M9 12l2 2 4-4"/>',
    fleet: '<rect x="3" y="5" width="8" height="14" rx="2"/><rect x="13" y="5" width="8" height="8" rx="2"/><path d="M13 17h8"/>',
    money: '<circle cx="12" cy="12" r="9"/><path d="M12 7v10M9.5 9.5h4a1.8 1.8 0 0 1 0 3.6h-3a1.8 1.8 0 0 0 0 3.6h4"/>',
    bulb: '<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-3.5 10.9c.5.4.9 1.2 1 1.9h5c.1-.7.5-1.5 1-1.9A6 6 0 0 0 12 3z"/>',
    export: '<path d="M12 15V3M8 7l4-4 4 4"/><path d="M4 15v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4"/>',
    sun: '<circle cx="12" cy="12" r="4.2"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M19.1 4.9l-1.4 1.4M6.3 17.7l-1.4 1.4"/>',
    wave: '<path d="M2 12c2-6 4-6 6 0s4 6 6 0 4-6 6 0"/>',
    grid: '<rect x="3" y="3" width="8" height="8" rx="2"/><rect x="13" y="3" width="8" height="8" rx="2"/><rect x="3" y="13" width="8" height="8" rx="2"/><rect x="13" y="13" width="8" height="8" rx="2"/>',
    filter: '<path d="M3 5h18l-7 8v6l-4 2v-8z"/>',
    bluetooth: '<path d="M7 7l10 10-5 4V3l5 4L7 17"/>',
    lock: '<rect x="4" y="10" width="16" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
    inbox: '<path d="M3 13h5l1.5 3h5L16 13h5"/><path d="M3 13l2.5-8h13L21 13v6H3z"/>',
    star: '<path d="M12 3l2.7 5.6 6 .9-4.3 4.2 1 6-5.4-2.9L6.6 19.7l1-6L3.3 9.5l6-.9z"/>',
  };
  function icon(name, cls = 'ic', style = '') {
    const p = P[name] || P.info;
    return `<svg class="${cls}" viewBox="0 0 24 24" ${style ? `style="${style}"` : ''}>${p}</svg>`;
  }

  /* ---------- color ---------- */
  const C = {
    pink: '#ff4d8d', rose: '#f43f75', purple: '#7c5cff', indigo: '#5b4bf0', violet: '#a78bfa',
    blue: '#3b82f6', sky: '#38bdf8', cyan: '#22d3ee', teal: '#14b8a6', green: '#34d399',
    lime: '#a3e635', yellow: '#fbbf24', orange: '#fb923c', red: '#f87171', gray: '#8593b5'
  };
  const soft = (hex, a = 0.15) => {
    const h = hex.replace('#', '');
    const n = parseInt(h, 16);
    return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
  };

  function riskTone(score) {
    if (score >= 70) return { label: 'High', cls: 'bad', color: C.red };
    if (score >= 45) return { label: 'Moderate', cls: 'warn', color: C.orange };
    return { label: 'Low', cls: 'good', color: C.green };
  }

  /* ---------- misc ---------- */
  function download(filename, text) {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([text], { type: 'text/plain' }));
    a.download = filename; a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  }

  return { rng, series, clamp, rand, pick, round, sum, avg, el, esc, $, $$, MONTHS, DAYS,
    fmtDate, fmtShort, fmtTime, greeting, daysAgo, initials, uid, icon, P, C, soft, riskTone, download };
})();
