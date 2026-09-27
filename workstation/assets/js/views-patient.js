/* ============================================================
   ENDO-TWIN NEXUS — PATIENT WORKSTATION VIEWS
   ============================================================ */
const PatientViews = (() => {

  /* ------------------------------ navigation ----------------------------- */
  const nav = [
    { items: [{ id: 'dashboard', label: 'Dashboard', icon: 'dashboard' }] },
    { label: 'Monitor', items: [
      { id: 'live', label: 'Live Monitoring', icon: 'pulse' },
      { id: 'wearable', label: 'Wearable Device', icon: 'watch', caret: true },
      { id: 'logger', label: 'Data Logger', icon: 'log' },
      { id: 'cycle', label: 'Cycle & Symptoms', icon: 'calendar', caret: true },
    ]},
    { label: 'Analysis', items: [
      { id: 'risk', label: 'AI Risk Analysis', icon: 'brain', caret: true },
      { id: 'twin', label: 'Hormonal Twin', icon: 'twin' },
      { id: 'prediction', label: 'Cycle Prediction', icon: 'predict' },
      { id: 'trends', label: 'Trends & Insights', icon: 'trends', caret: true },
      { id: 'comparative', label: 'Comparative Analysis', icon: 'compare' },
    ]},
    { label: 'Health Management', items: [
      { id: 'symptoms', label: 'Symptoms Tracker', icon: 'heartbeat', caret: true },
      { id: 'nutrition', label: 'Nutrition & Lifestyle', icon: 'leaf' },
      { id: 'sleep', label: 'Sleep & Stress', icon: 'moon' },
      { id: 'meds', label: 'Medications & Supplements', icon: 'pill' },
      { id: 'goals', label: 'Goals & Plans', icon: 'goal' },
    ]},
    { label: 'Reports', items: [
      { id: 'reports', label: 'Reports & Export', icon: 'report', caret: true },
      { id: 'sharing', label: 'Doctor Sharing', icon: 'share' },
      { id: 'finder', label: 'Clinic & Product Finder', icon: 'map' },
    ]},
    { label: 'Community', items: [
      { id: 'community', label: 'Community', icon: 'users', caret: true },
      { id: 'knowledge', label: 'Knowledge Hub', icon: 'book' },
      { id: 'events', label: 'Events & Awareness', icon: 'event', caret: true },
    ]},
    { label: 'Settings', items: [
      { id: 'profile', label: 'Profile & Preferences', icon: 'user' },
      { id: 'device', label: 'Device Settings', icon: 'settings' },
      { id: 'privacy', label: 'Data & Privacy', icon: 'shield' },
      { id: 'about', label: 'About', icon: 'info' },
    ]},
  ];

  /* ------------------------------ live state ----------------------------- */
  const liveState = { visible: { hr: true, hrv: true, temp: true, gsr: true, steps: true, spo2: true }, window: '10 min' };

  const SERIES_META = [
    { k: 'hr',    n: 'Heart Rate', c: U.C.pink },
    { k: 'hrv',   n: 'HRV',        c: U.C.sky },
    { k: 'temp',  n: 'Skin Temp',  c: U.C.orange },
    { k: 'gsr',   n: 'GSR',        c: U.C.violet },
    { k: 'steps', n: 'Activity',   c: U.C.green },
    { k: 'spo2',  n: 'SpO₂',       c: U.C.cyan },
  ];

  /* --------------------------- synthetic US image ------------------------- */
  function usImage(seed) {
    const r = U.rng(seed);
    let sp = '';
    for (let i = 0; i < 260; i++) {
      const x = 10 + r() * 280, y = 6 + r() * 150;
      sp += `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${(r() * 1.5 + .3).toFixed(1)}" fill="#b9c8e4" opacity="${(r() * .30 + .05).toFixed(2)}"/>`;
    }
    let fol = '';
    for (let i = 0; i < 9; i++) {
      const cx = 90 + r() * 120, cy = 45 + r() * 70, rr = 4 + r() * 7;
      fol += `<circle cx="${cx.toFixed(0)}" cy="${cy.toFixed(0)}" r="${rr.toFixed(0)}" fill="#05070d" stroke="#ff7ab0" stroke-width="1" stroke-dasharray="2 2" opacity=".85"/>`;
    }
    return `<svg viewBox="0 0 300 160" preserveAspectRatio="xMidYMid slice" style="width:100%;height:100%;display:block">
      <defs><radialGradient id="usg" cx="50%" cy="10%" r="95%">
        <stop offset="0%" stop-color="#5d6f92"/><stop offset="45%" stop-color="#2a3550"/><stop offset="100%" stop-color="#05070d"/>
      </radialGradient></defs>
      <rect width="300" height="160" fill="#05070d"/>
      <path d="M150 0 L300 160 L0 160 Z" fill="url(#usg)"/>
      ${sp}${fol}
      <text x="8" y="14" font-size="8" fill="#9fb4d8" font-family="monospace">ETN-USG · RESEARCH READ</text>
      <text x="8" y="153" font-size="7.5" fill="#7e8fb0" font-family="monospace">IMAGE-DERIVED · NOT A DIAGNOSIS</text>
    </svg>`;
  }

  /* ============================== DASHBOARD ============================== */
  function dashboard(p) {
    const q = DemoData.quotes[p.id.charCodeAt(6) % DemoData.quotes.length];
    const tone = U.riskTone(p.risk);

    /* hero */
    const hero = `<div class="hero">
      <div class="hero-main">
        <div>
          <div class="hero-greet">${U.greeting()}, ${p.name.split(' ')[0]}!</div>
          <div class="hero-sub">Your personalized hormonal health dashboard powered by ENDO-TWIN NEXUS</div>
        </div>
        <div class="hero-art">
          <div class="hero-quote">“${q}”</div>
        </div>
      </div>
      <div class="twin-card">
        <div>
          <div class="twin-title">ENDO-TWIN NEXUS</div>
          <div class="twin-sub">Your Digital Hormonal Twin</div>
          <div class="twin-tag">Sense • <b>Model</b> • Predict • Personalize</div>
        </div>
        <div class="twin-face">
          <svg width="66" height="66" viewBox="0 0 64 64" fill="none" stroke="rgba(255,255,255,.85)" stroke-width="1.4">
            <path d="M40 6c8 4 12 12 12 22s-5 18-12 24"/><path d="M24 58c-8-4-12-12-12-22S17 18 24 12"/>
            <circle cx="32" cy="32" r="7"/><path d="M32 6v11M32 47v11M12 32h13M39 32h13"/>
            <circle cx="32" cy="32" r="15" stroke-dasharray="3 4"/>
          </svg>
        </div>
      </div>
    </div>`;

    /* vitals */
    const v = p.vitals;
    const vitals = `<div class="row g-6">
      ${C.vital({ key:'hr',   name: 'Heart Rate',      value: v.hr,    unit: ' bpm',  state: v.hr < 85 ? 'Normal' : 'Elevated', tone: v.hr < 85 ? 'good' : 'warn', color: U.C.pink,   icon: 'heartbeat', series: p.live.hr })}
      ${C.vital({ key:'hrv',  name: 'HRV (RMSSD)',     value: v.hrv,   unit: ' ms',   state: v.hrv > 40 ? 'Good' : 'Low',       tone: v.hrv > 40 ? 'good' : 'warn', color: U.C.sky,    icon: 'pulse',     series: p.live.hrv })}
      ${C.vital({ key:'temp', name: 'Skin Temperature',value: v.temp,  unit: ' °C',   state: v.temp < 34.6 ? 'Normal' : 'Raised',tone: v.temp < 34.6 ? 'good' : 'warn', color: U.C.orange, icon: 'temp',   series: p.live.temp })}
      ${C.vital({ key:'gsr',  name: 'GSR (Stress)',    value: v.gsr,   unit: ' µS',   state: v.gsr < 0.32 ? 'Calm' : 'Aroused', tone: v.gsr < 0.32 ? 'good' : 'warn', color: U.C.violet, icon: 'zap',    series: p.live.gsr })}
      ${C.vital({ key:'steps',name: 'Activity',        value: v.steps.toLocaleString(), unit: ' steps', state: v.steps > 6000 ? 'Active' : 'Light', tone: v.steps > 6000 ? 'good' : 'info', color: U.C.green, icon: 'run', series: p.live.steps })}
      ${C.vital({ key:'spo2', name: 'SpO₂',            value: v.spo2,  unit: ' %',    state: v.spo2 >= 95 ? 'Normal' : 'Low',   tone: v.spo2 >= 95 ? 'good' : 'bad',  color: U.C.cyan,   icon: 'drop',   series: p.live.spo2 })}
    </div>`;

    /* live sensor card */
    const liveCard = C.card({
      title: 'Live Sensor Data',
      right: `<span class="tag good" style="margin:0">● Connected</span>
        <select class="select" data-act="liveWindow">
          ${['5 min', '10 min', '30 min', '1 hour'].map(w => `<option ${liveState.window === w ? 'selected' : ''}>${w}</option>`).join('')}
        </select>
        <button class="icon-btn" style="width:28px;height:28px" data-act="expandLive">${U.icon('grid')}</button>`,
      body: `
        <div class="chips" style="margin-bottom:10px">
          ${SERIES_META.map(s => `<button class="chip ${liveState.visible[s.k] ? 'on' : ''}" data-act="toggleSeries" data-arg="${s.k}">
            <span class="cdot" style="background:${s.c}"></span>${s.n}</button>`).join('')}
        </div>
        <div id="liveChart">${liveChartHTML(p)}</div>
        ${C.statMini([
          { k: 'HR', v: v.hr + ' bpm', icon: 'heartbeat', color: U.C.pink },
          { k: 'HRV', v: v.hrv + ' ms', icon: 'pulse', color: U.C.sky },
          { k: 'Skin Temp', v: v.temp + ' °C', icon: 'temp', color: U.C.orange },
          { k: 'GSR', v: v.gsr + ' µS', icon: 'zap', color: U.C.violet },
          { k: 'Steps', v: v.steps.toLocaleString(), icon: 'run', color: U.C.green },
          { k: 'SpO₂', v: v.spo2 + ' %', icon: 'drop', color: U.C.cyan },
        ])}`,
    });

    /* score */
    const scoreCard = C.card({
      title: 'Hormonal Health Score',
      body: `<div class="score-wrap">
        ${Chart.donut(p.risk, { size: 152, stroke: 15, sub: '' })}
        <div class="score-label" style="color:${tone.color}">${tone.label} Risk</div>
        <div class="score-note">Your current profile shows ${tone.label.toLowerCase()} risk signals for PCOS. Consistent tracking improves accuracy.</div>
        <button class="btn primary sm" data-go="risk">View Detailed Analysis ${U.icon('arrowR', 'ic', 'width:13px;height:13px')}</button>
      </div>`,
    });

    /* cycle */
    const cycleCard = C.card({
      title: 'Cycle Tracker',
      right: `<button class="btn sm ghost" data-act="editCycle">Edit</button>`,
      body: cycleWidget(p),
    });

    /* insights */
    const insightCard = C.card({
      title: 'AI Insights', right: `<span class="beta">Beta</span><span class="card-link" data-go="trends" style="margin-left:8px">See All →</span>`,
      body: DemoData.insights.slice(0, 4).map(i => `
        <div class="insight" style="background:${U.soft(i.color, .10)}">
          <div class="in-ico" style="background:${U.soft(i.color, .18)};color:${i.color}">${U.icon(i.icon)}</div>
          <div class="in-text">${i.text}</div>
        </div>`).join(''),
    });

    /* timeline */
    const timelineCard = C.card({
      title: "Today's Timeline",
      right: `<select class="select"><option>Today</option><option>Yesterday</option><option>This week</option></select>`,
      body: p.timeline.map(t => `<div class="tl-item">
        <div class="tl-ico" style="background:${U.soft(t.color, .16)};color:${t.color}">${U.icon(t.icon)}</div>
        <div class="tl-time">${t.t}</div>
        <div class="tl-title">${t.title}</div>
        <div class="tl-meta">${t.meta}</div>
      </div>`).join(''),
    });

    /* quick actions */
    const qaCard = C.card({
      title: 'Quick Actions',
      right: `<select class="select"><option>Customize</option></select>`,
      body: `<div class="qa-grid">${DemoData.quickActions.map(a => `
        <button class="qa" data-go="${a.go}" style="background:linear-gradient(145deg,${a.c1},${a.c2})">
          <span class="qa-ico" style="background:${U.soft(a.color, .2)};color:${a.color}">${U.icon(a.icon)}</span>${a.k}
        </button>`).join('')}</div>`,
    });

    /* progress */
    const progressCard = C.card({
      title: 'Your Progress',
      right: `<select class="select"><option>Last 30 Days</option><option>Last 7 Days</option><option>Last 90 Days</option></select>`,
      body: `<div class="row g-4" style="gap:8px">
          ${p.goals.map((g, i) => `<div class="mini-ring">
            ${Chart.ring(g.v, [U.C.violet, U.C.orange, U.C.cyan, U.C.pink][i], 78)}
            <div class="mr-label">${g.k}</div></div>`).join('')}
        </div>
        <div style="margin-top:8px">${Chart.lines([
          { name: 'HRV', color: U.C.violet, data: p.trend30.hrv },
          { name: 'Skin Temp', color: U.C.orange, data: p.trend30.temp.map(x => x * 2) },
          { name: 'GSR', color: U.C.pink, data: p.trend30.gsr.map(x => x * 120) },
        ], { h: 96, xlabels: ['1 Sep', '8 Sep', '15 Sep', '22 Sep', '29 Sep'], yticks: 2, pad: { l: 6, r: 6, t: 6, b: 18 } })}</div>
        ${C.legend([{ k: 'HRV', c: U.C.violet }, { k: 'Skin Temp', c: U.C.orange }, { k: 'GSR', c: U.C.pink }])}`,
    });

    /* recent analysis */
    const recentCard = C.card({
      title: 'Recent Analysis', right: `<span class="card-link" data-go="trends">View All →</span>`,
      body: `<div class="chips" style="margin-bottom:8px">
          ${['Risk Trend', 'Hormones', 'Symptoms', 'Lifestyle'].map((t, i) => `<button class="chip ${i === 0 ? 'on' : ''}" data-act="recentTab" data-arg="${i}">${t}</button>`).join('')}
        </div>
        <div id="recentChart">${Chart.lines([{ name: 'Risk %', color: U.C.violet, data: p.trend30.risk.filter((_, i) => i % 3 === 0) }],
          { h: 132, area: true, dots: true, xlabels: ['Jul', 'Aug', 'Sep', 'Oct'], min: 0, max: 100 })}</div>`,
    });

    /* ultrasound */
    const us = p.ultrasound;
    const usCard = C.card({
      title: 'Ultrasound Analysis',
      right: `<span class="tag violet" style="margin:0">◈ AI Powered</span><span class="card-link" data-go="ultrasound" style="margin-left:8px">View All →</span>`,
      body: `<div style="display:grid;grid-template-columns:1.1fr 1fr;gap:12px">
        <div class="us-thumb">${usImage(p.id)}</div>
        <div>
          ${C.kvs([
            { k: 'Follicle Count:', v: us.follicles },
            { k: 'Largest Follicle:', v: us.largest + ' mm' },
            { k: 'Ovarian Volume:', v: us.volume + ' cm³' },
            { k: 'PCOS Pattern:', v: `<span style="color:${us.pattern === 'Possible' ? U.C.orange : us.pattern === 'Indeterminate' ? U.C.yellow : U.C.green}">${us.pattern}</span>` },
          ])}
        </div>
      </div>
      <div class="flex gap-6 mt-10 wrap">
        <button class="btn primary sm" data-act="uploadScan">${U.icon('export', 'ic', 'width:13px;height:13px')} Upload Scan</button>
        <button class="btn sm" data-act="analyseScan">${U.icon('brain', 'ic', 'width:13px;height:13px')} Analyse with AI</button>
        <button class="btn sm" data-go="ultrasound">${U.icon('report', 'ic', 'width:13px;height:13px')} View Report</button>
      </div>`,
    });

    /* reports */
    const reportsCard = C.card({
      title: 'Reports & Export', sub: 'Generate detailed reports',
      body: `<div class="row g-2" style="gap:9px">
        ${C.tile({ title: 'Patient Report', sub: 'PDF', icon: 'report', color: U.C.pink, act: 'genReport', arg: 'patient' })}
        ${C.tile({ title: 'Doctor Report', sub: 'With Analysis', icon: 'stethoscope', color: U.C.green, act: 'genReport', arg: 'doctor' })}
        ${C.tile({ title: 'Data Export', sub: 'CSV / Excel', icon: 'export', color: U.C.sky, act: 'genReport', arg: 'csv' })}
        ${C.tile({ title: 'Share with Doctor', sub: 'Secure Link', icon: 'share', color: U.C.violet, act: 'shareDoctor' })}
      </div>`,
    });

    /* reminders */
    const remCard = C.card({
      title: 'Upcoming Reminders', right: `<span class="card-link" data-go="goals">View All →</span>`,
      body: DemoData.reminders.map(r => `<div class="reminder">
        <div class="rm-ico" style="background:${U.soft(r.color, .16)};color:${r.color}">${U.icon(r.icon, 'ic', 'width:13px;height:13px')}</div>
        <div class="rm-title">${r.title}</div><div class="rm-when">${r.when}</div></div>`).join(''),
    });

    return hero + vitals
      + `<div class="row g-dash-a">${liveCard}${scoreCard}${cycleCard}${insightCard}</div>`
      + `<div class="row g-dash-b">${timelineCard}${qaCard}${progressCard}</div>`
      + `<div class="row g-dash-c">${recentCard}${usCard}${reportsCard}${remCard}</div>`
      + C.disclaimer();
  }

  function liveChartHTML(p) {
    const n = { '5 min': 30, '10 min': 60, '30 min': 60, '1 hour': 60 }[liveState.window] || 60;
    const s = SERIES_META.map(m => ({
      name: m.n, color: m.c, hidden: !liveState.visible[m.k],
      data: (m.k === 'temp' ? p.live.temp.map(x => x * 2.2)
        : m.k === 'gsr' ? p.live.gsr.map(x => x * 150)
        : m.k === 'spo2' ? p.live.spo2.map(x => x * 1.05)
        : p.live[m.k]).slice(-n),
    }));
    const now = new Date();
    const labels = [4, 3, 2, 1, 0].map(k => {
      const d = new Date(now.getTime() - k * 10 * 60000 / 4);
      return U.fmtTime(d).replace(/ (AM|PM)/, '');
    });
    return Chart.lines(s, { h: 188, min: 20, max: 165, xlabels: labels, lastDot: true });
  }

  function cycleWidget(p) {
    const day = p.cycleDay, len = p.cycleLen;
    const ovul = Math.round(len / 2) - 1;
    const toOvul = ovul - day;
    const today = new Date();
    const cells = [];
    for (let i = -3; i <= 3; i++) {
      const d = new Date(today); d.setDate(today.getDate() + i);
      const dd = day + i;
      cells.push({
        n: d.getDate(), today: i === 0,
        fert: dd >= ovul - 2 && dd <= ovul + 1 && i !== 0,
        period: dd <= 5 || dd > len,
      });
    }
    return `<div class="cycle-nav">
        <button class="rbtn" data-act="cycleShift" data-arg="-1">${U.icon('chevL', 'ic', 'width:13px;height:13px')}</button>
        <div><div class="cycle-day">Day ${day} of ${len}</div>
          <div class="cycle-bar"><span style="width:${Math.min(100, (day / len) * 100)}%"></span></div></div>
        <button class="rbtn" data-act="cycleShift" data-arg="1">${U.icon('chevR', 'ic', 'width:13px;height:13px')}</button>
      </div>
      <div class="ovul-box">
        <div class="ob-t">Ovulation Window</div>
        <div class="ob-v">${toOvul > 0 ? `in ${toOvul} day${toOvul > 1 ? 's' : ''}` : toOvul === 0 ? 'today' : `passed ${-toOvul}d ago`}</div>
      </div>
      <div class="cal">
        ${['S','M','T','W','T','F','S'].map(d => `<div class="cal-h">${d}</div>`).join('')}
        ${cells.map(c => `<div class="cal-d ${c.today ? 'today' : c.fert ? 'fert' : c.period ? 'period' : ''}">${c.n}</div>`).join('')}
      </div>
      ${C.legend([{ k: 'Period', c: U.C.rose }, { k: 'Fertile', c: U.C.green }, { k: 'Ovulation', c: U.C.pink }, { k: 'Predicted', c: '#94a3b8' }])}`;
  }

  /* =============================== LIVE =============================== */
  function live(p) {
    return C.pageHead('Live Monitoring', 'Real-time multimodal stream from the ENDO-TWIN wearable — PPG, GSR, skin temperature, IMU.',
      `<div class="seg"><button class="on">Streaming</button><button data-act="pauseStream">Pause</button></div>`)
      + `<div class="row g-2">
        ${C.card({ title: 'PPG waveform', sub: 'MAX30102 · 50 Hz · IR channel', icon: 'wave', iconColor: U.C.pink,
          body: Chart.waveform(p.id + 'w', U.C.pink, 320, 84, 6) + C.statMini([
            { k: 'Perfusion', v: U.round(0.8 + (p.quality * 2), 2) + ' %', icon: 'drop', color: U.C.pink },
            { k: 'Quality', v: (p.quality * 100).toFixed(0) + ' %', icon: 'check', color: U.C.green },
            { k: 'Artifacts', v: Math.round((1 - p.quality) * 40) + ' /min', icon: 'zap', color: U.C.orange }]) })}
        ${C.card({ title: 'Autonomic balance', sub: 'HRV frequency-domain estimate', icon: 'pulse', iconColor: U.C.sky,
          body: Chart.lines([{ name: 'LF', color: U.C.violet, data: p.live.hrv.map(x => x * 1.2) }, { name: 'HF', color: U.C.cyan, data: p.live.hrv.map((x, i) => x * .8 + (i % 5)) }], { h: 108, area: true })
            + C.legend([{ k: 'LF power', c: U.C.violet }, { k: 'HF power', c: U.C.cyan }]) })}
      </div>
      <div class="row g-3">
        ${SERIES_META.slice(0, 6).map(m => C.card({
          title: m.n, sub: 'Live window · last 60 samples',
          body: Chart.lines([{ name: m.n, color: m.c, data: p.live[m.k] }], { h: 110, area: true, lastDot: true }),
        })).join('')}
      </div>
      ${C.card({ title: 'Stream diagnostics', icon: 'settings', body: `<div class="log-box">
        <div><span class="dim">[link]</span> transport=<b>BLE</b> device=${p.device} rssi=-54 dBm</div>
        <div><span class="ok">[ok]</span> packets=18,442 dropped=12 (0.06%) jitter=3.1 ms</div>
        <div><span class="ok">[ok]</span> ppg quality gate = ${(p.quality * 100).toFixed(0)}% (threshold 60%)</div>
        <div><span class="warn">[warn]</span> motion artifact bursts detected: ${Math.round((1 - p.quality) * 14)}</div>
        <div><span class="dim">[prov]</span> HR=MEASURED · HRV=DERIVED · Temp=MEASURED · Activity=DERIVED</div>
      </div>` })}
      ${C.disclaimer()}`;
  }

  /* ============================= WEARABLE ============================= */
  function wearable(p) {
    return C.pageHead('Wearable Device', 'Pairing, firmware, calibration and signal health for your ENDO-TWIN band.',
      `<button class="btn primary" data-act="pairDevice">${U.icon('bluetooth')} Pair new device</button>`)
      + `<div class="row g-3">
        ${C.card({ title: p.device, sub: 'Primary device', icon: 'watch', iconColor: U.C.cyan, body: `
          <div class="flex center gap-14">
            ${Chart.ring(p.battery, p.battery > 40 ? U.C.green : U.C.orange, 86, p.battery + '%')}
            <div style="flex:1">${C.kvs([
              { k: 'Status', v: C.statusTag(p.battery > 0 ? 'Online' : 'Offline') },
              { k: 'Firmware', v: 'v8.7.1' }, { k: 'Last sync', v: p.lastSync },
              { k: 'Link', v: 'BLE · -54 dBm' },
            ])}</div>
          </div>` })}
        ${C.card({ title: 'Sensor suite', icon: 'grid', body: C.kvs([
          { k: 'MAX30102 (PPG / SpO₂)', v: C.statusTag('Online') },
          { k: 'DS18B20 (Skin temp)', v: C.statusTag('Online') },
          { k: 'GSR electrodes', v: C.statusTag('Online') },
          { k: 'MPU6050 (IMU)', v: C.statusTag('Online') },
          { k: 'Analog pulse sensor', v: C.statusTag('Weak link') },
        ]) })}
        ${C.card({ title: 'Signal quality (7 days)', icon: 'chart', body:
          Chart.bars(['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].map((d, i) => ({ k: d, v: Math.round(p.quality * 100 - 10 + (i * 7) % 18), color: U.C.cyan })), { h: 150, max: 100 }) })}
      </div>
      <div class="row g-2">
        ${C.card({ title: 'Calibration', icon: 'settings', body: `
          ${Chart.hbars([
            { k: 'PPG gain', v: 72, text: 'auto' }, { k: 'Temp offset', v: 48, text: '-0.3 °C' },
            { k: 'GSR baseline', v: 61, text: '0.18 µS' }, { k: 'IMU zero-g', v: 88, text: 'calibrated' }])}
          <div class="flex gap-6 mt-14"><button class="btn sm" data-act="recalibrate">Recalibrate</button>
          <button class="btn sm ghost" data-act="firmware">Check firmware</button></div>` })}
        ${C.card({ title: 'Wear compliance', sub: 'Hours per day, last 14 days', icon: 'clock', body:
          Chart.lines([{ name: 'Hours', color: U.C.green, data: U.series(p.id + 'wear', 14, p.adherence / 5, 3) }], { h: 150, area: true, dots: true, min: 0, max: 24 }) })}
      </div>${C.disclaimer()}`;
  }

  /* ============================== LOGGER ============================== */
  function logger(p) {
    const rows = (Store.logs(p.id).length ? Store.logs(p.id) : [
      { when: '12:41 PM', type: 'Symptom', text: 'Mood swing · severity 3' },
      { when: '11:02 AM', type: 'Meal', text: 'Oats + curd, 320 kcal' },
      { when: '09:30 AM', type: 'Medication', text: 'Inositol 2 g taken' },
      { when: '07:15 AM', type: 'Sleep', text: `${p.vitals.sleep} h, 2 awakenings` },
    ]).map(l => ({ cells: [l.when, `<span class="tag info" style="margin:0">${l.type}</span>`, l.text, `<button class="btn sm ghost" data-act="deleteLog" data-arg="${l.when}">${U.icon('trash', 'ic', 'width:13px;height:13px')}</button>`] }));

    return C.pageHead('Data Logger', 'Manual entries merge with sensor streams — every row keeps its provenance label.',
      `<button class="btn primary" data-act="addLog">${U.icon('plus')} New entry</button>`)
      + `<div class="row g-4">
        ${['Sensor samples', 'Manual entries', 'Images', 'Sync queue'].map((k, i) => C.card({
          body: `<div class="card-sub">${k}</div><div class="big">${[ (18442).toLocaleString(), Store.logs(p.id).length + 128, 6, 0][i]}</div>
            <span class="tag ${i === 3 ? 'good' : 'info'}">${i === 3 ? 'All synced' : 'local-first'}</span>` })).join('')}
      </div>
      ${C.card({ title: 'Entry log', icon: 'log', body: C.table(
        [{ t: 'Time', w: '110px' }, { t: 'Type', w: '120px' }, { t: 'Detail' }, { t: '', w: '60px' }], rows) })}
      ${C.card({ title: 'Raw stream tail', icon: 'wave', body: `<div class="log-box">${
        Array.from({ length: 10 }, (_, i) => `<div><span class="dim">${U.fmtTime(new Date(Date.now() - i * 4000))}</span> ppg=${(1800 + i * 13) % 2400} hr=${p.vitals.hr + (i % 3)} temp=${(p.vitals.temp + i * 0.02).toFixed(2)} gsr=${(p.vitals.gsr + i * 0.003).toFixed(3)} ax=${(0.01 * i).toFixed(2)} q=<span class="ok">${(p.quality * 100).toFixed(0)}%</span></div>`).join('')
      }</div>` })}`;
  }

  /* ========================= CYCLE & SYMPTOMS ========================= */
  function cycle(p) {
    const len = p.cycleLen;
    const hist = U.series(p.id + 'cyc', 12, len, 5).map(x => Math.round(x));
    return C.pageHead('Cycle & Symptoms', 'Cycle phases, variability and symptom overlay for the last 12 cycles.',
      `<button class="btn primary" data-act="editCycle">${U.icon('calendar')} Log cycle date</button>`)
      + `<div class="row g-3">
        ${C.card({ title: 'Current cycle', icon: 'calendar', iconColor: U.C.pink, body: cycleWidget(p) })}
        ${C.card({ title: 'Cycle length history', sub: 'Variability is a key research signal', icon: 'trends', body:
          Chart.bars(hist.map((v, i) => ({ k: 'C' + (i + 1), v, color: v > 35 ? U.C.orange : U.C.violet })), { h: 170, max: 50 })
          + C.statMini([
            { k: 'Mean', v: Math.round(U.avg(hist)) + ' d', icon: 'chart', color: U.C.violet },
            { k: 'Std dev', v: U.round(Math.sqrt(U.avg(hist.map(x => Math.pow(x - U.avg(hist), 2)))), 1) + ' d', icon: 'compare', color: U.C.orange },
            { k: 'Longest', v: Math.max(...hist) + ' d', icon: 'arrowUp', color: U.C.red }]) })}
        ${C.card({ title: 'Phase estimate', sub: 'cycle_phase_hmm v0.9.3 · research', icon: 'twin', body:
          Chart.radar(['Menstrual', 'Follicular', 'Ovulatory', 'Luteal', 'Late luteal'],
            [{ color: U.C.pink, values: [0.2, 0.9, 0.7, 0.4, 0.3].map((v, i) => U.clamp(v + (p.cycleDay / len) * (i / 6), 0.05, 1)) }], 220)
          + `<div class="small muted" style="text-align:center">MODEL-INFERRED · low confidence without ≥3 logged cycles</div>` })}
      </div>
      <div class="row g-2">
        ${C.card({ title: 'Symptom overlay', icon: 'heartbeat', iconColor: U.C.pink, body:
          Chart.heatmap(p.symptoms.map(s => s.name), ['W1','W2','W3','W4','W5','W6','W7','W8'],
            p.symptoms.map((s, ri) => Array.from({ length: 8 }, (_, ci) => U.clamp((s.severity / 5) * ((ci + ri) % 4) / 3, 0, 1))), U.C.pink, 17) })}
        ${C.card({ title: 'Logged symptoms', icon: 'note', right: `<button class="btn sm primary" data-act="logSymptom">${U.icon('plus', 'ic', 'width:12px;height:12px')} Log</button>`, body:
          C.table([{ t: 'Symptom' }, { t: 'Severity' }, { t: 'Days' }, { t: 'Trend' }],
            p.symptoms.map(s => ({ cells: [s.name, `${'●'.repeat(s.severity)}<span style="opacity:.25">${'●'.repeat(5 - s.severity)}</span>`, s.days + ' d',
              `<span class="tag ${s.trend === 'up' ? 'bad' : 'good'}" style="margin:0">${s.trend === 'up' ? '▲ rising' : '▼ easing'}</span>`] }))) })}
      </div>${C.disclaimer()}`;
  }

  /* =============================== RISK =============================== */
  function risk(p) {
    const tone = U.riskTone(p.risk);
    return C.pageHead('AI Risk Analysis', 'Model-inferred PCOS research signal with drivers, uncertainty and provenance.',
      `<button class="btn primary" data-act="rerunModel">${U.icon('brain')} Re-run analysis</button>`)
      + `<div class="row g-dash-b">
        ${C.card({ title: 'Composite research score', icon: 'brain', iconColor: U.C.violet, body: `
          <div class="score-wrap">${Chart.donut(p.risk, { size: 176, stroke: 16 })}
            <div class="score-label" style="color:${tone.color}">${tone.label} risk signal</div>
            <div class="score-note">Confidence interval ${Math.max(0, p.risk - 9)}–${Math.min(100, p.risk + 9)} % · model pcos_risk_gbm v2.4.1</div>
          </div>` })}
        ${C.card({ title: 'Signal drivers', sub: 'Relative contribution (SHAP-style, research)', icon: 'bulb', iconColor: U.C.yellow,
          body: Chart.hbars(p.drivers.map(d => ({ k: d.k, v: d.v, color: `linear-gradient(90deg,${U.C.indigo},${U.C.pink})` }))) })}
        ${C.card({ title: 'Risk trajectory', sub: '30-day model output', icon: 'trends',
          body: Chart.lines([{ name: 'Risk', color: U.C.pink, data: p.trend30.risk }], { h: 150, area: true, min: 0, max: 100 })
            + C.statMini([
              { k: '7-day Δ', v: (p.trend30.risk.at(-1) - p.trend30.risk.at(-8) > 0 ? '+' : '') + U.round(p.trend30.risk.at(-1) - p.trend30.risk.at(-8), 1), icon: 'compare', color: U.C.orange },
              { k: 'Baseline', v: U.round(U.avg(p.trend30.risk), 0), icon: 'chart', color: U.C.sky },
              { k: 'Quality gate', v: (p.quality * 100).toFixed(0) + '%', icon: 'check', color: U.C.green }]) })}
      </div>
      <div class="row g-2">
        ${C.card({ title: 'Plain-language explanation', icon: 'info', body: `
          <p style="font-size:12.5px;line-height:1.7;color:var(--text-2)">
          Over the last 30 days your cycle length varied by more than 7 days and your HRV stayed
          ${Math.round(12 + p.risk / 6)}% below <b>your own</b> baseline on ${Math.round(p.risk / 6)} nights. Night-time skin temperature
          was slightly elevated around the predicted luteal window. Taken together these produce a
          <b style="color:${tone.color}">${tone.label.toLowerCase()}</b> research signal.
          This is <b>not a diagnosis</b> — it is a pattern description from your own longitudinal data.</p>
          <div class="chips mt-10">
            <span class="chip">OBSERVED: HR, skin temp, activity</span>
            <span class="chip">DERIVED: HRV, sleep stages</span>
            <span class="chip">MODEL-INFERRED: risk score, phase</span>
            <span class="chip">UNKNOWN: serum hormones</span>
          </div>` })}
        ${C.card({ title: 'Uncertainty & limitations', icon: 'shield', iconColor: U.C.orange, body: C.kvs([
          { k: 'PPG-derived HRV vs ECG', v: 'lower accuracy' },
          { k: 'Cycles logged', v: `${Math.max(1, Math.round(p.adherence / 12))} (≥3 recommended)` },
          { k: 'Ultrasound input', v: p.ultrasound.pattern },
          { k: 'Model calibration', v: '0.92 (dev set)' },
          { k: 'External validation', v: 'not performed' },
          { k: 'Regulatory status', v: 'research prototype' },
        ]) })}
      </div>${C.disclaimer()}`;
  }

  /* =============================== TWIN =============================== */
  function twin(p) {
    return C.pageHead('Hormonal Twin', 'Your chrono-metabolic fingerprint — a personal model of daily physiological rhythm.')
      + `<div class="row g-dash-b">
        ${C.card({ title: 'Chrono-metabolic fingerprint', icon: 'twin', iconColor: U.C.violet, body:
          Chart.radar(['HRV', 'Temp rhythm', 'Activity', 'Sleep reg.', 'Stress', 'Cycle stab.'],
            [{ color: U.C.violet, values: [1 - p.risk / 140, 0.5 + p.quality / 3, p.vitals.steps / 9000, p.vitals.sleep / 9, 1 - p.vitals.gsr, 1 - p.risk / 120].map(v => U.clamp(v, .08, 1)) },
             { color: U.C.cyan, values: [.72, .68, .7, .75, .66, .74] }], 250)
          + C.legend([{ k: 'You', c: U.C.violet }, { k: 'Cohort median', c: U.C.cyan }]) })}
        ${C.card({ title: '24-hour rhythm model', sub: 'Circadian phase estimate', icon: 'clock', body:
          Chart.lines([
            { name: 'Skin temp', color: U.C.orange, data: U.series(p.id + 'c1', 24, 34, .8) },
            { name: 'HRV', color: U.C.sky, data: U.series(p.id + 'c2', 24, 44, 9).map(x => x / 1.4) },
            { name: 'Activity', color: U.C.green, data: U.series(p.id + 'c3', 24, 30, 22) },
          ], { h: 176, area: false, xlabels: ['00', '06', '12', '18', '23'] })
          + C.legend([{ k: 'Skin temp', c: U.C.orange }, { k: 'HRV', c: U.C.sky }, { k: 'Activity', c: U.C.green }]) })}
        ${C.card({ title: 'Twin state', icon: 'grid', body: C.kvs([
          { k: 'Baseline learned from', v: `${Math.round(p.adherence * 1.6)} days` },
          { k: 'Baseline confidence', v: `${(p.quality * 100).toFixed(0)} %` },
          { k: 'Circadian phase shift', v: `${U.round((p.risk - 50) / 25, 1)} h` },
          { k: 'Regularity index', v: U.round(1 - p.risk / 200, 2) },
          { k: 'Deviation state', v: p.risk > 70 ? 'PERSISTENT MULTIMODAL SIGNAL' : p.risk > 45 ? 'EARLY CHANGE SIGNAL' : 'LOW CHANGE SIGNAL' },
          { k: 'Model', v: 'chrono_fingerprint v3.0.0' },
        ]) + `<div class="mt-14">${Chart.hbars([
          { k: 'Autonomic', v: U.clamp(100 - p.risk, 5, 100) }, { k: 'Metabolic', v: U.clamp(95 - p.risk * .8, 5, 100) },
          { k: 'Circadian', v: U.clamp(90 - p.risk * .6, 5, 100) }, { k: 'Reproductive', v: U.clamp(100 - p.risk * 1.05, 5, 100) }])}</div>` })}
      </div>${C.disclaimer()}`;
  }

  /* ============================ PREDICTION ============================ */
  function prediction(p) {
    const next = new Date(); next.setDate(next.getDate() + (p.cycleLen - p.cycleDay));
    return C.pageHead('Cycle Prediction', 'Forward estimates with explicit uncertainty bands. Predictions are not certainties.')
      + `<div class="row g-3">
        ${C.card({ title: 'Next period', icon: 'calendar', iconColor: U.C.rose, body:
          `<div class="big" style="color:${U.C.rose}">${U.fmtShort(next)}</div>
           <div class="small muted">± ${Math.round(2 + p.risk / 25)} days · based on ${Math.max(1, Math.round(p.adherence / 12))} logged cycles</div>
           <div class="mt-10">${Chart.hbars([{ k: 'Prediction confidence', v: U.clamp(100 - p.risk * .7, 10, 96) }])}</div>` })}
        ${C.card({ title: 'Fertile window', icon: 'leaf', iconColor: U.C.green, body:
          `<div class="big" style="color:${U.C.green}">${U.fmtShort(U.daysAgo(-(Math.round(p.cycleLen / 2) - p.cycleDay - 3)))} – ${U.fmtShort(U.daysAgo(-(Math.round(p.cycleLen / 2) - p.cycleDay + 1)))}</div>
           <div class="small muted">Temperature + HRV assisted estimate</div>
           <div class="mt-10">${Chart.hbars([{ k: 'Window confidence', v: U.clamp(90 - p.risk * .6, 10, 92), color: 'linear-gradient(90deg,#10b981,#34d399)' }])}` })}
        ${C.card({ title: 'Symptom forecast', icon: 'bulb', iconColor: U.C.yellow, body:
          Chart.hbars(p.symptoms.slice(0, 4).map(s => ({ k: s.name + ' likely', v: U.clamp(s.severity * 17 + 10, 5, 95), color: 'linear-gradient(90deg,#fbbf24,#fb923c)' }))) })}
      </div>
      ${C.card({ title: '90-day projection', sub: 'Shaded band = uncertainty', icon: 'predict', body:
        Chart.lines([
          { name: 'Predicted cycle length', color: U.C.violet, data: U.series(p.id + 'pr', 12, p.cycleLen, 4) },
          { name: 'Upper', color: U.soft(U.C.violet, .5), dash: '4 4', data: U.series(p.id + 'pr', 12, p.cycleLen, 4).map(v => v + 4) },
          { name: 'Lower', color: U.soft(U.C.violet, .5), dash: '4 4', data: U.series(p.id + 'pr', 12, p.cycleLen, 4).map(v => v - 4) },
        ], { h: 200, xlabels: ['Now', '+30 d', '+60 d', '+90 d'] }) })}
      ${C.disclaimer()}`;
  }

  /* ============================== TRENDS ============================== */
  function trends(p) {
    return C.pageHead('Trends & Insights', 'Longitudinal view across every modality, compared against your personal baseline.',
      `<div class="seg"><button class="on">30 days</button><button>90 days</button><button>1 year</button></div>`)
      + `<div class="row g-2">
        ${C.card({ title: 'Multimodal trend', icon: 'trends', body: Chart.lines([
            { name: 'HR', color: U.C.pink, data: p.trend30.hr },
            { name: 'HRV', color: U.C.sky, data: p.trend30.hrv },
            { name: 'Skin temp ×2', color: U.C.orange, data: p.trend30.temp.map(x => x * 2) },
            { name: 'GSR ×100', color: U.C.violet, data: p.trend30.gsr.map(x => x * 100) },
          ], { h: 230, xlabels: ['30 d ago', '20 d', '10 d', 'today'] })
          + C.legend([{ k: 'HR', c: U.C.pink }, { k: 'HRV', c: U.C.sky }, { k: 'Skin temp', c: U.C.orange }, { k: 'GSR', c: U.C.violet }]) })}
        ${C.card({ title: 'Baseline deviation', sub: 'z-score vs personal baseline', icon: 'compare', body:
          Chart.bars([
            { k: 'HR', v: U.round(Math.abs(p.risk - 50) / 14, 1), color: U.C.pink },
            { k: 'HRV', v: U.round(p.risk / 30, 1), color: U.C.sky },
            { k: 'Temp', v: U.round(p.risk / 45, 1), color: U.C.orange },
            { k: 'GSR', v: U.round(p.risk / 60, 1), color: U.C.violet },
            { k: 'Sleep', v: U.round(p.risk / 40, 1), color: U.C.cyan },
            { k: 'Steps', v: U.round(p.risk / 55, 1), color: U.C.green },
          ], { h: 230, max: 3.5 }) })}
      </div>
      <div class="row g-3">
        ${C.card({ title: 'Sleep duration', icon: 'moon', body: Chart.lines([{ name: 'Sleep h', color: U.C.violet, data: p.trend30.sleep }], { h: 140, area: true, min: 3, max: 10 }) })}
        ${C.card({ title: 'Daily steps', icon: 'run', body: Chart.lines([{ name: 'Steps', color: U.C.green, data: p.trend30.steps }], { h: 140, area: true }) })}
        ${C.card({ title: 'Body weight', icon: 'chart', body: Chart.lines([{ name: 'kg', color: U.C.cyan, data: p.trend30.weight }], { h: 140, area: true }) })}
      </div>
      ${C.card({ title: 'Insight feed', icon: 'bulb', iconColor: U.C.yellow, body: DemoData.insights.map(i => `
        <div class="insight" style="background:${U.soft(i.color, .09)}">
          <div class="in-ico" style="background:${U.soft(i.color, .18)};color:${i.color}">${U.icon(i.icon)}</div>
          <div class="in-text">${i.text}</div></div>`).join('') })}`;
  }

  /* =========================== COMPARATIVE ============================ */
  function comparative(p) {
    const cohort = Store.patients().filter(x => x.id !== p.id).slice(0, 6);
    return C.pageHead('Comparative Analysis', 'You vs. de-identified cohort medians. Comparison never replaces your personal baseline.')
      + `<div class="row g-2">
        ${C.card({ title: 'Where you sit', sub: 'Percentile within cohort (synthetic)', icon: 'compare', body:
          Chart.scatter(cohort.map(c => ({ x: c.age, y: c.risk, r: 6, color: U.soft(U.C.sky, .8), label: c.id }))
            .concat([{ x: p.age, y: p.risk, r: 9, color: U.C.pink, label: 'You' }]), { h: 230, xlabel: 'Age (years) → risk signal (%)' })
          + C.legend([{ k: 'You', c: U.C.pink }, { k: 'Cohort', c: U.C.sky }]) })}
        ${C.card({ title: 'Metric comparison', icon: 'chart', body: C.table(
          [{ t: 'Metric' }, { t: 'You' }, { t: 'Cohort median' }, { t: 'Δ' }],
          [['HR (bpm)', p.vitals.hr, 74], ['HRV (ms)', p.vitals.hrv, 46], ['Sleep (h)', p.vitals.sleep, 7.1],
           ['Steps', p.vitals.steps, 5800], ['Cycle length (d)', p.cycleLen, 29], ['Risk signal (%)', p.risk, 58]]
            .map(r => ({ cells: [r[0], `<b>${typeof r[1] === 'number' ? r[1].toLocaleString() : r[1]}</b>`, r[2].toLocaleString(),
              `<span class="tag ${(+r[1] - +r[2]) > 0 ? 'warn' : 'good'}" style="margin:0">${(+r[1] - +r[2]) > 0 ? '+' : ''}${U.round(+r[1] - +r[2], 1)}</span>`] }))) })}
      </div>
      ${C.card({ title: 'Cohort distribution', icon: 'users', body:
        Chart.bars(Store.patients().map(c => ({ k: c.id.slice(-2), v: c.risk, color: c.id === p.id ? U.C.pink : U.C.indigo })), { h: 180, max: 100 })
        + `<div class="small muted" style="text-align:center;margin-top:6px">Your record is highlighted in pink · all identifiers are synthetic</div>` })}
      ${C.disclaimer()}`;
  }

  /* ============================= SYMPTOMS ============================= */
  function symptoms(p) {
    return C.pageHead('Symptoms Tracker', 'Log what you feel. Symptom logs are OBSERVED data and drive a large part of the model.',
      `<button class="btn primary" data-act="logSymptom">${U.icon('plus')} Log symptom</button>`)
      + `<div class="row g-4">
        ${DemoData.SYMPTOM_POOL.slice(0, 8).map((s, i) => `
          <button class="qa" data-act="quickSymptom" data-arg="${s}" style="background:linear-gradient(145deg,${U.soft([U.C.pink, U.C.violet, U.C.orange, U.C.cyan, U.C.green, U.C.yellow, U.C.sky, U.C.rose][i], .18)},transparent)">
            <span class="qa-ico" style="background:${U.soft([U.C.pink, U.C.violet, U.C.orange, U.C.cyan, U.C.green, U.C.yellow, U.C.sky, U.C.rose][i], .2)};color:${[U.C.pink, U.C.violet, U.C.orange, U.C.cyan, U.C.green, U.C.yellow, U.C.sky, U.C.rose][i]}">${U.icon('plus')}</span>${s}
          </button>`).join('')}
      </div>
      <div class="row g-2">
        ${C.card({ title: 'Active symptoms', icon: 'heartbeat', iconColor: U.C.pink, body: C.table(
          [{ t: 'Symptom' }, { t: 'Severity' }, { t: 'Duration' }, { t: 'Trend' }, { t: '' }],
          p.symptoms.map(s => ({ cells: [s.name, `${s.severity}/5`, s.days + ' days',
            `<span class="tag ${s.trend === 'up' ? 'bad' : 'good'}" style="margin:0">${s.trend === 'up' ? 'rising' : 'easing'}</span>`,
            `<button class="btn sm ghost" data-act="logSymptom">${U.icon('edit', 'ic', 'width:13px;height:13px')}</button>`] }))) })}
        ${C.card({ title: 'Severity over time', icon: 'trends', body:
          Chart.lines(p.symptoms.slice(0, 3).map((s, i) => ({ name: s.name, color: [U.C.pink, U.C.violet, U.C.orange][i], data: U.series(p.id + s.name, 20, s.severity, 1.6) })),
            { h: 190, min: 0, max: 5, dots: true })
          + C.legend(p.symptoms.slice(0, 3).map((s, i) => ({ k: s.name, c: [U.C.pink, U.C.violet, U.C.orange][i] }))) })}
      </div>
      ${C.card({ title: 'Symptom ↔ physiology correlation', sub: 'Research view · correlation is not causation', icon: 'compare', body:
        Chart.heatmap(p.symptoms.map(s => s.name), ['HR', 'HRV', 'Temp', 'GSR', 'Sleep', 'Steps'],
          p.symptoms.map((s, ri) => [0, 1, 2, 3, 4, 5].map(ci => U.clamp(Math.abs(Math.sin((ri + 1) * (ci + 2) * 0.7)) * (s.severity / 5), 0, 1))), U.C.violet, 20) })}`;
  }

  /* ============================= NUTRITION ============================ */
  function nutrition(p) {
    return C.pageHead('Nutrition & Lifestyle', 'Food, movement and routine logs — the levers you can actually control.',
      `<button class="btn primary" data-act="addMeal">${U.icon('plus')} Log meal</button>`)
      + `<div class="row g-4">
        ${[['Calories', Math.round(1650 + p.risk * 4) + ' kcal', 'leaf', U.C.green], ['Protein', Math.round(48 + p.age) + ' g', 'flask', U.C.sky],
           ['Carbs', Math.round(160 + p.risk) + ' g', 'chart', U.C.orange], ['Water', U.round(1.6 + p.adherence / 60, 1) + ' L', 'drop', U.C.cyan]]
          .map(m => C.card({ body: `<div class="flex center gap-10">
            <div class="t-ico" style="background:${U.soft(m[3], .16)};color:${m[3]};width:34px;height:34px;border-radius:11px;display:grid;place-items:center">${U.icon(m[2])}</div>
            <div><div class="card-sub">${m[0]}</div><div class="big" style="font-size:19px">${m[1]}</div></div></div>` })).join('')}
      </div>
      <div class="row g-dash-b">
        ${C.card({ title: 'Macro balance (7 days)', icon: 'chart', body: Chart.bars(
          ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].map((d, i) => ({ k: d, v: Math.round(1500 + ((i * 137 + p.age) % 700)), color: U.C.green })), { h: 180, max: 2600 }) })}
        ${C.card({ title: 'Lifestyle plan', sub: 'Generated from your own trends', icon: 'goal', body: Chart.hbars([
          { k: '30 min brisk walk · 5×/week', v: U.clamp(p.vitals.steps / 80, 5, 100) },
          { k: 'Protein at breakfast', v: U.clamp(p.adherence - 10, 5, 100) },
          { k: 'Sleep window 23:00–07:00', v: U.clamp(p.vitals.sleep * 12, 5, 100) },
          { k: 'Strength training 2×/week', v: U.clamp(p.adherence - 30, 5, 100) },
          { k: 'Limit added sugar', v: U.clamp(100 - p.risk, 5, 100) },
        ]) })}
        ${C.card({ title: 'Today\'s meals', icon: 'log', body: C.table([{ t: 'Time' }, { t: 'Meal' }, { t: 'kcal' }],
          [['08:10', 'Oats + curd + berries', 320], ['11:00', 'Almonds', 150], ['13:40', 'Dal, rice, salad', 520],
           ['17:00', 'Green tea + fruit', 90], ['20:30', 'Roti, paneer, veggies', 560]].map(r => ({ cells: r }))) })}
      </div>`;
  }

  /* ============================== SLEEP =============================== */
  function sleep(p) {
    return C.pageHead('Sleep & Stress', 'Sleep architecture estimates and autonomic stress load from GSR + HRV.')
      + `<div class="row g-dash-b">
        ${C.card({ title: 'Last night', icon: 'moon', iconColor: U.C.violet, body: `
          <div class="flex center gap-14">${Chart.ring(U.clamp(p.vitals.sleep * 12, 5, 100), U.C.violet, 96, p.vitals.sleep + 'h')}
            <div style="flex:1">${C.kvs([
              { k: 'Deep', v: U.round(p.vitals.sleep * .21, 1) + ' h' }, { k: 'REM', v: U.round(p.vitals.sleep * .23, 1) + ' h' },
              { k: 'Light', v: U.round(p.vitals.sleep * .5, 1) + ' h' }, { k: 'Awake', v: Math.round(p.vitals.sleep * 6) + ' min' },
              { k: 'Efficiency', v: Math.round(78 + p.quality * 18) + ' %' }])}</div></div>` })}
        ${C.card({ title: 'Sleep stages', sub: 'DERIVED from PPG + IMU', icon: 'wave', body:
          Chart.lines([{ name: 'Stage', color: U.C.violet, data: U.series(p.id + 'sl', 40, 2.4, 1.6) }], { h: 170, area: true, min: 0, max: 4 })
          + C.legend([{ k: 'Awake 4', c: U.C.pink }, { k: 'REM 3', c: U.C.violet }, { k: 'Light 2', c: U.C.sky }, { k: 'Deep 1', c: U.C.indigo }]) })}
        ${C.card({ title: 'Stress load', sub: 'GSR + HRV composite', icon: 'zap', iconColor: U.C.orange, body:
          Chart.lines([{ name: 'Stress', color: U.C.orange, data: p.live.gsr.map(x => x * 100) }], { h: 170, area: true })
          + C.statMini([{ k: 'Peak', v: U.round(Math.max(...p.live.gsr) * 100, 0), icon: 'arrowUp', color: U.C.red },
            { k: 'Mean', v: U.round(U.avg(p.live.gsr) * 100, 0), icon: 'chart', color: U.C.orange },
            { k: 'Recovery', v: Math.round(100 - p.risk) + '%', icon: 'check', color: U.C.green }]) })}
      </div>
      ${C.card({ title: 'Sleep regularity (30 days)', icon: 'clock', body:
        Chart.heatmap(['Bedtime', 'Wake', 'Duration'], Array.from({ length: 15 }, (_, i) => String(i + 1)),
          [0, 1, 2].map(ri => Array.from({ length: 15 }, (_, ci) => U.clamp(Math.abs(Math.sin((ri + 2) * (ci + 1) * .6)), .05, 1))), U.C.cyan, 18) })}`;
  }

  /* =============================== MEDS =============================== */
  function meds(p) {
    return C.pageHead('Medications & Supplements', 'Logged medication is CLINICALLY ENTERED data — never inferred by the platform.',
      `<button class="btn primary" data-act="addMed">${U.icon('plus')} Add item</button>`)
      + `<div class="row g-2">
        ${C.card({ title: 'Current list', icon: 'pill', iconColor: U.C.orange, body: C.table(
          [{ t: 'Item' }, { t: 'Dose' }, { t: 'Schedule' }, { t: 'Type' }, { t: 'Today' }],
          p.meds.map(m => ({ cells: [`<b>${m.n}</b>`, m.d, m.t, `<span class="tag plain" style="margin:0">${m.k}</span>`,
            m.taken ? `<span class="tag good" style="margin:0">Taken</span>` : `<button class="btn sm" data-act="markTaken" data-arg="${m.n}">Mark taken</button>`] }))) })}
        ${C.card({ title: 'Adherence', sub: 'Last 30 days', icon: 'check', iconColor: U.C.green, body:
          Chart.heatmap(p.meds.map(m => m.n.split(' ')[0]), Array.from({ length: 15 }, (_, i) => String(i + 1)),
            p.meds.map((m, ri) => Array.from({ length: 15 }, (_, ci) => ((ci + ri) % 7 === 0 ? 0.1 : p.adherence / 100))), U.C.green, 18)
          + `<div class="mt-14">${Chart.hbars([{ k: 'Overall adherence', v: p.adherence, color: 'linear-gradient(90deg,#10b981,#34d399)' }])}</div>` })}
      </div>
      ${C.card({ title: 'Interaction & safety notes', icon: 'shield', iconColor: U.C.orange, body: `
        <p class="small muted" style="line-height:1.7">This platform does <b>not</b> provide prescriptions, dosing advice or interaction checking.
        Items listed here are logs you or your clinician entered. Always confirm with your treating doctor.</p>` })}`;
  }

  /* =============================== GOALS ============================== */
  function goals(p) {
    return C.pageHead('Goals & Plans', 'Small, measurable targets generated from your own data.',
      `<button class="btn primary" data-act="addGoal">${U.icon('plus')} New goal</button>`)
      + `<div class="row g-4">
        ${p.goals.map((g, i) => C.card({ body: `<div class="mini-ring">${Chart.ring(g.v, [U.C.violet, U.C.orange, U.C.cyan, U.C.pink][i], 96)}
          <div class="mr-label" style="font-size:12px;color:var(--text)">${g.k}</div>
          <div class="small muted">${g.v >= 80 ? 'On track' : g.v >= 50 ? 'Needs attention' : 'Behind'}</div></div>` })).join('')}
      </div>
      <div class="row g-2">
        ${C.card({ title: 'Active plans', icon: 'goal', body: C.table([{ t: 'Plan' }, { t: 'Target' }, { t: 'Progress' }, { t: 'Ends' }],
          [['Sleep regularity', '≥ 7.5 h, ±30 min window', U.clamp(p.vitals.sleep * 12, 5, 100), '31 Oct'],
           ['Daily movement', '8,000 steps', U.clamp(p.vitals.steps / 80, 5, 100), '31 Oct'],
           ['Cycle logging', 'every cycle day', p.adherence, 'ongoing'],
           ['Stress practice', '10 min × 5/week', U.clamp(100 - p.risk, 5, 100), '15 Nov']]
            .map(r => ({ cells: [`<b>${r[0]}</b>`, r[1], `<div class="progress" style="width:120px"><span style="width:${r[2]}%;background:linear-gradient(90deg,var(--indigo),var(--purple))"></span></div>`, r[3]] }))) })}
        ${C.card({ title: 'Streaks & milestones', icon: 'star', iconColor: U.C.yellow, body: C.kvs([
          { k: 'Logging streak', v: `${Math.round(p.adherence / 3)} days` },
          { k: 'Longest streak', v: `${Math.round(p.adherence / 2)} days` },
          { k: 'Reports generated', v: p.reports.length },
          { k: 'Cycles tracked', v: Math.max(1, Math.round(p.adherence / 12)) },
          { k: 'Badges', v: '🏅 Consistent · 🌙 Sleep hero' },
        ]) })}
      </div>`;
  }

  /* ============================= REPORTS ============================== */
  function reports(p) {
    return C.pageHead('Reports & Export', 'Every report states model version, data quality, confidence and limitations.',
      `<button class="btn primary" data-act="genReport" data-arg="patient">${U.icon('report')} Generate report</button>`)
      + `<div class="row g-4">
        ${C.tile({ title: 'Patient Report', sub: 'PDF · plain language', icon: 'report', color: U.C.pink, act: 'genReport', arg: 'patient' })}
        ${C.tile({ title: 'Doctor Report', sub: 'PDF · full analysis', icon: 'stethoscope', color: U.C.green, act: 'genReport', arg: 'doctor' })}
        ${C.tile({ title: 'Data Export', sub: 'CSV / Excel', icon: 'export', color: U.C.sky, act: 'genReport', arg: 'csv' })}
        ${C.tile({ title: 'Research Bundle', sub: 'JSON + provenance', icon: 'flask', color: U.C.violet, act: 'genReport', arg: 'json' })}
      </div>
      ${C.card({ title: 'Report library', icon: 'report', body: C.table(
        [{ t: 'Report ID' }, { t: 'Title' }, { t: 'Kind' }, { t: 'Date' }, { t: 'Pages' }, { t: '' }],
        p.reports.map(r => ({ cells: [`<span class="mono">${r.id}</span>`, r.title, `<span class="tag info" style="margin:0">${r.kind}</span>`, r.date, r.pages,
          `<div class="row-actions"><button class="btn sm" data-act="viewReport" data-arg="${r.id}">Open</button>
           <button class="btn sm ghost" data-act="genReport" data-arg="csv">Export</button></div>`] }))) })}
      ${C.disclaimer()}`;
  }

  /* ============================== SHARING ============================= */
  function sharing(p) {
    const doc = Store.doctors().find(d => d.id === p.doctorId) || Store.doctors()[0];
    return C.pageHead('Doctor Sharing', 'You choose exactly what leaves your device. Sharing is opt-in and revocable.')
      + `<div class="row g-2">
        ${C.card({ title: 'Your care team', icon: 'stethoscope', iconColor: U.C.green, body:
          Store.doctors().slice(0, 4).map(d => `<div class="tl-item">
            ${C.avatar(d.name)}
            <div><div class="tl-title">${d.name}</div><div class="small muted">${d.specialty} · ${d.clinic}</div></div>
            <div class="tl-meta">${d.id === doc.id ? '<span class="tag good" style="margin:0">Primary</span>' : `<button class="btn sm" data-act="shareDoctor" data-arg="${d.id}">Share</button>`}</div>
          </div>`).join('') })}
        ${C.card({ title: 'Share scope', icon: 'shield', body: `
          ${['Vitals & trends', 'Cycle & symptoms', 'Sleep & stress', 'Ultrasound images', 'Raw sensor data', 'Contact details']
            .map((k, i) => `<label class="kv" style="cursor:pointer"><span class="k">${k}</span>
              <span class="v"><input type="checkbox" ${i < 4 ? 'checked' : ''} data-act="scope"></span></label>`).join('')}
          <button class="btn primary block mt-14" data-act="shareDoctor">${U.icon('share')} Create secure share link</button>
          <div class="small muted mt-6">Links expire after 7 days. Access is logged in the audit trail.</div>` })}
      </div>
      ${C.card({ title: 'Share history', icon: 'audit', body: C.table([{ t: 'When' }, { t: 'With' }, { t: 'Scope' }, { t: 'Status' }],
        [['24 Sep, 10:12', doc.name, 'Vitals, Cycle, Sleep', 'Active'], ['11 Sep, 16:40', 'Dr. Meera Iyer', 'Ultrasound', 'Expired'],
         ['02 Sep, 09:05', doc.name, 'Full record', 'Revoked']].map(r => ({ cells: [r[0], r[1], r[2],
          `<span class="tag ${r[3] === 'Active' ? 'good' : r[3] === 'Expired' ? 'plain' : 'bad'}" style="margin:0">${r[3]}</span>`] }))) })}`;
  }

  /* ============================== FINDER ============================== */
  function finder() {
    return C.pageHead('Clinic & Product Finder', 'Nearby clinics, labs and ENDO-TWIN hardware. Listings are demo data.')
      + `<div class="row g-2">
        ${C.card({ title: 'Nearby care', icon: 'hospital', iconColor: U.C.sky, body: DemoData.clinics.map(c => `
          <div class="tl-item"><div class="tl-ico" style="background:${U.soft(U.C.sky, .15)};color:${U.C.sky}">${U.icon('hospital')}</div>
            <div><div class="tl-title">${c.n}</div><div class="small muted">${c.a} · ${c.k}</div></div>
            <div class="tl-meta">${c.d} · ★ ${c.r}</div></div>`).join('') })}
        ${C.card({ title: 'Hardware & accessories', icon: 'watch', iconColor: U.C.violet, body: DemoData.products.map(pr => `
          <div class="tl-item"><div class="tl-ico" style="background:${U.soft(U.C.violet, .15)};color:${U.C.violet}">${U.icon('watch')}</div>
            <div><div class="tl-title">${pr.n}</div><div class="small muted">${pr.k} · ${pr.s}</div></div>
            <div class="tl-meta">${pr.p}</div></div>`).join('') })}
      </div>`;
  }

  /* ============================ COMMUNITY ============================= */
  function community() {
    return C.pageHead('Community', 'Peer support. Moderated. No medical advice, no product claims.',
      `<button class="btn primary" data-act="newPost">${U.icon('plus')} New post</button>`)
      + `<div class="row g-2">${DemoData.community.map(c => C.card({
        body: `<div class="flex center gap-10">${C.avatar(c.u)}<div><div class="tl-title">${c.t}</div>
            <div class="small muted">${c.u} · ${c.when} ago</div></div></div>
          <p class="small" style="line-height:1.7;color:var(--text-2);margin:10px 0 8px">${c.b}</p>
          <div class="flex gap-10 small muted"><span>♥ ${c.l}</span><span>💬 ${c.c}</span><span>↗ Share</span></div>` })).join('')}</div>`;
  }

  function knowledge() {
    return C.pageHead('Knowledge Hub', 'Reviewed explainers on physiology, signals and the limits of this platform.')
      + `<div class="row g-3">${DemoData.knowledge.map(k => C.card({
        body: `<span class="tag ${k.tag === 'Reviewed' ? 'good' : k.tag === 'Safety' ? 'warn' : 'violet'}" style="margin:0">${k.tag}</span>
          <div class="card-title" style="margin:8px 0 4px;font-size:13.5px">${k.t}</div>
          <div class="small muted">${k.c} · ${k.m}</div>
          <button class="btn sm mt-10" data-act="readArticle" data-arg="${U.esc(k.t)}">Read →</button>` })).join('')}</div>`;
  }

  function events() {
    return C.pageHead('Events & Awareness', 'Webinars, meetups and awareness drives.')
      + `<div class="row g-2">${DemoData.events.map(e => C.card({
        body: `<div class="flex center gap-10">
          <div class="t-ico" style="background:${U.soft(U.C.pink, .16)};color:${U.C.pink};width:38px;height:38px;border-radius:12px;display:grid;place-items:center">${U.icon('event')}</div>
          <div style="flex:1"><div class="tl-title">${e.t}</div><div class="small muted">${e.d} · ${e.p}</div></div>
          <button class="btn sm primary" data-act="rsvp" data-arg="${U.esc(e.t)}">RSVP</button></div>` })).join('')}</div>`;
  }

  /* ============================= SETTINGS ============================= */
  function profile(p) {
    return C.pageHead('Profile & Preferences', 'Your identity stays on this device unless you explicitly share it.',
      `<button class="btn primary" data-act="editPatient" data-arg="${p.id}">${U.icon('edit')} Edit profile</button>`)
      + `<div class="row g-dash-b">
        ${C.card({ body: `<div class="flex center gap-14">${C.avatar(p.name, 'lg')}
          <div><div class="page-title" style="font-size:17px">${p.name}</div>
          <div class="small muted">${p.id} · ${p.age} y · ${p.gender}</div>
          <div class="chips mt-6"><span class="chip">${p.cohort}</span><span class="chip">${p.status}</span></div></div></div>
          <div class="mt-14">${C.kvs([
            { k: 'Email', v: p.email }, { k: 'Phone', v: p.phone }, { k: 'City', v: p.city },
            { k: 'Height / Weight', v: `${p.height} cm · ${p.weight} kg` }, { k: 'BMI', v: p.bmi },
            { k: 'Blood group', v: p.blood }, { k: 'Joined', v: p.joined },
          ])}</div>` })}
        ${C.card({ title: 'Preferences', icon: 'settings', body: settingsRows([
          ['units', 'Units', ['metric', 'imperial']], ['language', 'Language', ['English', 'हिन्दी', 'বাংলা']],
          ['liveStream', 'Live streaming', null], ['notifications', 'Notifications', null], ['autoReport', 'Weekly auto-report', null],
        ]) })}
        ${C.card({ title: 'Clinical summary', icon: 'stethoscope', body: C.kvs([
          { k: 'Primary clinician', v: (Store.doctors().find(d => d.id === p.doctorId) || {}).name || '—' },
          { k: 'Cycle length', v: p.cycleLen + ' days' }, { k: 'Current cycle day', v: p.cycleDay },
          { k: 'Risk signal', v: `<span style="color:${U.riskTone(p.risk).color}">${p.risk}% ${U.riskTone(p.risk).label}</span>` },
          { k: 'Data quality', v: (p.quality * 100).toFixed(0) + '%' }, { k: 'Adherence', v: p.adherence + '%' },
          { k: 'Next visit', v: p.nextVisit },
        ]) })}
      </div>`;
  }

  function settingsRows(rows) {
    const s = Store.state.settings;
    return rows.map(([k, label, options]) => `<div class="kv"><span class="k">${label}</span><span class="v">${
      options ? `<select class="select" data-act="setSetting" data-arg="${k}">${options.map(o => `<option ${s[k] === o ? 'selected' : ''}>${o}</option>`).join('')}</select>`
        : `<input type="checkbox" data-act="setSetting" data-arg="${k}" ${s[k] ? 'checked' : ''}>`}</span></div>`).join('');
  }

  function device(p) {
    return C.pageHead('Device Settings', 'Sampling, streaming and power behaviour of your band.')
      + `<div class="row g-2">
        ${C.card({ title: 'Acquisition', icon: 'settings', body: C.kvs([
          { k: 'PPG sample rate', v: `<select class="select"><option>50 Hz</option><option>100 Hz</option><option>25 Hz</option></select>` },
          { k: 'GSR sample rate', v: `<select class="select"><option>10 Hz</option><option>4 Hz</option></select>` },
          { k: 'Temp interval', v: `<select class="select"><option>30 s</option><option>10 s</option><option>60 s</option></select>` },
          { k: 'IMU', v: `<select class="select"><option>Enabled</option><option>Disabled</option></select>` },
          { k: 'Night mode', v: `<input type="checkbox" checked>` },
        ]) })}
        ${C.card({ title: 'Connectivity & power', icon: 'bluetooth', iconColor: U.C.cyan, body: C.kvs([
          { k: 'Transport', v: 'BLE (preferred) · Wi-Fi fallback' },
          { k: 'Sync interval', v: '5 min' }, { k: 'Battery', v: p.battery + '%' },
          { k: 'Estimated runtime', v: Math.round(p.battery / 3) + ' h' },
          { k: 'Firmware', v: 'v8.7.1 (up to date)' },
        ]) + `<div class="flex gap-6 mt-14"><button class="btn sm" data-act="recalibrate">Run self-test</button>
          <button class="btn sm ghost" data-act="firmware">Update firmware</button></div>` })}
      </div>`;
  }

  function privacy() {
    return C.pageHead('Data & Privacy', 'Local-first by design. SQLite on your device; nothing leaves without consent.')
      + `<div class="row g-2">
        ${C.card({ title: 'Privacy controls', icon: 'shield', iconColor: U.C.green, body: settingsRows([
          ['localOnly', 'Keep all data local only', null], ['shareWithDoctor', 'Allow doctor access', null], ['notifications', 'Notifications', null],
        ]) + `<div class="flex gap-6 mt-14 wrap">
          <button class="btn sm" data-act="genReport" data-arg="json">Export my data</button>
          <button class="btn sm danger" data-act="resetDemo">Erase local demo data</button></div>` })}
        ${C.card({ title: 'What we store', icon: 'db', body: C.kvs([
          { k: 'Database', v: 'SQLite · 18 tables · local' }, { k: 'Cloud upload', v: 'None' },
          { k: 'Identifiers', v: 'Pseudonymous IDs' }, { k: 'Retention', v: 'Until you erase it' },
          { k: 'Encryption at rest', v: 'OS-level' }, { k: 'Audit trail', v: 'Every access logged' },
        ]) })}
      </div>
      ${C.card({ title: 'Provenance model', icon: 'audit', body: `<div class="chips">
        <span class="chip" style="color:var(--green)">MEASURED</span><span class="chip" style="color:var(--sky)">DERIVED</span>
        <span class="chip" style="color:var(--violet)">CLINICALLY ENTERED</span><span class="chip" style="color:var(--orange)">IMAGE-DERIVED</span>
        <span class="chip" style="color:var(--yellow)">MODEL-INFERRED</span><span class="chip">UNKNOWN</span></div>
        <p class="small muted mt-10" style="line-height:1.7">These labels never mix. If a value cannot be traced to a source it is shown as UNKNOWN by design rather than being estimated silently.</p>` })}`;
  }

  function about() {
    return C.pageHead('About ENDO-TWIN NEXUS', 'Platform identity, versions and safety statement.')
      + `<div class="row g-2">
        ${C.card({ title: 'Platform', icon: 'info', body: C.kvs([
          { k: 'Product', v: 'ENDO-TWIN NEXUS' }, { k: 'Version', v: 'V8.7 · Unified Workstation' },
          { k: 'First disease model', v: 'CHRONO-PCOS' }, { k: 'Core', v: 'Sense • Model • Predict • Personalize • Connect' },
          { k: 'Data', v: 'Local-first SQLite' }, { k: 'Build', v: 'Web workstation (this UI)' },
        ]) })}
        ${C.card({ title: 'Safety statement', icon: 'shield', iconColor: U.C.orange, body: `
          <p class="small" style="line-height:1.8;color:var(--text-2)">
          ENDO-TWIN is a general personalized physiological modelling platform. CHRONO-PCOS is the first
          disease-specific module inside it. Outputs are <b>research / risk-screening signals</b>, not diagnoses.
          The system is <b>not a medical device</b>, has <b>not</b> been clinically validated, and must not be used
          to start, stop or change any treatment. Always consult a qualified clinician.</p>` })}
      </div>${C.disclaimer()}`;
  }

  /* ============================ ULTRASOUND ============================ */
  function ultrasound(p) {
    const us = p.ultrasound;
    return C.pageHead('Ultrasound Analysis', 'Research read of pelvic ultrasound. Findings are IMAGE-DERIVED and never diagnostic.',
      `<button class="btn primary" data-act="uploadScan">${U.icon('export')} Upload scan</button>`)
      + `<div class="row g-dash-b">
        ${C.card({ title: 'Latest scan · ' + us.date, icon: 'scan', iconColor: U.C.orange,
          body: `<div class="us-thumb">${usImage(p.id)}</div>
            <div class="flex gap-6 mt-10 wrap"><button class="btn sm primary" data-act="analyseScan">Analyse with AI</button>
            <button class="btn sm">Segmentation overlay</button><button class="btn sm ghost">Compare previous</button></div>` })}
        ${C.card({ title: 'Measurements', icon: 'chart', body: C.kvs([
          { k: 'Follicle count (per ovary)', v: us.follicles }, { k: 'Largest follicle', v: us.largest + ' mm' },
          { k: 'Ovarian volume', v: us.volume + ' cm³' }, { k: 'Stromal echogenicity', v: p.risk > 60 ? 'Increased' : 'Normal' },
          { k: 'Endometrial thickness', v: U.round(6 + p.cycleDay / 4, 1) + ' mm' },
          { k: 'Image quality gate', v: `${(us.quality * 100).toFixed(0)} %` },
          { k: 'PCOS morphology pattern', v: `<span style="color:${us.pattern === 'Possible' ? U.C.orange : U.C.green}">${us.pattern}</span>` },
        ]) })}
        ${C.card({ title: 'Model card', icon: 'flask', iconColor: U.C.violet, body: C.kvs([
          { k: 'Model', v: 'follicle_seg_unet v1.2.2' }, { k: 'Training n', v: '512 images' },
          { k: 'Dice (dev)', v: '0.83' }, { k: 'External validation', v: 'None' },
          { k: 'Output label', v: 'IMAGE-DERIVED' }, { k: 'Clinician review', v: 'Required' },
        ]) + `<div class="mt-14">${Chart.hbars([{ k: 'Segmentation confidence', v: Math.round(us.quality * 100) },
          { k: 'Count reliability', v: Math.round(us.quality * 88) }])}</div>` })}
      </div>${C.disclaimer()}`;
  }

  /* ------------------------------ registry ------------------------------- */
  const pages = { dashboard, live, wearable, logger, cycle, risk, twin, prediction, trends,
    comparative, symptoms, nutrition, sleep, meds, goals, reports, sharing, finder,
    community, knowledge, events, profile, device, privacy, about, ultrasound };

  function render(id) {
    const p = Store.patient();
    const fn = pages[id] || pages.dashboard;
    return fn(p);
  }

  return { nav, render, pages, liveState, liveChartHTML, SERIES_META, usImage, cycleWidget };
})();
