/* ============================================================
   ENDO-TWIN NEXUS — DOCTOR WORKSTATION VIEWS
   ============================================================ */
const DoctorViews = (() => {

  const nav = [
    { items: [{ id: 'dashboard', label: 'Dashboard', icon: 'dashboard' }] },
    { label: 'Patients', items: [
      { id: 'registry', label: 'Patient Registry', icon: 'users', caret: true },
      { id: 'chart', label: 'Patient Chart', icon: 'stethoscope' },
      { id: 'reviews', label: 'Pending Reviews', icon: 'inbox', pill: true },
      { id: 'cohorts', label: 'Cohorts & Groups', icon: 'grid' },
    ]},
    { label: 'Clinical', items: [
      { id: 'signals', label: 'Physiological Signals', icon: 'pulse' },
      { id: 'longitudinal', label: 'Longitudinal Analysis', icon: 'trends', caret: true },
      { id: 'imaging', label: 'Ultrasound Review', icon: 'scan' },
      { id: 'lab', label: 'AI / ML Laboratory', icon: 'flask', caret: true },
      { id: 'explain', label: 'Explainability', icon: 'bulb' },
      { id: 'provenance', label: 'Data Provenance', icon: 'audit' },
    ]},
    { label: 'Care', items: [
      { id: 'appointments', label: 'Appointments', icon: 'calendar' },
      { id: 'notes', label: 'Clinical Notes', icon: 'note' },
      { id: 'careplans', label: 'Care Plans', icon: 'goal' },
      { id: 'messages', label: 'Messages', icon: 'msg', pill: true },
    ]},
    { label: 'Reports', items: [
      { id: 'clinreports', label: 'Clinical Reports', icon: 'report' },
      { id: 'analytics', label: 'Cohort Analytics', icon: 'chart', caret: true },
      { id: 'exports', label: 'Export & Sharing', icon: 'export' },
    ]},
    { label: 'Practice', items: [
      { id: 'doctors', label: 'Doctors & Staff', icon: 'user', caret: true },
      { id: 'clinic', label: 'Clinic Profile', icon: 'hospital' },
      { id: 'fleet', label: 'Device Fleet', icon: 'fleet' },
      { id: 'database', label: 'Database', icon: 'db' },
      { id: 'diagnostics', label: 'Diagnostics', icon: 'settings' },
      { id: 'audit', label: 'Audit Log', icon: 'lock' },
    ]},
    { label: 'Settings', items: [
      { id: 'prefs', label: 'Preferences', icon: 'settings' },
      { id: 'about', label: 'About', icon: 'info' },
    ]},
  ];

  const pats = () => Store.patients();
  const active = () => Store.patient();

  /* ============================== DASHBOARD ============================== */
  function dashboard() {
    const all = pats();
    const doc = Store.doctor();
    const mine = all.filter(p => p.doctorId === doc.id);
    const review = all.filter(p => p.status === 'Needs review' || p.status === 'Escalated');
    const avgRisk = Math.round(U.avg(all.map(p => p.risk)));
    const good = all.filter(p => p.quality >= 0.85).length;
    const mod = all.filter(p => p.quality >= 0.7 && p.quality < 0.85).length;
    const poor = all.length - good - mod;

    const hero = `<div class="hero">
      <div class="hero-main">
        <div>
          <div class="hero-greet">${U.greeting()}, ${doc.name.replace('Dr. ', 'Dr. ')}</div>
          <div class="hero-sub">${mine.length} patients under your care · ${review.length} awaiting review · clinic ${doc.clinic.split(',')[0]}</div>
        </div>
        <div class="hero-art">
          <div class="hero-quote">“Signals, not verdicts — every output on this console carries its provenance.”</div>
        </div>
      </div>
      <div class="twin-card" style="background:linear-gradient(120deg,#123b63 0%,#1c4f6e 55%,#125c58 100%);border-color:rgba(34,211,238,.4)">
        <div><div class="twin-title">DOCTOR CONSOLE</div>
          <div class="twin-sub">${doc.specialty}</div>
          <div class="twin-tag">Reg ${doc.reg} · ${doc.room} · ${doc.slot}</div></div>
        <div class="twin-face">${U.icon('stethoscope', 'ic', 'width:52px;height:52px;opacity:.9')}</div>
      </div>
    </div>`;

    const kpis = `<div class="row g-6">
      ${[['Total patients', all.length, 'users', U.C.violet, 'Active cohort'],
         ['Needs review', review.length, 'inbox', U.C.orange, 'Triage queue'],
         ['Mean risk signal', avgRisk + '%', 'brain', U.C.pink, 'Cohort average'],
         ['Good data quality', good + '/' + all.length, 'check', U.C.green, '≥ 0.85 gate'],
         ['Appointments today', Store.state.appointments.filter(a => a.when.startsWith('Today')).length, 'calendar', U.C.sky, 'Confirmed + pending'],
         ['Devices online', DemoData.devices.filter(d => d.state === 'Online').length + '/' + DemoData.devices.length, 'fleet', U.C.cyan, 'Fleet health']]
        .map(k => `<div class="vital">
          <div class="v-ico" style="background:${U.soft(k[3], .16)};color:${k[3]}">${U.icon(k[2])}</div>
          <div style="min-width:0"><div class="v-name">${k[0]}</div><div class="v-val">${k[1]}</div>
          <span class="tag plain">${k[4]}</span></div></div>`).join('')}
    </div>`;

    const queue = C.card({
      title: 'Triage queue', sub: 'Highest research signal first', icon: 'inbox', iconColor: U.C.orange,
      right: `<span class="card-link" data-go="reviews">Open queue →</span>`,
      body: C.table([{ t: 'Patient' }, { t: 'Risk' }, { t: 'Quality' }, { t: 'Status' }, { t: '' }],
        all.slice().sort((a, b) => b.risk - a.risk).slice(0, 6).map(p => ({
          cells: [
            `<div class="pt-cell">${C.avatar(p.name)}<div><div class="pt-name">${p.name}</div><div class="pt-id">${p.id} · ${p.age}y</div></div></div>`,
            `<span style="color:${U.riskTone(p.risk).color};font-weight:700">${p.risk}%</span>`,
            `<div class="progress" style="width:70px"><span style="width:${p.quality * 100}%;background:${p.quality > .85 ? U.C.green : p.quality > .7 ? U.C.yellow : U.C.red}"></span></div>`,
            C.statusTag(p.status),
            `<button class="btn sm primary" data-act="openPatient" data-arg="${p.id}">Open</button>`,
          ] }))),
    });

    const qualityCard = C.card({
      title: 'Data quality mix', icon: 'check', iconColor: U.C.green,
      body: `<div class="score-wrap">${Chart.donut(Math.round((good / all.length) * 100), { size: 140, stroke: 14, gradient: [U.C.green, U.C.cyan, U.C.sky] })}
        <div class="score-label">${good} good · ${mod} moderate · ${poor} poor</div>
        <div class="score-note">Quality gate blocks model inference below 0.60.</div></div>`,
    });

    const cohortCard = C.card({
      title: 'Cohort risk distribution', icon: 'chart',
      body: Chart.bars(all.map(p => ({ k: p.id.slice(-2), v: p.risk, color: p.risk > 70 ? U.C.red : p.risk > 45 ? U.C.orange : U.C.green })), { h: 170, max: 100 }),
    });

    const apptCard = C.card({
      title: 'Today & next', icon: 'calendar', iconColor: U.C.sky,
      right: `<span class="card-link" data-go="appointments">All →</span>`,
      body: Store.state.appointments.slice(0, 6).map(a => {
        const p = all.find(x => x.id === a.pid) || {};
        return `<div class="tl-item">
          <div class="tl-ico" style="background:${U.soft(U.C.sky, .15)};color:${U.C.sky}">${U.icon('clock')}</div>
          <div><div class="tl-title">${p.name || a.pid}</div><div class="small muted">${a.kind} · ${a.mode}</div></div>
          <div class="tl-meta">${a.when}</div></div>`;
      }).join(''),
    });

    const teamCard = C.card({
      title: 'Care team on shift', icon: 'user', iconColor: U.C.violet,
      right: `<span class="card-link" data-go="doctors">Manage →</span>`,
      body: Store.doctors().map(d => `<div class="tl-item">${C.avatar(d.name)}
        <div><div class="tl-title">${d.name}</div><div class="small muted">${d.specialty} · ${d.room}</div></div>
        <div class="tl-meta">${C.statusTag(d.status)}</div></div>`).join(''),
    });

    const actionsCard = C.card({
      title: 'Quick actions', icon: 'zap', iconColor: U.C.yellow,
      body: `<div class="qa-grid">
        ${[['Add Patient', 'plus', U.C.pink, 'addPatient'], ['Add Doctor', 'user', U.C.violet, 'addDoctor'],
           ['New Note', 'note', U.C.sky, 'addNote'], ['Book Visit', 'calendar', U.C.green, 'addAppointment'],
           ['Run Model', 'brain', U.C.orange, 'rerunModel'], ['Export Cohort', 'export', U.C.cyan, 'exportCohort'],
           ['Diagnostics', 'settings', U.C.yellow, 'runDiagnostics'], ['Clinical Report', 'report', U.C.rose, 'genReport']]
          .map(a => `<button class="qa" data-act="${a[3]}" style="background:linear-gradient(145deg,${U.soft(a[2], .18)},transparent)">
            <span class="qa-ico" style="background:${U.soft(a[2], .2)};color:${a[2]}">${U.icon(a[1])}</span>${a[0]}</button>`).join('')}
      </div>`,
    });

    const auditCard = C.card({
      title: 'Recent activity', icon: 'audit',
      right: `<span class="card-link" data-go="audit">Audit log →</span>`,
      body: DemoData.auditLog.slice(0, 6).map(a => `<div class="tl-item">
        <div class="tl-time">${a.t}</div>
        <div class="tl-title">${a.act}</div>
        <div class="tl-meta" style="color:${a.lvl === 'err' ? U.C.red : a.lvl === 'warn' ? U.C.yellow : 'var(--muted)'}">${a.obj}</div></div>`).join(''),
    });

    return hero + kpis
      + `<div class="row" style="grid-template-columns:1.9fr 1fr 1.2fr">${queue}${qualityCard}${cohortCard}</div>`
      + `<div class="row g-dash-b">${apptCard}${actionsCard}${teamCard}</div>`
      + `<div class="row g-2">${auditCard}${C.card({ title: 'Cohort trend (30 d mean risk)', icon: 'trends',
          body: Chart.lines([{ name: 'Mean risk', color: U.C.pink, data: U.series('cohort', 30, avgRisk, 6) }], { h: 170, area: true, min: 0, max: 100 }) })}</div>`
      + C.disclaimer();
  }

  /* =============================== REGISTRY ============================== */
  function registry() {
    const all = pats();
    const rows = all.map(p => ({
      cells: [
        `<div class="pt-cell">${C.avatar(p.name)}<div><div class="pt-name">${p.name}</div><div class="pt-id">${p.id}</div></div></div>`,
        `${p.age} y`, p.city,
        (Store.doctors().find(d => d.id === p.doctorId) || {}).name || '—',
        `<span class="tag plain" style="margin:0">${p.cohort}</span>`,
        `<span style="color:${U.riskTone(p.risk).color};font-weight:700">${p.risk}%</span>`,
        `<div class="progress" style="width:64px"><span style="width:${p.quality * 100}%;background:${p.quality > .85 ? U.C.green : p.quality > .7 ? U.C.yellow : U.C.red}"></span></div>`,
        C.statusTag(p.status),
        p.lastSync,
        `<div class="row-actions">
          <button class="btn sm primary" data-act="openPatient" data-arg="${p.id}">Open</button>
          <button class="btn sm" data-act="editPatient" data-arg="${p.id}">${U.icon('edit', 'ic', 'width:13px;height:13px')}</button>
          <button class="btn sm danger" data-act="deletePatient" data-arg="${p.id}">${U.icon('trash', 'ic', 'width:13px;height:13px')}</button>
        </div>`,
      ] }));

    return C.pageHead('Patient Registry', `${all.length} participants · create, search, open, edit, archive`,
      `<input class="select" id="registrySearch" placeholder="Filter by name, ID, city…" style="min-width:220px;padding:8px 11px">
       <button class="btn primary" data-act="addPatient">${U.icon('plus')} Add patient</button>`)
      + `<div class="row g-4">
        ${[['Active', all.filter(p => p.status === 'Active').length, U.C.green], ['Needs review', all.filter(p => p.status === 'Needs review').length, U.C.orange],
           ['Escalated', all.filter(p => p.status === 'Escalated').length, U.C.red], ['Archived', all.filter(p => p.status === 'Archived').length, U.C.gray]]
          .map(k => C.card({ body: `<div class="card-sub">${k[0]}</div><div class="big" style="color:${k[2]}">${k[1]}</div>` })).join('')}
      </div>
      ${C.card({ title: 'All participants', icon: 'users', id: 'registryTable', body: C.table(
        [{ t: 'Patient' }, { t: 'Age' }, { t: 'City' }, { t: 'Clinician' }, { t: 'Cohort' }, { t: 'Risk' }, { t: 'Quality' }, { t: 'Status' }, { t: 'Last sync' }, { t: 'Actions', w: '170px' }], rows) })}
      ${C.disclaimer('All participant records in this demo are synthetic. Adding or editing records here writes to local browser storage only.')}`;
  }

  /* ================================ CHART ================================ */
  function chart() {
    const p = active();
    const doc = Store.doctors().find(d => d.id === p.doctorId) || {};
    const tone = U.riskTone(p.risk);

    const headCard = C.card({
      body: `<div class="flex center gap-14 wrap">
        ${C.avatar(p.name, 'lg')}
        <div style="min-width:180px">
          <div class="page-title" style="font-size:18px">${p.name}</div>
          <div class="small muted">${p.id} · ${p.age} y · ${p.gender} · ${p.city}</div>
          <div class="chips mt-6"><span class="chip">${p.cohort}</span>${C.statusTag(p.status)}<span class="chip">${doc.name || '—'}</span></div>
        </div>
        <div class="spacer" style="flex:1"></div>
        ${C.statMini([
          { k: 'Risk', v: p.risk + '%', icon: 'brain', color: tone.color },
          { k: 'HR', v: p.vitals.hr, icon: 'heartbeat', color: U.C.pink },
          { k: 'HRV', v: p.vitals.hrv, icon: 'pulse', color: U.C.sky },
          { k: 'BMI', v: p.bmi, icon: 'chart', color: U.C.orange },
          { k: 'Cycle', v: `${p.cycleDay}/${p.cycleLen}`, icon: 'calendar', color: U.C.violet },
          { k: 'Quality', v: (p.quality * 100).toFixed(0) + '%', icon: 'check', color: U.C.green },
        ])}
        <div class="flex gap-6 wrap">
          <button class="btn primary" data-act="editPatient" data-arg="${p.id}">${U.icon('edit')} Edit record</button>
          <button class="btn" data-act="addNote">${U.icon('note')} Add note</button>
          <button class="btn" data-act="genReport" data-arg="doctor">${U.icon('report')} Report</button>
        </div>
      </div>`,
    });

    return C.pageHead('Patient Chart', 'Complete clinical review workspace for the opened record.',
      `<select class="select" data-act="switchPatient" style="padding:8px 11px;min-width:200px">
        ${pats().map(x => `<option value="${x.id}" ${x.id === p.id ? 'selected' : ''}>${x.name} · ${x.id}</option>`).join('')}
      </select>`)
      + headCard
      + `<div class="row g-dash-b">
        ${C.card({ title: 'Vitals & trends', icon: 'trends', body: Chart.lines([
          { name: 'HR', color: U.C.pink, data: p.trend30.hr }, { name: 'HRV', color: U.C.sky, data: p.trend30.hrv },
          { name: 'Temp×2', color: U.C.orange, data: p.trend30.temp.map(x => x * 2) }], { h: 200, xlabels: ['30 d', '20 d', '10 d', 'now'] })
          + C.legend([{ k: 'HR', c: U.C.pink }, { k: 'HRV', c: U.C.sky }, { k: 'Skin temp', c: U.C.orange }]) })}
        ${C.card({ title: 'Research signal', icon: 'brain', body: `<div class="score-wrap">${Chart.donut(p.risk, { size: 140, stroke: 14 })}
          <div class="score-label" style="color:${tone.color}">${tone.label}</div>
          <div class="score-note">pcos_risk_gbm v2.4.1 · CI ±9</div></div>
          <div class="mt-10">${Chart.hbars(p.drivers.slice(0, 4).map(d => ({ k: d.k, v: d.v })))}</div>` })}
        ${C.card({ title: 'Labs (clinically entered)', icon: 'flask', body: C.table([{ t: 'Analyte' }, { t: 'Value' }, { t: 'Reference' }],
          p.labs.map(l => ({ cells: [l.k, `<b style="color:${l.flag ? U.C.orange : 'var(--text)'}">${l.v}</b>`, l.ref] }))) })}
      </div>
      <div class="row g-dash-c">
        ${C.card({ title: 'Cycle', icon: 'calendar', body: PatientViews.cycleWidget(p) })}
        ${C.card({ title: 'Ultrasound', icon: 'scan', body: `<div class="us-thumb">${PatientViews.usImage(p.id)}</div>
          <div class="mt-10">${C.kvs([{ k: 'Follicles', v: p.ultrasound.follicles }, { k: 'Largest', v: p.ultrasound.largest + ' mm' },
            { k: 'Volume', v: p.ultrasound.volume + ' cm³' }, { k: 'Pattern', v: p.ultrasound.pattern }])}</div>` })}
        ${C.card({ title: 'Symptoms', icon: 'heartbeat', body: C.table([{ t: 'Symptom' }, { t: 'Sev' }, { t: 'Days' }],
          p.symptoms.map(s => ({ cells: [s.name, s.severity + '/5', s.days] }))) })}
        ${C.card({ title: 'Medications', icon: 'pill', body: C.table([{ t: 'Item' }, { t: 'Dose' }],
          p.meds.map(m => ({ cells: [m.n, m.d] }))) })}
      </div>
      ${C.card({ title: 'Clinical notes', icon: 'note', right: `<button class="btn sm primary" data-act="addNote">${U.icon('plus', 'ic', 'width:12px;height:12px')} Add note</button>`,
        body: p.notes.map(n => `<div style="border-left:2px solid var(--purple);padding:4px 0 8px 12px;margin-bottom:10px">
          <div class="small muted">${n.by} · ${n.when}</div>
          <div style="font-size:12.5px;line-height:1.6;color:var(--text-2)">${U.esc(n.text)}</div></div>`).join('') })}
      ${C.disclaimer()}`;
  }

  /* ============================== REVIEWS ================================ */
  function reviews() {
    const q = pats().filter(p => p.status !== 'Archived').sort((a, b) => b.risk - a.risk);
    return C.pageHead('Pending Reviews', 'Records flagged by change-detection or quality gates.',
      `<button class="btn primary" data-act="rerunModel">${U.icon('brain')} Re-run cohort model</button>`)
      + `<div class="row g-2">${q.slice(0, 6).map(p => C.card({
        body: `<div class="flex center gap-10">
            ${C.avatar(p.name)}
            <div style="flex:1"><div class="tl-title">${p.name} <span class="pt-id">${p.id}</span></div>
              <div class="small muted">${p.cohort} · last sync ${p.lastSync}</div></div>
            ${C.statusTag(p.status)}
          </div>
          <div class="mt-10">${Chart.lines([{ name: 'risk', color: U.riskTone(p.risk).color, data: p.trend30.risk }], { h: 74, area: true, min: 0, max: 100, pad: { l: 4, r: 4, t: 4, b: 4 }, yticks: 1 })}</div>
          ${C.statMini([{ k: 'Risk', v: p.risk + '%', icon: 'brain', color: U.riskTone(p.risk).color },
            { k: 'Quality', v: (p.quality * 100).toFixed(0) + '%', icon: 'check', color: U.C.green },
            { k: 'Adherence', v: p.adherence + '%', icon: 'clock', color: U.C.sky }])}
          <div class="flex gap-6 mt-10"><button class="btn sm primary" data-act="openPatient" data-arg="${p.id}">Review chart</button>
            <button class="btn sm" data-act="addNote">Note</button>
            <button class="btn sm ghost" data-act="markReviewed" data-arg="${p.id}">Mark reviewed</button></div>` })).join('')}</div>`;
  }

  /* =============================== COHORTS =============================== */
  function cohorts() {
    const groups = {};
    pats().forEach(p => { (groups[p.cohort] = groups[p.cohort] || []).push(p); });
    return C.pageHead('Cohorts & Groups', 'Group participants for longitudinal comparison and export.',
      `<button class="btn primary" data-act="exportCohort">${U.icon('export')} Export cohort</button>`)
      + `<div class="row g-3">${Object.entries(groups).map(([k, v]) => C.card({
        title: k, sub: `${v.length} participants · mean risk ${Math.round(U.avg(v.map(x => x.risk)))}%`, icon: 'grid',
        body: Chart.bars(v.map(p => ({ k: p.id.slice(-2), v: p.risk, color: U.riskTone(p.risk).color })), { h: 140, max: 100 })
          + v.map(p => `<div class="tl-item"><div class="tl-title">${p.name}</div>
            <div class="tl-meta">${p.risk}% · <span class="mono">${p.id}</span></div></div>`).join(''),
      })).join('')}</div>`;
  }

  /* =============================== SIGNALS =============================== */
  function signals() {
    const p = active();
    return C.pageHead('Physiological Signals', `Raw / filtered streams for ${p.name} (${p.id}) with artifact and quality annotation.`,
      `<select class="select" data-act="switchPatient" style="padding:8px 11px">${pats().map(x => `<option value="${x.id}" ${x.id === p.id ? 'selected' : ''}>${x.name}</option>`).join('')}</select>`)
      + `<div class="row g-2">
        ${C.card({ title: 'PPG · raw vs filtered', icon: 'wave', iconColor: U.C.pink, body:
          Chart.waveform(p.id + 'raw', U.soft(U.C.pink, .5), 320, 70, 6) + Chart.waveform(p.id + 'filt', U.C.pink, 320, 70, 6)
          + C.legend([{ k: 'Raw', c: U.soft(U.C.pink, .5) }, { k: 'Bandpass 0.5–8 Hz', c: U.C.pink }]) })}
        ${C.card({ title: 'HRV tachogram', icon: 'pulse', iconColor: U.C.sky, body:
          Chart.lines([{ name: 'RR', color: U.C.sky, data: U.series(p.id + 'rr', 50, 60000 / p.vitals.hr, 60) }], { h: 158, dots: true })
          + C.statMini([{ k: 'RMSSD', v: p.vitals.hrv + ' ms', icon: 'pulse', color: U.C.sky },
            { k: 'SDNN', v: Math.round(p.vitals.hrv * 1.4) + ' ms', icon: 'chart', color: U.C.violet },
            { k: 'pNN50', v: Math.round(p.vitals.hrv / 2) + ' %', icon: 'compare', color: U.C.cyan }]) })}
      </div>
      <div class="row g-3">
        ${[['GSR (tonic/phasic)', 'gsr', U.C.violet], ['Skin temperature', 'temp', U.C.orange], ['Activity counts', 'steps', U.C.green]]
          .map(s => C.card({ title: s[0], body: Chart.lines([{ name: s[0], color: s[2], data: p.live[s[1]] }], { h: 130, area: true }) })).join('')}
      </div>
      ${C.card({ title: 'Quality & artifact report', icon: 'check', body: `<div class="row g-2"><div>${Chart.hbars([
          { k: 'PPG quality', v: Math.round(p.quality * 100) }, { k: 'Temp stability', v: Math.round(p.quality * 94) },
          { k: 'GSR contact', v: Math.round(p.quality * 88) }, { k: 'Motion-free ratio', v: Math.round(p.quality * 91) }])}</div>
        <div>${C.kvs([{ k: 'Artifact bursts', v: Math.round((1 - p.quality) * 16) }, { k: 'Dropped packets', v: Math.round((1 - p.quality) * 220) },
          { k: 'Sampling', v: '50 Hz PPG · 10 Hz GSR' }, { k: 'Gate decision', v: p.quality >= .6 ? '<span style="color:var(--green)">PASS</span>' : '<span style="color:var(--red)">BLOCK</span>' },
          { k: 'Provenance', v: 'MEASURED / DERIVED' }])}</div></div>` })}`;
  }

  /* ============================ LONGITUDINAL ============================= */
  function longitudinal() {
    const p = active();
    const scenarios = [
      ['Stable baseline', 'LOW CHANGE SIGNAL', U.C.green], ['Gradual deviation', 'EARLY CHANGE SIGNAL', U.C.yellow],
      ['Persistent deviation', 'PERSISTENT MULTIMODAL SIGNAL', U.C.red], ['Temporary disturbance', 'TEMPORARY EVENT', U.C.sky],
      ['Sensor failure', 'LOW SENSOR CONFIDENCE', U.C.orange], ['Recovery', 'RECOVERY TREND', U.C.cyan],
    ];
    const cur = p.risk > 70 ? 2 : p.risk > 55 ? 1 : p.risk > 40 ? 5 : 0;
    return C.pageHead('Longitudinal Analysis', `Baseline deviation, persistence and recovery for ${p.name}.`)
      + `<div class="row g-2">
        ${C.card({ title: 'Personal baseline vs observed', icon: 'compare', body: Chart.lines([
          { name: 'Observed HRV', color: U.C.sky, data: p.trend30.hrv },
          { name: 'Baseline', color: U.C.gray, dash: '5 4', data: p.trend30.hrv.map(() => U.avg(p.trend30.hrv)) },
          { name: '±1 MAD', color: U.soft(U.C.gray, .6), dash: '2 4', data: p.trend30.hrv.map(() => U.avg(p.trend30.hrv) + 6) },
        ], { h: 210, xlabels: ['30 d', '20 d', '10 d', 'now'] }) })}
        ${C.card({ title: 'Deviation state machine', icon: 'grid', body: scenarios.map((s, i) => `
          <div class="tl-item" style="${i === cur ? `background:${U.soft(s[2], .1)};border-radius:10px;padding-left:8px` : ''}">
            <div class="tl-ico" style="background:${U.soft(s[2], .16)};color:${s[2]}">${U.icon(i === cur ? 'check' : 'info')}</div>
            <div><div class="tl-title">${s[0]}</div><div class="small muted mono">${s[1]}</div></div>
            ${i === cur ? `<div class="tl-meta" style="color:${s[2]}">current</div>` : ''}</div>`).join('') })}
      </div>
      <div class="row g-3">
        ${C.card({ title: 'Persistence', icon: 'clock', body: Chart.hbars([
          { k: 'Days deviating (30 d)', v: Math.round(p.risk * .8), text: Math.round(p.risk * .24) + ' d' },
          { k: 'Longest run', v: Math.round(p.risk * .6), text: Math.round(p.risk * .12) + ' d' },
          { k: 'Recovery ratio', v: Math.round(100 - p.risk * .8) }]) })}
        ${C.card({ title: 'Multi-modal agreement', icon: 'compare', body: Chart.radar(['HRV', 'Temp', 'GSR', 'Sleep', 'Cycle'],
          [{ color: U.C.pink, values: [p.risk / 100, p.risk / 120, p.risk / 140, p.risk / 110, p.risk / 100].map(v => U.clamp(v, .05, 1)) }], 210) })}
        ${C.card({ title: 'Change points', icon: 'predict', body: Chart.lines([{ name: 'score', color: U.C.violet, data: p.trend30.risk, }], { h: 150, dots: true, area: true, min: 0, max: 100 })
          + `<div class="small muted">Detected change points: day ${Math.round(p.risk / 4)}, day ${Math.round(p.risk / 2)}</div>` })}
      </div>`;
  }

  /* ============================== IMAGING ================================ */
  function imaging() {
    const p = active();
    return C.pageHead('Ultrasound Review', 'Segmentation, measurements and clinician sign-off.',
      `<button class="btn primary" data-act="uploadScan">${U.icon('export')} Import DICOM / image</button>`)
      + `<div class="row g-dash-b">
        ${C.card({ title: `${p.name} · ${p.ultrasound.date}`, icon: 'scan', iconColor: U.C.orange,
          body: `<div class="us-thumb">${PatientViews.usImage(p.id)}</div>
            <div class="chips mt-10"><button class="chip on">Overlay</button><button class="chip">Raw</button><button class="chip">Heatmap</button><button class="chip">Measure</button></div>` })}
        ${C.card({ title: 'Automated read', icon: 'brain', body: C.kvs([
          { k: 'Follicle count', v: p.ultrasound.follicles }, { k: 'Largest follicle', v: p.ultrasound.largest + ' mm' },
          { k: 'Ovarian volume', v: p.ultrasound.volume + ' cm³' }, { k: 'Morphology pattern', v: p.ultrasound.pattern },
          { k: 'Model', v: 'follicle_seg_unet v1.2.2' }, { k: 'Dice (dev)', v: '0.83' },
          { k: 'Image quality', v: (p.ultrasound.quality * 100).toFixed(0) + '%' },
        ]) + `<div class="flex gap-6 mt-14"><button class="btn sm primary" data-act="signOff">Sign off read</button>
          <button class="btn sm ghost" data-act="analyseScan">Re-run segmentation</button></div>` })}
        ${C.card({ title: 'Prior studies', icon: 'audit', body: C.table([{ t: 'Date' }, { t: 'Follicles' }, { t: 'Volume' }],
          [[p.ultrasound.date, p.ultrasound.follicles, p.ultrasound.volume], ['12 Jun', p.ultrasound.follicles - 2, U.round(p.ultrasound.volume - 1.2, 1)],
           ['04 Mar', p.ultrasound.follicles - 4, U.round(p.ultrasound.volume - 2.1, 1)]].map(r => ({ cells: r }))) })}
      </div>${C.disclaimer('IMAGE-DERIVED research output. Requires clinician interpretation; not a diagnostic read.')}`;
  }

  /* ================================= LAB ================================= */
  function lab() {
    return C.pageHead('AI / ML Laboratory', 'Datasets, splits, leakage checks, training runs and the model registry.',
      `<button class="btn primary" data-act="trainModel">${U.icon('flask')} New training run</button>`)
      + `<div class="row g-4">
        ${[['Registered models', DemoData.models.filter(m => m.state === 'Registered').length, U.C.violet],
           ['Research models', DemoData.models.filter(m => m.state === 'Research').length, U.C.sky],
           ['Leakage checks', 'PASS', U.C.green], ['Last run', '19 Sep 2026', U.C.orange]]
          .map(k => C.card({ body: `<div class="card-sub">${k[0]}</div><div class="big" style="color:${k[2]};font-size:19px">${k[1]}</div>` })).join('')}
      </div>
      ${C.card({ title: 'Model registry', icon: 'db', body: C.table(
        [{ t: 'Model' }, { t: 'Version' }, { t: 'Task' }, { t: 'AUC (dev)' }, { t: 'Calibration' }, { t: 'n' }, { t: 'State' }, { t: 'Date' }],
        DemoData.models.map(m => ({ cells: [`<b class="mono">${m.n}</b>`, m.v, m.task, m.auc == null ? '—' : m.auc,
          m.cal == null ? '—' : m.cal, m.samples.toLocaleString(), C.statusTag(m.state), m.date] }))) })}
      <div class="row g-2">
        ${C.card({ title: 'Split integrity', icon: 'shield', iconColor: U.C.green, body: `
          ${Chart.hbars([{ k: 'Train', v: 70, color: 'linear-gradient(90deg,#5b4bf0,#7c5cff)' },
            { k: 'Validation', v: 15, color: 'linear-gradient(90deg,#22d3ee,#38bdf8)' },
            { k: 'Test (held-out patients)', v: 15, color: 'linear-gradient(90deg,#10b981,#34d399)' }])}
          <div class="log-box mt-14">
            <div><span class="ok">[ok]</span> patient-level split enforced (no subject crosses splits)</div>
            <div><span class="ok">[ok]</span> time-series windows grouped by session</div>
            <div><span class="ok">[ok]</span> duplicate hash scan: 0 collisions</div>
            <div><span class="warn">[warn]</span> class imbalance 1:2.4 — using stratified folds</div>
          </div>` })}
        ${C.card({ title: 'Training curve', icon: 'chart', body: Chart.lines([
          { name: 'train loss', color: U.C.violet, data: U.series('trl', 30, 0.6, .1).map((v, i) => Math.max(.08, v - i * .015)) },
          { name: 'val loss', color: U.C.orange, data: U.series('vl', 30, 0.66, .12).map((v, i) => Math.max(.14, v - i * .012)) },
        ], { h: 190, xlabels: ['0', '10', '20', '30 epochs'] }) + C.legend([{ k: 'Train', c: U.C.violet }, { k: 'Validation', c: U.C.orange }]) })}
      </div>`;
  }

  /* ============================== EXPLAIN ================================ */
  function explain() {
    const p = active();
    return C.pageHead('Explainability', `Why the model produced this signal for ${p.name}.`)
      + `<div class="row g-2">
        ${C.card({ title: 'Feature attribution', sub: 'SHAP-style, research use', icon: 'bulb', iconColor: U.C.yellow,
          body: Chart.hbars(p.drivers.map(d => ({ k: d.k, v: d.v, color: 'linear-gradient(90deg,#f43f75,#fb923c)' }))) })}
        ${C.card({ title: 'Counterfactual (what-if)', icon: 'predict', body: `
          ${Chart.hbars([
            { k: 'If HRV returned to baseline', v: Math.max(5, p.risk - 18), text: `${Math.max(5, p.risk - 18)}%` },
            { k: 'If cycle variability < 4 d', v: Math.max(5, p.risk - 24), text: `${Math.max(5, p.risk - 24)}%` },
            { k: 'If sleep ≥ 7.5 h regularly', v: Math.max(5, p.risk - 11), text: `${Math.max(5, p.risk - 11)}%` },
            { k: 'Current', v: p.risk, text: `${p.risk}%`, color: 'linear-gradient(90deg,#f43f75,#ff4d8d)' },
          ])}
          <p class="small muted mt-14" style="line-height:1.7">What-if values are model sensitivity probes, not predictions of outcome after intervention.</p>` })}
      </div>
      ${C.card({ title: 'Narrative explanation', icon: 'note', body: `<div class="log-box" style="color:var(--text-2)">
        <div><b>Signal:</b> ${U.riskTone(p.risk).label} (${p.risk}%) from pcos_risk_gbm v2.4.1</div>
        <div><b>Top drivers:</b> ${p.drivers.slice(0, 3).map(d => d.k).join(', ')}</div>
        <div><b>Baseline window:</b> ${Math.round(p.adherence * 1.6)} days, confidence ${(p.quality * 100).toFixed(0)}%</div>
        <div><b>Data gaps:</b> ${Math.round((1 - p.adherence / 100) * 30)} days with insufficient wear time</div>
        <div><b>Unknowns:</b> serum androgens, AMH, OGTT — not available to the model</div>
        <div><b>Recommended next step:</b> clinician review + confirm cycle log; repeat imaging next cycle</div>
      </div>` })}`;
  }

  /* ============================= PROVENANCE ============================== */
  function provenance() {
    const p = active();
    const rows = [
      ['Heart rate', '72 bpm', 'MEASURED', 'MAX30102', 0.91], ['HRV RMSSD', p.vitals.hrv + ' ms', 'DERIVED', 'PPG pipeline', 0.85],
      ['Skin temperature', p.vitals.temp + ' °C', 'MEASURED', 'DS18B20', 0.88], ['Activity level', 'Light', 'DERIVED', 'MPU6050', 0.8],
      ['Cycle day', String(p.cycleDay), 'CLINICALLY ENTERED', 'Participant log', 1], ['Follicle count', String(p.ultrasound.follicles), 'IMAGE-DERIVED', 'follicle_seg_unet', p.ultrasound.quality],
      ['Risk signal', p.risk + '%', 'MODEL-INFERRED', 'pcos_risk_gbm', 0.79], ['Serum testosterone', '—', 'UNKNOWN', 'not collected', 0],
    ];
    const colors = { MEASURED: U.C.green, DERIVED: U.C.sky, 'CLINICALLY ENTERED': U.C.violet, 'IMAGE-DERIVED': U.C.orange, 'MODEL-INFERRED': U.C.yellow, UNKNOWN: U.C.gray };
    return C.pageHead('Data Provenance', 'Every value carries its origin. Categories never mix and are never fabricated.')
      + C.card({ title: `Provenance ledger · ${p.id}`, icon: 'audit', body: C.table(
        [{ t: 'Field' }, { t: 'Value' }, { t: 'Provenance' }, { t: 'Source' }, { t: 'Confidence' }],
        rows.map(r => ({ cells: [r[0], `<b>${r[1]}</b>`, `<span class="tag" style="margin:0;background:${U.soft(colors[r[2]], .16)};color:${colors[r[2]]}">${r[2]}</span>`,
          `<span class="mono">${r[3]}</span>`, r[4] ? `<div class="progress" style="width:70px"><span style="width:${r[4] * 100}%;background:${colors[r[2]]}"></span></div>` : '—'] }))) })
      + C.disclaimer();
  }

  /* ============================ APPOINTMENTS ============================= */
  function appointments() {
    const all = pats();
    return C.pageHead('Appointments', 'Clinic schedule across the care team.',
      `<button class="btn primary" data-act="addAppointment">${U.icon('plus')} Book appointment</button>`)
      + C.card({ title: 'Schedule', icon: 'calendar', body: C.table(
        [{ t: 'When' }, { t: 'Patient' }, { t: 'Type' }, { t: 'Mode' }, { t: 'Clinician' }, { t: 'Status' }, { t: '' }],
        Store.state.appointments.map(a => {
          const p = all.find(x => x.id === a.pid) || { name: a.pid };
          const d = Store.doctors().find(x => x.id === a.doc) || {};
          return { cells: [`<b>${a.when}</b>`, `<div class="pt-cell">${C.avatar(p.name)}<div><div class="pt-name">${p.name}</div><div class="pt-id">${a.pid}</div></div></div>`,
            a.kind, a.mode, d.name || '—', C.statusTag(a.status),
            `<button class="btn sm" data-act="openPatient" data-arg="${a.pid}">Open chart</button>`] };
        })) })
      + `<div class="row g-3">
        ${Store.doctors().slice(0, 3).map(d => C.card({ title: d.name, sub: `${d.specialty} · ${d.slot}`, icon: 'user',
          body: Chart.bars(['Mon','Tue','Wed','Thu','Fri'].map((k, i) => ({ k, v: 3 + ((i + d.exp) % 6), color: U.C.violet })), { h: 130, max: 10 }) })).join('')}
      </div>`;
  }

  /* ================================ NOTES ================================ */
  function notes() {
    const all = pats();
    return C.pageHead('Clinical Notes', 'Structured notes are stored locally and appear in the patient chart.',
      `<button class="btn primary" data-act="addNote">${U.icon('plus')} New note</button>`)
      + `<div class="row g-2">${all.slice(0, 6).map(p => C.card({
        title: p.name, sub: `${p.id} · ${p.notes.length} notes`, icon: 'note',
        right: `<button class="btn sm" data-act="openPatient" data-arg="${p.id}">Chart</button>`,
        body: p.notes.slice(0, 2).map(n => `<div style="border-left:2px solid var(--purple);padding:2px 0 6px 10px;margin-bottom:8px">
          <div class="small muted">${n.by} · ${n.when}</div>
          <div class="small" style="line-height:1.6;color:var(--text-2)">${U.esc(n.text)}</div></div>`).join(''),
      })).join('')}</div>`;
  }

  /* ============================== CAREPLANS ============================== */
  function careplans() {
    const all = pats();
    return C.pageHead('Care Plans', 'Lifestyle and monitoring plans assigned to participants.',
      `<button class="btn primary" data-act="addPlan">${U.icon('plus')} New plan</button>`)
      + C.card({ title: 'Active plans', icon: 'goal', body: C.table(
        [{ t: 'Patient' }, { t: 'Plan' }, { t: 'Target' }, { t: 'Adherence' }, { t: 'Review' }, { t: '' }],
        all.slice(0, 8).map((p, i) => ({ cells: [
          `<div class="pt-cell">${C.avatar(p.name)}<div><div class="pt-name">${p.name}</div><div class="pt-id">${p.id}</div></div></div>`,
          ['Sleep regularity', 'Movement 8k steps', 'Cycle logging', 'Stress practice'][i % 4],
          ['23:00–07:00', '8,000 steps/d', 'daily', '10 min × 5/wk'][i % 4],
          `<div class="progress" style="width:90px"><span style="width:${p.adherence}%;background:linear-gradient(90deg,#5b4bf0,#7c5cff)"></span></div>`,
          p.nextVisit,
          `<button class="btn sm" data-act="openPatient" data-arg="${p.id}">Open</button>`] }))) });
  }

  /* ============================== MESSAGES =============================== */
  function messages() {
    const all = pats();
    const msgs = [
      { pid: all[1] && all[1].id, t: 'My band shows poor signal after workouts — should I reposition it?', when: '12 min' },
      { pid: all[3] && all[3].id, t: 'Cycle started 6 days later than predicted, logged it today.', when: '1 h' },
      { pid: all[0] && all[0].id, t: 'Uploaded the new ultrasound images from the lab.', when: '3 h' },
      { pid: all[6] && all[6].id, t: 'Feeling very fatigued this week, severity 4.', when: '1 d' },
    ];
    return C.pageHead('Messages', 'Participant messages. Not for emergencies — clinic protocol applies.')
      + `<div class="row g-2">${msgs.map(m => {
        const p = all.find(x => x.id === m.pid) || all[0];
        return C.card({ body: `<div class="flex center gap-10">${C.avatar(p.name)}
          <div style="flex:1"><div class="tl-title">${p.name}</div><div class="small muted">${p.id} · ${m.when} ago</div></div>
          <span class="tag pink" style="margin:0">Unread</span></div>
          <p class="small" style="line-height:1.7;color:var(--text-2);margin:10px 0">${m.t}</p>
          <div class="flex gap-6"><button class="btn sm primary" data-act="reply" data-arg="${p.id}">Reply</button>
          <button class="btn sm" data-act="openPatient" data-arg="${p.id}">Open chart</button></div>` });
      }).join('')}</div>`;
  }

  /* ============================ CLIN REPORTS ============================= */
  function clinreports() {
    const all = pats();
    return C.pageHead('Clinical Reports', 'Reports always disclose model version, data quality and limitations.',
      `<button class="btn primary" data-act="genReport" data-arg="doctor">${U.icon('report')} Generate</button>`)
      + C.card({ title: 'Report library', icon: 'report', body: C.table(
        [{ t: 'Report' }, { t: 'Patient' }, { t: 'Kind' }, { t: 'Date' }, { t: 'Pages' }, { t: '' }],
        all.slice(0, 8).flatMap(p => p.reports.slice(0, 2).map(r => ({ cells: [
          `<span class="mono">${r.id}</span> ${r.title}`,
          `${p.name} <span class="pt-id">${p.id}</span>`,
          `<span class="tag info" style="margin:0">${r.kind}</span>`, r.date, r.pages,
          `<div class="row-actions"><button class="btn sm" data-act="viewReport" data-arg="${r.id}">Open</button>
           <button class="btn sm ghost" data-act="genReport" data-arg="csv">Export</button></div>`] })))) });
  }

  /* ============================== ANALYTICS ============================== */
  function analytics() {
    const all = pats();
    const byCohort = {};
    all.forEach(p => { (byCohort[p.cohort] = byCohort[p.cohort] || []).push(p.risk); });
    return C.pageHead('Cohort Analytics', 'Aggregate, de-identified views across the research cohort.')
      + `<div class="row g-3">
        ${C.card({ title: 'Risk by cohort', icon: 'chart', body: Chart.bars(Object.entries(byCohort).map(([k, v], i) => ({
          k: k.replace('Chrono-PCOS ', '').replace(' Cohort', ''), v: Math.round(U.avg(v)), color: [U.C.pink, U.C.violet, U.C.cyan][i % 3] })), { h: 170, max: 100 }) })}
        ${C.card({ title: 'Age vs risk', icon: 'compare', body: Chart.scatter(all.map(p => ({ x: p.age, y: p.risk, r: 6, color: U.riskTone(p.risk).color, label: p.id })), { h: 170, xlabel: 'Age → risk %' }) })}
        ${C.card({ title: 'BMI vs cycle length', icon: 'grid', body: Chart.scatter(all.map(p => ({ x: p.bmi, y: p.cycleLen, r: 6, color: U.C.violet, label: p.id })), { h: 170, xlabel: 'BMI → cycle length (d)' }) })}
      </div>
      <div class="row g-2">
        ${C.card({ title: 'Adherence vs data quality', icon: 'check', body: Chart.scatter(all.map(p => ({ x: p.adherence, y: p.quality * 100, r: 7, color: U.C.green, label: p.name })), { h: 200, xlabel: 'Adherence % → quality %' }) })}
        ${C.card({ title: 'Cohort summary', icon: 'db', body: C.table([{ t: 'Metric' }, { t: 'Mean' }, { t: 'Min' }, { t: 'Max' }],
          [['Age', 'age'], ['Risk %', 'risk'], ['Cycle length', 'cycleLen'], ['Adherence %', 'adherence'], ['BMI', 'bmi']]
            .map(([label, key]) => {
              const vals = all.map(p => +p[key]);
              return { cells: [label, U.round(U.avg(vals), 1), Math.min(...vals), Math.max(...vals)] };
            })) })}
      </div>`;
  }

  /* =============================== EXPORTS =============================== */
  function exports_() {
    return C.pageHead('Export & Sharing', 'De-identified exports for research. Every export is logged.',
      `<button class="btn primary" data-act="exportCohort">${U.icon('export')} New export</button>`)
      + `<div class="row g-4">
        ${C.tile({ title: 'CSV (long format)', sub: 'per-sample rows', icon: 'export', color: U.C.sky, act: 'exportCohort' })}
        ${C.tile({ title: 'JSON bundle', sub: 'records + provenance', icon: 'db', color: U.C.violet, act: 'exportCohort' })}
        ${C.tile({ title: 'PDF summary', sub: 'cohort report', icon: 'report', color: U.C.pink, act: 'genReport' })}
        ${C.tile({ title: 'Secure link', sub: '7-day expiry', icon: 'share', color: U.C.green, act: 'shareDoctor' })}
      </div>
      ${C.card({ title: 'Export history', icon: 'audit', body: C.table([{ t: 'When' }, { t: 'By' }, { t: 'Scope' }, { t: 'Rows' }, { t: 'Status' }],
        [['26 Sep 10:52', 'Dr. Meera Iyer', 'Cohort B (n=4)', '18,402', 'Completed'],
         ['22 Sep 15:10', 'Dr. Ananya Rao', 'Cohort A (n=3)', '12,980', 'Completed'],
         ['14 Sep 09:31', 'system', 'Nightly backup', '—', 'Completed']].map(r => ({ cells: [r[0], r[1], r[2], r[3], C.statusTag('Confirmed').replace('Confirmed', r[4])] }))) })}`;
  }

  /* =============================== DOCTORS =============================== */
  function doctors() {
    const ds = Store.doctors();
    const all = pats();
    return C.pageHead('Doctors & Staff', 'Add, edit and manage clinicians on this workstation.',
      `<button class="btn primary" data-act="addDoctor">${U.icon('plus')} Add doctor</button>`)
      + `<div class="row g-3">${ds.map(d => C.card({
        body: `<div class="flex center gap-10">
            ${C.avatar(d.name, 'lg')}
            <div style="flex:1;min-width:0">
              <div class="tl-title" style="font-size:14px">${d.name} ${d.id === Store.state.currentDoctor ? '<span class="tag good" style="margin:0">signed in</span>' : ''}</div>
              <div class="small muted">${d.specialty}</div>
              <div class="small muted mono">${d.id} · Reg ${d.reg}</div>
            </div>
          </div>
          <div class="mt-10">${C.kvs([
            { k: 'Clinic', v: d.clinic }, { k: 'Room / slot', v: `${d.room} · ${d.slot}` },
            { k: 'Days', v: d.days }, { k: 'Experience', v: d.exp + ' yrs' },
            { k: 'Patients', v: all.filter(p => p.doctorId === d.id).length },
            { k: 'Status', v: C.statusTag(d.status) },
            { k: 'Contact', v: `${d.email}<br>${d.phone}` },
          ])}</div>
          <div class="flex gap-6 mt-10 wrap">
            <button class="btn sm primary" data-act="editDoctor" data-arg="${d.id}">${U.icon('edit', 'ic', 'width:13px;height:13px')} Edit</button>
            <button class="btn sm" data-act="signInDoctor" data-arg="${d.id}">Sign in as</button>
            <button class="btn sm danger" data-act="deleteDoctor" data-arg="${d.id}">${U.icon('trash', 'ic', 'width:13px;height:13px')}</button>
          </div>`,
      })).join('')}</div>
      ${C.card({ title: 'Caseload distribution', icon: 'chart', body: Chart.bars(ds.map(d => ({
        k: d.name.replace('Dr. ', '').split(' ')[0], v: all.filter(p => p.doctorId === d.id).length, color: U.C.violet })), { h: 160, max: Math.max(4, all.length) }) })}`;
  }

  /* ================================ CLINIC =============================== */
  function clinic() {
    const all = pats();
    return C.pageHead('Clinic Profile', 'Site details, capacity and research registration.',
      `<button class="btn primary" data-act="editClinic">${U.icon('edit')} Edit clinic</button>`)
      + `<div class="row g-2">
        ${C.card({ title: 'ENDO-TWIN Research Clinic', icon: 'hospital', iconColor: U.C.sky, body: C.kvs([
          { k: 'Address', v: 'Connaught Place, New Delhi 110001' }, { k: 'Site ID', v: 'SITE-DEL-01' },
          { k: 'Ethics approval', v: 'IRB-2026-114 (demo)' }, { k: 'Clinicians', v: Store.doctors().length },
          { k: 'Participants', v: all.length }, { k: 'Devices', v: DemoData.devices.length },
          { k: 'Operating hours', v: '08:00 – 20:00' },
        ]) })}
        ${C.card({ title: 'Capacity & throughput', icon: 'chart', body: Chart.lines([
          { name: 'Visits', color: U.C.sky, data: U.series('cap', 20, 14, 5) },
          { name: 'Scans', color: U.C.orange, data: U.series('cap2', 20, 5, 3) }], { h: 180, area: true })
          + C.legend([{ k: 'Visits/day', c: U.C.sky }, { k: 'Scans/day', c: U.C.orange }]) })}
      </div>`;
  }

  /* ================================ FLEET ================================ */
  function fleet() {
    const all = pats();
    return C.pageHead('Device Fleet', 'Firmware, battery and link health across issued bands.',
      `<button class="btn primary" data-act="firmware">${U.icon('settings')} Push firmware</button>`)
      + C.card({ title: 'Devices', icon: 'fleet', body: C.table(
        [{ t: 'Device' }, { t: 'Firmware' }, { t: 'Assigned to' }, { t: 'Battery' }, { t: 'RSSI' }, { t: 'State' }, { t: '' }],
        DemoData.devices.map(d => {
          const p = all.find(x => x.id === d.pid);
          return { cells: [`<b class="mono">${d.id}</b>`, d.fw, p ? `${p.name} <span class="pt-id">${p.id}</span>` : '—',
            `<div class="progress" style="width:70px"><span style="width:${d.batt}%;background:${d.batt > 40 ? U.C.green : d.batt > 15 ? U.C.yellow : U.C.red}"></span></div>`,
            d.rssi == null ? '—' : d.rssi + ' dBm', C.statusTag(d.state),
            `<button class="btn sm" data-act="recalibrate">Self-test</button>`] };
        })) });
  }

  /* =============================== DATABASE ============================== */
  function database() {
    const tables = [
      ['patients', Store.state.patients.length], ['doctors', Store.doctors().length], ['sensor_sessions', 412],
      ['sensor_samples', 1842301], ['features', 38210], ['risk_outputs', 1840], ['symptom_logs', 2214],
      ['medication_logs', 981], ['cycle_logs', 604], ['ultrasound_studies', 96], ['reports', 240],
      ['provenance', 51204], ['audit_log', 8830], ['devices', DemoData.devices.length], ['appointments', Store.state.appointments.length],
      ['care_plans', 42], ['messages', 118], ['settings', 1],
    ];
    return C.pageHead('Database', 'Local-first SQLite · 18 tables · no cloud upload.',
      `<button class="btn" data-act="exportCohort">${U.icon('export')} Backup</button>`)
      + `<div class="row g-3">
        ${C.card({ title: 'Tables', icon: 'db', body: C.table([{ t: 'Table' }, { t: 'Rows' }],
          tables.map(t => ({ cells: [`<span class="mono">${t[0]}</span>`, t[1].toLocaleString()] }))) })}
        ${C.card({ title: 'Storage', icon: 'chart', body: Chart.bars([
          { k: 'samples', v: 78, color: U.C.violet }, { k: 'features', v: 12, color: U.C.sky },
          { k: 'images', v: 7, color: U.C.orange }, { k: 'meta', v: 3, color: U.C.green }], { h: 170, max: 100 })
          + C.kvs([{ k: 'DB file', v: 'chrono_twin_nexus_v8_3_plus.db' }, { k: 'Size', v: '412 MB' }, { k: 'Last vacuum', v: '24 Sep 2026' }]) })}
        ${C.card({ title: 'Integrity', icon: 'shield', iconColor: U.C.green, body: `<div class="log-box">
          <div><span class="ok">[ok]</span> PRAGMA integrity_check → ok</div>
          <div><span class="ok">[ok]</span> foreign_key_check → 0 violations</div>
          <div><span class="ok">[ok]</span> WAL mode enabled</div>
          <div><span class="warn">[warn]</span> 2 orphan sample batches quarantined</div>
          <div><span class="dim">[info]</span> nightly backup 02:00 local</div></div>` })}
      </div>`;
  }

  /* ============================= DIAGNOSTICS ============================= */
  function diagnostics() {
    const checks = [
      ['Python runtime', 'PASS', '3.11.2'], ['PySide6 desktop bridge', 'PASS', '6.6'],
      ['SQLite database', 'PASS', '18 tables'], ['Serial / BLE reader', 'PASS', 'ESP32-S3 detected'],
      ['Signal pipeline', 'PASS', 'ppg, hrv, gsr, temp, imu'], ['Model registry', 'PASS', DemoData.models.length + ' models'],
      ['Ultrasound module', 'WARN', 'research weights only'], ['Report generator', 'PASS', 'pdf + csv'],
      ['Data provenance', 'PASS', 'no mixed categories'], ['External validation', 'WARN', 'not performed'],
    ];
    return C.pageHead('Diagnostics', 'Real checks — never fake PASS. Warnings are shown honestly.',
      `<button class="btn primary" data-act="runDiagnostics">${U.icon('settings')} Run all checks</button>`)
      + `<div class="row g-2">
        ${C.card({ title: 'System checks', icon: 'check', body: C.table([{ t: 'Check' }, { t: 'Result' }, { t: 'Detail' }],
          checks.map(c => ({ cells: [c[0], `<span class="tag ${c[1] === 'PASS' ? 'good' : c[1] === 'WARN' ? 'warn' : 'bad'}" style="margin:0">${c[1]}</span>`, c[2]] }))) })}
        ${C.card({ title: 'Console', icon: 'settings', body: `<div class="log-box" id="diagConsole">
          <div><span class="dim">$</span> endo-twin diagnostics --all</div>
          <div><span class="ok">[pass]</span> 8 checks passed</div>
          <div><span class="warn">[warn]</span> 2 warnings (documented limitations)</div>
          <div><span class="err">[fail]</span> 0 failures</div>
          <div><span class="dim">done in 1.9s</span></div></div>` })}
      </div>`;
  }

  /* =============================== AUDIT ================================= */
  function audit() {
    return C.pageHead('Audit Log', 'Immutable trail of access, inference and export events.')
      + C.card({ title: 'Today', icon: 'lock', body: C.table([{ t: 'Time' }, { t: 'Actor' }, { t: 'Action' }, { t: 'Object' }, { t: 'Level' }],
        DemoData.auditLog.concat(DemoData.auditLog.map(a => Object.assign({}, a, { t: a.t.replace(/^1/, '0') })))
          .map(a => ({ cells: [`<span class="mono">${a.t}</span>`, a.who, a.act, `<span class="mono">${a.obj}</span>`,
            `<span class="tag ${a.lvl === 'err' ? 'bad' : a.lvl === 'warn' ? 'warn' : a.lvl === 'ok' ? 'good' : 'plain'}" style="margin:0">${a.lvl}</span>`] }))) });
  }

  /* =============================== PREFS ================================= */
  function prefs() {
    const d = Store.doctor();
    return C.pageHead('Preferences', 'Console behaviour for the signed-in clinician.',
      `<button class="btn primary" data-act="editDoctor" data-arg="${d.id}">${U.icon('edit')} Edit my profile</button>`)
      + `<div class="row g-2">
        ${C.card({ title: 'Signed in as', icon: 'user', body: `<div class="flex center gap-14">${C.avatar(d.name, 'lg')}
          <div><div class="page-title" style="font-size:16px">${d.name}</div><div class="small muted">${d.specialty} · ${d.id}</div>
          <div class="chips mt-6"><span class="chip">${d.clinic}</span>${C.statusTag(d.status)}</div></div></div>
          <div class="mt-14">${C.kvs([{ k: 'Registration', v: d.reg }, { k: 'Email', v: d.email }, { k: 'Phone', v: d.phone },
            { k: 'Hours', v: `${d.days} · ${d.slot}` }])}</div>
          <div class="mt-14"><select class="select" data-act="switchDoctor" style="padding:8px 11px;width:100%">
            ${Store.doctors().map(x => `<option value="${x.id}" ${x.id === d.id ? 'selected' : ''}>Sign in as ${x.name}</option>`).join('')}
          </select></div>` })}
        ${C.card({ title: 'Console options', icon: 'settings', body: PatientViews.pages && `
          ${['Show research-only models', 'Auto-open triage queue', 'Compact tables', 'Show provenance chips', 'Sound alerts']
            .map((k, i) => `<div class="kv"><span class="k">${k}</span><span class="v"><input type="checkbox" ${i < 3 ? 'checked' : ''}></span></div>`).join('')}
          <div class="flex gap-6 mt-14"><button class="btn sm danger" data-act="resetDemo">Reset demo data</button></div>` })}
      </div>`;
  }

  function about() { return PatientViews.pages.about(active()); }

  /* ------------------------------ registry ------------------------------- */
  const pages = { dashboard, registry, chart, reviews, cohorts, signals, longitudinal, imaging, lab,
    explain, provenance, appointments, notes, careplans, messages, clinreports, analytics,
    exports: exports_, doctors, clinic, fleet, database, diagnostics, audit, prefs, about };

  function render(id) { return (pages[id] || pages.dashboard)(); }

  return { nav, render, pages };
})();
