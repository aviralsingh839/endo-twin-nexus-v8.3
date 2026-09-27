/* ============================================================
   ENDO-TWIN NEXUS — dependency-free SVG chart toolkit
   sparkline · multi-line · area · donut gauge · rings · bars ·
   radar · heatmap · scatter · waveform
   ============================================================ */
const Chart = (() => {
  let uidc = 0;
  const nid = () => 'cg' + (++uidc);

  const norm = (vals, min, max) => vals.map(v => (max === min ? 0.5 : (v - min) / (max - min)));

  function path(points, smooth = true) {
    if (!points.length) return '';
    if (!smooth || points.length < 3) return 'M' + points.map(p => `${p[0]},${p[1]}`).join('L');
    let d = `M${points[0][0]},${points[0][1]}`;
    for (let i = 0; i < points.length - 1; i++) {
      const p0 = points[i], p1 = points[i + 1];
      const cx = (p0[0] + p1[0]) / 2;
      d += ` C${cx},${p0[1]} ${cx},${p1[1]} ${p1[0]},${p1[1]}`;
    }
    return d;
  }

  /* ------------------------------ sparkline ------------------------------ */
  function spark(values, color, w = 66, h = 30, opts = {}) {
    const min = Math.min(...values), max = Math.max(...values);
    const n = norm(values, min, max);
    const pts = n.map((v, i) => [i * (w / (n.length - 1 || 1)), h - 3 - v * (h - 8)]);
    const id = nid();
    const fill = opts.fill !== false;
    return `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">
      <defs><linearGradient id="${id}" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="${color}" stop-opacity=".45"/>
        <stop offset="100%" stop-color="${color}" stop-opacity="0"/>
      </linearGradient></defs>
      ${fill ? `<path d="${path(pts)} L${w},${h} L0,${h} Z" fill="url(#${id})"/>` : ''}
      <path d="${path(pts)}" fill="none" stroke="${color}" stroke-width="1.8" stroke-linecap="round"/>
    </svg>`;
  }

  /* ---------------------------- multi-line chart --------------------------- */
  /* series: [{name, color, data:[..], hidden}] */
  function lines(series, opts = {}) {
    const w = opts.w || 720, h = opts.h || 190;
    const pad = Object.assign({ l: 34, r: 10, t: 10, b: 20 }, opts.pad || {});
    const iw = w - pad.l - pad.r, ih = h - pad.t - pad.b;
    const vis = series.filter(s => !s.hidden && s.data && s.data.length);
    if (!vis.length) return `<div class="empty">No series selected</div>`;
    const all = vis.flatMap(s => s.data);
    let min = opts.min != null ? opts.min : Math.min(...all);
    let max = opts.max != null ? opts.max : Math.max(...all);
    if (min === max) { min -= 1; max += 1; }
    const padv = (max - min) * 0.12; min -= padv; max += padv;
    const len = Math.max(...vis.map(s => s.data.length));
    const X = i => pad.l + i * (iw / ((len - 1) || 1));
    const Y = v => pad.t + ih - ((v - min) / (max - min)) * ih;

    const ticks = opts.yticks || 4;
    let grid = '';
    for (let i = 0; i <= ticks; i++) {
      const y = pad.t + (ih / ticks) * i;
      const val = max - ((max - min) / ticks) * i;
      grid += `<line x1="${pad.l}" y1="${y}" x2="${w - pad.r}" y2="${y}" stroke="var(--grid-line)" stroke-width="1"/>`;
      grid += `<text x="${pad.l - 7}" y="${y + 3.5}" text-anchor="end" font-size="9" fill="var(--muted-2)">${Math.round(val)}</text>`;
    }
    const xl = opts.xlabels || [];
    let xax = '';
    xl.forEach((lab, i) => {
      const x = pad.l + (iw / ((xl.length - 1) || 1)) * i;
      xax += `<text x="${x}" y="${h - 5}" text-anchor="middle" font-size="9" fill="var(--muted-2)">${lab}</text>`;
    });

    let body = '';
    vis.forEach(s => {
      const pts = s.data.map((v, i) => [X(i), Y(v)]);
      const id = nid();
      if (opts.area) {
        body += `<defs><linearGradient id="${id}" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="${s.color}" stop-opacity=".30"/>
          <stop offset="100%" stop-color="${s.color}" stop-opacity="0"/></linearGradient></defs>
          <path d="${path(pts)} L${X(s.data.length - 1)},${pad.t + ih} L${pad.l},${pad.t + ih} Z" fill="url(#${id})"/>`;
      }
      body += `<path d="${path(pts)}" fill="none" stroke="${s.color}" stroke-width="${s.width || 1.9}"
        stroke-linecap="round" stroke-linejoin="round" ${s.dash ? `stroke-dasharray="${s.dash}"` : ''}/>`;
      if (opts.dots) pts.forEach(p => { body += `<circle cx="${p[0]}" cy="${p[1]}" r="2.6" fill="${s.color}"/>`; });
      if (opts.lastDot) {
        const p = pts[pts.length - 1];
        body += `<circle cx="${p[0]}" cy="${p[1]}" r="3.2" fill="${s.color}"><animate attributeName="r" values="3;5;3" dur="2s" repeatCount="indefinite"/></circle>`;
      }
    });
    return `<svg class="chart" width="100%" viewBox="0 0 ${w} ${h}" style="display:block;height:auto">${grid}${body}${xax}</svg>`;
  }

  /* ------------------------------ donut gauge ----------------------------- */
  function donut(pct, opts = {}) {
    const size = opts.size || 150, sw = opts.stroke || 14;
    const r = (size - sw) / 2 - 2, cx = size / 2, cy = size / 2;
    const circ = 2 * Math.PI * r;
    const id = nid();
    const stops = opts.gradient || ['#22d3ee', '#7c5cff', '#ff4d8d', '#fb923c'];
    const off = circ * (1 - Math.min(100, Math.max(0, pct)) / 100);
    return `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
      <defs><linearGradient id="${id}" x1="0" y1="0" x2="1" y2="1">
        ${stops.map((c, i) => `<stop offset="${(i / (stops.length - 1)) * 100}%" stop-color="${c}"/>`).join('')}
      </linearGradient></defs>
      <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="var(--panel-3)" stroke-width="${sw}"/>
      <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="url(#${id})" stroke-width="${sw}"
        stroke-linecap="round" stroke-dasharray="${circ}" stroke-dashoffset="${circ}"
        transform="rotate(-90 ${cx} ${cy})">
        <animate attributeName="stroke-dashoffset" from="${circ}" to="${off}" dur=".9s" fill="freeze" calcMode="spline" keySplines="0.3 0 0.2 1" keyTimes="0;1"/>
      </circle>
      <text x="${cx}" y="${cy + (opts.sub ? 0 : 6)}" text-anchor="middle" font-size="${opts.fs || 30}" font-weight="800" fill="var(--text)">${opts.text != null ? opts.text : pct + '%'}</text>
      ${opts.sub ? `<text x="${cx}" y="${cy + 18}" text-anchor="middle" font-size="10" fill="var(--muted)">${opts.sub}</text>` : ''}
    </svg>`;
  }

  /* ------------------------------ small ring ------------------------------ */
  function ring(pct, color, size = 74, label = '') {
    const sw = 8, r = (size - sw) / 2 - 1, cx = size / 2, circ = 2 * Math.PI * r;
    const off = circ * (1 - pct / 100);
    return `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
      <circle cx="${cx}" cy="${cx}" r="${r}" fill="none" stroke="var(--panel-3)" stroke-width="${sw}"/>
      <circle cx="${cx}" cy="${cx}" r="${r}" fill="none" stroke="${color}" stroke-width="${sw}" stroke-linecap="round"
        stroke-dasharray="${circ}" stroke-dashoffset="${circ}" transform="rotate(-90 ${cx} ${cx})">
        <animate attributeName="stroke-dashoffset" from="${circ}" to="${off}" dur=".8s" fill="freeze"/>
      </circle>
      <text x="${cx}" y="${cx + 5}" text-anchor="middle" font-size="15" font-weight="800" fill="var(--text)">${label || pct + '%'}</text>
    </svg>`;
  }

  /* --------------------------------- bars -------------------------------- */
  function bars(data, opts = {}) {
    const w = opts.w || 320, h = opts.h || 140;
    const pad = { l: 28, r: 8, t: 8, b: 20 };
    const iw = w - pad.l - pad.r, ih = h - pad.t - pad.b;
    const max = opts.max || Math.max(...data.map(d => d.v)) * 1.15 || 1;
    const bw = iw / data.length;
    let out = '';
    for (let i = 0; i <= 3; i++) {
      const y = pad.t + (ih / 3) * i;
      out += `<line x1="${pad.l}" y1="${y}" x2="${w - pad.r}" y2="${y}" stroke="var(--grid-line)"/>
              <text x="${pad.l - 6}" y="${y + 3}" text-anchor="end" font-size="9" fill="var(--muted-2)">${Math.round(max - (max / 3) * i)}</text>`;
    }
    data.forEach((d, i) => {
      const bh = Math.max(2, (d.v / max) * ih);
      const x = pad.l + i * bw + bw * 0.22, y = pad.t + ih - bh;
      out += `<rect x="${x}" y="${y}" width="${bw * 0.56}" height="${bh}" rx="3" fill="${d.color || opts.color || '#7c5cff'}" opacity=".9">
        <animate attributeName="height" from="0" to="${bh}" dur=".6s" fill="freeze"/>
        <animate attributeName="y" from="${pad.t + ih}" to="${y}" dur=".6s" fill="freeze"/></rect>
        <text x="${x + bw * 0.28}" y="${h - 5}" text-anchor="middle" font-size="9" fill="var(--muted-2)">${d.k}</text>`;
    });
    return `<svg width="100%" viewBox="0 0 ${w} ${h}" style="display:block;height:auto">${out}</svg>`;
  }

  /* -------------------------------- radar -------------------------------- */
  function radar(axes, sets, size = 240) {
    const cx = size / 2, cy = size / 2, R = size / 2 - 32;
    const n = axes.length;
    const pt = (i, v) => {
      const a = (Math.PI * 2 * i) / n - Math.PI / 2;
      return [cx + Math.cos(a) * R * v, cy + Math.sin(a) * R * v];
    };
    let out = '';
    for (let g = 1; g <= 4; g++) {
      const p = axes.map((_, i) => pt(i, g / 4));
      out += `<polygon points="${p.map(q => q.join(',')).join(' ')}" fill="none" stroke="var(--grid-line)"/>`;
    }
    axes.forEach((a, i) => {
      const p = pt(i, 1), lp = pt(i, 1.19);
      out += `<line x1="${cx}" y1="${cy}" x2="${p[0]}" y2="${p[1]}" stroke="var(--grid-line)"/>
        <text x="${lp[0]}" y="${lp[1] + 3}" text-anchor="middle" font-size="9" fill="var(--muted)">${a}</text>`;
    });
    sets.forEach(s => {
      const p = s.values.map((v, i) => pt(i, Math.max(0.03, v)));
      out += `<polygon points="${p.map(q => q.join(',')).join(' ')}" fill="${s.color}" fill-opacity=".18" stroke="${s.color}" stroke-width="1.8"/>`;
      p.forEach(q => out += `<circle cx="${q[0]}" cy="${q[1]}" r="2.4" fill="${s.color}"/>`);
    });
    return `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">${out}</svg>`;
  }

  /* ------------------------------- heatmap ------------------------------- */
  function heatmap(rows, cols, values, color = '#7c5cff', cell = 15) {
    const gap = 3, w = cols.length * (cell + gap) + 46, h = rows.length * (cell + gap) + 20;
    let out = '';
    rows.forEach((r, ri) => {
      out += `<text x="0" y="${ri * (cell + gap) + cell - 2}" font-size="9" fill="var(--muted-2)">${r}</text>`;
      cols.forEach((c, ci) => {
        const v = values[ri] ? (values[ri][ci] || 0) : 0;
        out += `<rect x="${42 + ci * (cell + gap)}" y="${ri * (cell + gap)}" width="${cell}" height="${cell}" rx="3"
          fill="${color}" fill-opacity="${0.08 + v * 0.85}"><title>${r} ${c}: ${(v * 100).toFixed(0)}%</title></rect>`;
      });
    });
    cols.forEach((c, ci) => {
      out += `<text x="${42 + ci * (cell + gap) + cell / 2}" y="${rows.length * (cell + gap) + 11}" font-size="8.5" text-anchor="middle" fill="var(--muted-2)">${c}</text>`;
    });
    return `<svg width="100%" viewBox="0 0 ${w} ${h}" style="display:block;height:auto">${out}</svg>`;
  }

  /* ------------------------------- scatter ------------------------------- */
  function scatter(points, opts = {}) {
    const w = opts.w || 320, h = opts.h || 200, pad = { l: 30, r: 10, t: 10, b: 22 };
    const iw = w - pad.l - pad.r, ih = h - pad.t - pad.b;
    const xs = points.map(p => p.x), ys = points.map(p => p.y);
    const xmin = Math.min(...xs), xmax = Math.max(...xs), ymin = Math.min(...ys), ymax = Math.max(...ys);
    const X = v => pad.l + ((v - xmin) / ((xmax - xmin) || 1)) * iw;
    const Y = v => pad.t + ih - ((v - ymin) / ((ymax - ymin) || 1)) * ih;
    let out = '';
    for (let i = 0; i <= 4; i++) {
      const y = pad.t + (ih / 4) * i;
      out += `<line x1="${pad.l}" y1="${y}" x2="${w - pad.r}" y2="${y}" stroke="var(--grid-line)"/>`;
    }
    points.forEach(p => {
      out += `<circle cx="${X(p.x)}" cy="${Y(p.y)}" r="${p.r || 4}" fill="${p.color || '#7c5cff'}" fill-opacity=".8">
        <title>${p.label || ''}</title></circle>`;
    });
    out += `<text x="${w / 2}" y="${h - 4}" text-anchor="middle" font-size="9" fill="var(--muted-2)">${opts.xlabel || ''}</text>`;
    return `<svg width="100%" viewBox="0 0 ${w} ${h}" style="display:block;height:auto">${out}</svg>`;
  }

  /* ------------------------------ waveform ------------------------------- */
  function waveform(seed, color = '#ff4d8d', w = 320, h = 70, beats = 6) {
    const r = U.rng(seed);
    let d = `M0,${h / 2}`;
    const step = w / beats;
    for (let b = 0; b < beats; b++) {
      const x = b * step, amp = (0.75 + r() * 0.35);
      d += ` L${x + step * 0.25},${h / 2}`;
      d += ` L${x + step * 0.32},${h / 2 - 5 * amp}`;
      d += ` L${x + step * 0.40},${h / 2 + 7 * amp}`;
      d += ` L${x + step * 0.47},${h / 2 - 26 * amp}`;
      d += ` L${x + step * 0.54},${h / 2 + 12 * amp}`;
      d += ` L${x + step * 0.62},${h / 2}`;
      d += ` L${x + step * 0.78},${h / 2 - 8 * amp}`;
      d += ` L${x + step},${h / 2}`;
    }
    return `<svg width="100%" viewBox="0 0 ${w} ${h}" style="display:block;height:auto">
      <path d="${d}" fill="none" stroke="${color}" stroke-width="1.6" stroke-linejoin="round"/></svg>`;
  }

  /* --------------------------- horizontal bars ---------------------------- */
  function hbars(items, opts = {}) {
    return `<div style="display:flex;flex-direction:column;gap:9px">` + items.map(it => `
      <div>
        <div class="flex between small" style="margin-bottom:4px">
          <span style="color:var(--text-2)">${U.esc(it.k)}</span>
          <span style="color:var(--muted)">${it.text != null ? U.esc(it.text) : it.v + '%'}</span>
        </div>
        <div class="progress"><span style="width:${Math.min(100, it.v)}%;background:${it.color || 'linear-gradient(90deg,var(--indigo),var(--purple))'}"></span></div>
      </div>`).join('') + `</div>`;
  }

  return { spark, lines, donut, ring, bars, radar, heatmap, scatter, waveform, hbars, path };
})();
