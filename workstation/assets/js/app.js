/* ============================================================
   ENDO-TWIN NEXUS — application shell, routing, actions
   ============================================================ */
const App = (() => {
  let route = 'dashboard';
  let liveTimer = null;

  const role = () => Store.state.role;
  const views = () => (role() === 'doctor' ? DoctorViews : PatientViews);

  /* ------------------------------- brand -------------------------------- */
  const BRAND_SVG = `<svg viewBox="0 0 48 48" fill="none">
    <defs><linearGradient id="bg1" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#7c5cff"/><stop offset="55%" stop-color="#ff4d8d"/><stop offset="100%" stop-color="#22d3ee"/>
    </linearGradient></defs>
    <path d="M24 26c-4-10-10-14-16-12-4 1.4-5 8 0 13 4 4 10 5 16 3z" fill="url(#bg1)" opacity=".92"/>
    <path d="M24 26c4-10 10-14 16-12 4 1.4 5 8 0 13-4 4-10 5-16 3z" fill="url(#bg1)" opacity=".72"/>
    <path d="M24 26c-2 5-3 10-2 16M24 26c2 5 3 10 2 16" stroke="url(#bg1)" stroke-width="2.2" stroke-linecap="round"/>
    <circle cx="24" cy="24" r="3" fill="#fff" opacity=".9"/></svg>`;

  /* ------------------------------ top bar ------------------------------- */
  function renderTop() {
    U.$('#brandMark').innerHTML = BRAND_SVG;
    const p = Store.patient() || { name: 'No participant', device: '', battery: 0 };
    const d = Store.doctor() || { name: 'No clinician', specialty: '—' };
    const isDoc = role() === 'doctor';
    U.$('#topAvatar').textContent = U.initials(isDoc ? d.name : p.name);
    U.$('#topName').textContent = isDoc ? d.name : String(p.name).split(' ')[0];
    U.$('#topRole').textContent = isDoc ? 'Doctor View' : 'Patient View';
    const link = (window.DeviceLink && DeviceLink.state.status) || {};
    const linked = link.state === 'connected' || link.state === 'streaming';
    const pill = U.$('#devicePill');
    if (linked) {
      const bat = U.has(link.battery) ? ` • ${Math.round(link.battery)}%` : '';
      U.$('#deviceLabel').textContent = link.recording ? 'Recording' : 'Wearable Live';
      U.$('#deviceSub').textContent = `${link.deviceName || 'ENDO-TWIN device'} · ${(link.transport || '').toUpperCase()}${bat}`;
      pill.classList.remove('off');
      pill.classList.toggle('rec', !!link.recording);
    } else {
      U.$('#deviceLabel').textContent = isDoc ? 'Device Fleet' : 'Wearable';
      U.$('#deviceSub').textContent = isDoc
        ? `${DemoData.devices.filter(x => x.state === 'Online').length}/${DemoData.devices.length} devices online`
        : `${(p.device || '').split('·').pop().trim() || 'Not paired'} • ${U.num(p.battery)}%`;
      pill.classList.toggle('off', !isDoc && !p.battery);
      pill.classList.remove('rec');
    }
    pill.onclick = () => go(isDoc ? 'livedevice' : 'wearable');
    renderSourceChip();
    U.$('#notifyBadge').textContent = Store.state.notifications.filter(n => !n.read).length || '';
    U.$('#notifyBadge').style.display = Store.state.notifications.some(n => !n.read) ? 'grid' : 'none';
    renderSwitchMenu();
  }

  /* --------------------- data source chip (live / demo) ------------------ */
  function renderSourceChip() {
    const chip = U.$('#dsChip'); if (!chip) return;
    const live = Store.isLive(), empty = Store.dbEmpty();
    chip.classList.toggle('demo', !live);
    chip.classList.toggle('warn', live && empty);
    U.$('#dsText').textContent = Store.sourceLabel();
    const h = Store.health();
    chip.title = live
      ? `Reading the real platform database\n${h ? h.db : ''}\n${h ? h.counts.patients + ' patients · ' + h.counts.sensor_sessions + ' sensor sessions' : ''}`
      : 'Built-in sample dataset (no database reachable or demo mode selected)';
  }

  function sourceModal() {
    const h = Store.health(), live = Store.isLive();
    const rows = h ? [
      ['Database file', `<span class="mono">${U.esc(h.db)}</span>`],
      ['File size', (h.size_bytes / 1048576).toFixed(2) + ' MB'],
      ['Participants', h.counts.patients], ['Providers / clinicians', h.counts.providers],
      ['Sensor sessions', h.counts.sensor_sessions],
      ['Sensor rows', (h.counts.hrv_data + h.counts.ppg_data + h.counts.temperature_data + h.counts.gsr_data).toLocaleString()],
      ['Symptom entries', h.counts.symptoms], ['Cycle entries', h.counts.cycles],
      ['Ultrasound studies', h.counts.ultrasound_records], ['Model results', h.counts.model_results],
      ['Clinician notes', h.counts.doctor_notes], ['Reports', h.counts.reports],
      ['Rows labelled SYNTHETIC_DEMO', h.counts.demo_rows],
    ] : [['Backend', 'unreachable — ' + (Store.serverError || 'static file mode')]];
    C.modal({
      title: 'Data source', sub: live ? 'Live platform database' : 'Built-in demo dataset',
      icon: 'database', color: live ? U.C.green : U.C.yellow,
      body: `<p class="muted" style="margin:0 0 12px;font-size:12.6px;line-height:1.6">
          ${live
            ? 'Every number on screen is read from the SQLite database this platform writes to. Measurements that were never recorded stay blank (—) instead of being invented.'
            : 'The backend API is not reachable, so the interface is showing its built-in sample dataset. Nothing here comes from a real participant.'}
        </p>
        ${C.table(['Property', 'Value'], rows.map(r => ({ cells: r })))}
        <div class="dbb-actions" style="margin-top:14px">
          ${live ? `<button class="btn" data-ds="seed">${U.icon('plus')} Seed demo cohort into database</button>
                    <button class="btn ghost" data-ds="clear">${U.icon('trash')} Remove seeded demo rows</button>` : ''}
          <button class="btn ghost" data-ds="${live ? 'demo' : 'live'}">${U.icon('refresh')} ${live ? 'Switch to built-in demo data' : 'Retry live database'}</button>
        </div>`,
      footer: `<button class="btn primary" data-close="1">Close</button>`,
    });
    U.$$('[data-ds]').forEach(b => b.onclick = async () => {
      const k = b.dataset.ds;
      b.disabled = true;
      try {
        if (k === 'seed') { C.toast('Seeding cohort into the database…', 'info'); await Store.seedDemoCohort(); C.toast('Demo cohort written to the database'); }
        if (k === 'clear') { await Store.clearDemoCohort(); C.toast('Seeded demo rows removed', 'info'); }
        if (k === 'demo') { await Store.useDemo(); C.toast('Showing built-in demo data', 'info'); }
        if (k === 'live') { await Store.useLive(); C.toast(Store.isLive() ? 'Connected to the platform database' : 'Database still unreachable', Store.isLive() ? 'ok' : 'err'); }
      } catch (e) { C.toast('Failed: ' + e.message, 'err'); }
      b.disabled = false;
      C.closeModal(); renderAll();
    });
  }

  function emptyDbPage() {
    const h = Store.health() || { db: '', counts: {} };
    return `<div class="db-banner">
        <div class="dbb-ico">${U.icon('database')}</div>
        <div style="flex:1">
          <h3>The platform database has no participants yet</h3>
          <p>This workstation is connected to the real database
            (<span class="mono">${U.esc(h.db)}</span>) and it currently contains
            <b>${h.counts.patients || 0}</b> participant records. Rather than show invented numbers, every
            panel stays empty until real data exists. Record a session from the PySide6 platform or the ESP32-S3
            device, or write a clearly-labelled demo cohort into the database to explore the interface.</p>
          <div class="dbb-actions">
            <button class="btn" data-act="seedCohort">${U.icon('plus')} Seed demo cohort into database</button>
            <button class="btn ghost" data-act="useDemoData">${U.icon('eye')} Use built-in demo data instead</button>
            <button class="btn ghost" data-act="showSource">${U.icon('database')} Data source details</button>
          </div>
        </div>
      </div>
      ${C.card({ title: 'Why this screen is empty', icon: 'info', color: U.C.sky,
        body: C.bullets([
          'Vitals, trends, cycle phase and risk are all derived from rows in the database — none are simulated in live mode.',
          'Seeding writes rows tagged SYNTHETIC_DEMO into the same database, so they can be removed again in one click.',
          'Switching to built-in demo data leaves the database untouched and flags the interface as DEMO DATA.',
        ]) })}
      ${C.disclaimer()}`;
  }

  function renderSwitchMenu() {
    const isDoc = role() === 'doctor';
    const menu = U.$('#switchMenu');
    menu.innerHTML = `
      <div class="sm-label">Switch workspace</div>
      <div class="sm-role ${!isDoc ? 'active' : ''}" data-role="patient">
        <div class="sm-ico">${U.icon('user')}</div>
        <div><div class="sm-title">Patient View</div><div class="sm-desc">Your own dashboard & tracking</div></div>
        ${!isDoc ? `<span class="sm-check">${U.icon('check')}</span>` : ''}
      </div>
      <div class="sm-role ${isDoc ? 'active' : ''}" data-role="doctor">
        <div class="sm-ico">${U.icon('stethoscope')}</div>
        <div><div class="sm-title">Doctor View</div><div class="sm-desc">Clinical console & registry</div></div>
        ${isDoc ? `<span class="sm-check">${U.icon('check')}</span>` : ''}
      </div>
      <div class="sm-sep"></div>
      <div class="sm-label">${isDoc ? 'Signed in clinician' : 'Demo patient profile'}</div>
      <div style="max-height:180px;overflow:auto">
        ${isDoc
          ? Store.doctors().map(d => `<div class="sm-person ${d.id === Store.state.currentDoctor ? 'active' : ''}" data-doctor="${d.id}">
              ${C.avatar(d.name)}<div><div class="sm-title" style="font-size:12px">${d.name}</div>
              <div class="sm-desc">${d.specialty}</div></div></div>`).join('')
          : Store.patients().map(p => `<div class="sm-person ${p.id === Store.state.activePatient ? 'active' : ''}" data-patient="${p.id}">
              ${C.avatar(p.name)}<div><div class="sm-title" style="font-size:12px">${p.name}</div>
              <div class="sm-desc">${p.id} · ${p.age} y · risk ${p.risk}%</div></div></div>`).join('')}
      </div>
      <div class="sm-sep"></div>
      <div class="sm-item" data-act="${isDoc ? 'addDoctor' : 'addPatient'}">${U.icon('plus')} ${isDoc ? 'Add doctor' : 'Add patient'}</div>
      <div class="sm-item" data-act="${isDoc ? 'editDoctor' : 'editPatient'}" data-arg="${isDoc ? Store.state.currentDoctor : Store.state.activePatient}">${U.icon('edit')} Edit ${isDoc ? 'my profile' : 'my profile'}</div>
      <div class="sm-item" data-go="${isDoc ? 'prefs' : 'profile'}">${U.icon('settings')} Settings</div>
      <div class="sm-item" data-act="resetDemo">${U.icon('trash')} Reset demo data</div>`;

    U.$$('[data-role]', menu).forEach(b => b.onclick = e => { e.stopPropagation(); setRole(b.dataset.role); });
    U.$$('[data-patient]', menu).forEach(b => b.onclick = e => {
      e.stopPropagation(); Store.setActivePatient(b.dataset.patient); closeMenus(); renderAll();
      C.toast('Switched to ' + Store.patient().name, 'info');
    });
    U.$$('[data-doctor]', menu).forEach(b => b.onclick = e => {
      e.stopPropagation(); Store.setCurrentDoctor(b.dataset.doctor); closeMenus(); renderAll();
      C.toast('Signed in as ' + Store.doctor().name, 'info');
    });
  }

  function setRole(r) {
    if (role() === r) { closeMenus(); return; }
    Store.setRole(r);
    route = 'dashboard';
    closeMenus();
    renderAll();
    C.toast(r === 'doctor' ? 'Doctor workstation active' : 'Patient workstation active', 'info');
  }

  /* ------------------------------ sidebar ------------------------------- */
  function renderNav() {
    const groups = views().nav;
    const reviewCount = Store.patients().filter(p => p.status === 'Needs review' || p.status === 'Escalated').length;
    U.$('#navList').innerHTML = groups.map(g => `
      ${g.label ? `<div class="nav-group-label">${g.label}</div>` : ''}
      ${g.items.map(i => `<div class="nav-item ${route === i.id ? 'active' : ''}" data-go="${i.id}">
        ${U.icon(i.icon)}<span>${i.label}</span>
        ${i.pill ? `<span class="nav-pill">${i.id === 'reviews' ? reviewCount : 4}</span>` : i.caret ? `<span class="nav-caret">${U.icon('chevR', 'ic', 'width:13px;height:13px')}</span>` : ''}
      </div>`).join('')}`).join('');
  }

  /* -------------------------------- main -------------------------------- */
  /* Generic add/edit/delete editor for the clinical lists (labs, meds, goals) */
  function listEditor(kind, title, id) {
    const p = Store.patient(id) || Store.patient();
    const items = (p[kind] || []);
    const cols = {
      labs: [{ t: 'Test' }, { t: 'Value' }, { t: 'Unit' }, { t: 'Date' }, { t: '', w: '90px' }],
      meds: [{ t: 'Item' }, { t: 'Dose' }, { t: 'Schedule' }, { t: 'Since' }, { t: '', w: '90px' }],
      goals: [{ t: 'Goal' }, { t: 'Target' }, { t: 'Progress' }, { t: 'Due' }, { t: '', w: '90px' }],
    }[kind];
    const rowOf = it => ({
      labs: [it.k || it.name, `<b>${U.num(it.value, 2)}</b>`, it.unit || '', it.date || it.added || ''],
      meds: [it.n || it.name, it.d || it.dose || '', it.t || it.schedule || '', it.since || it.added || ''],
      goals: [it.k || it.name, it.target || '', U.num(it.v, 0) + '%', it.due || ''],
    }[kind]).concat([
      `<button class="btn sm ghost" data-litem="${it.id}" data-lact="edit">${U.icon('edit', 'ic', 'width:13px;height:13px')}</button>
       <button class="btn sm ghost" data-litem="${it.id}" data-lact="del">${U.icon('trash', 'ic', 'width:13px;height:13px')}</button>`]);

    C.modal({
      title, sub: `${p.name} · ${p.id}`, icon: kind === 'labs' ? 'flask' : kind === 'meds' ? 'pill' : 'goal',
      color: U.C.violet,
      body: (items.length ? C.table(cols, items.map(it => ({ cells: rowOf(it) })))
        : C.empty('Nothing recorded yet', 'Add the first entry — it feeds straight into the predictions.'))
        + `<div class="flex gap-6 mt-14"><button class="btn sm primary" data-lact="add">${U.icon('plus')} Add entry</button></div>`,
      footer: `<button class="btn primary" data-close="1">Done</button>`,
    });

    const fieldsFor = (it = {}) => ({
      labs: [
        { n: 'k', l: 'Test', t: 'select', o: LAB_PRESETS, v: it.k },
        { n: 'value', l: 'Value', t: 'number', v: it.value },
        { n: 'unit', l: 'Unit', v: it.unit, ph: 'mg/dL' },
        { n: 'ref', l: 'Reference range', v: it.ref, ph: '70–99' },
        { n: 'date', l: 'Sample date', t: 'date', v: it.date },
      ],
      meds: [
        { n: 'n', l: 'Medication / supplement', v: it.n },
        { n: 'd', l: 'Dose', v: it.d, ph: '500 mg' },
        { n: 't', l: 'Schedule', t: 'select', o: ['Morning', 'Afternoon', 'Night', 'After dinner', 'Twice daily'], v: it.t },
        { n: 'k', l: 'Type', t: 'select', o: ['Supplement', 'Prescription', 'OTC'], v: it.k },
        { n: 'since', l: 'Started', t: 'date', v: it.since },
      ],
      goals: [
        { n: 'k', l: 'Goal', v: it.k },
        { n: 'target', l: 'Target', v: it.target },
        { n: 'v', l: 'Progress (%)', t: 'number', v: it.v, min: 0, max: 100 },
        { n: 'due', l: 'Due', t: 'date', v: it.due },
      ],
    }[kind]);

    const save = async (method, payload) => {
      await Store.api(`/api/patients/${encodeURIComponent(p.id)}/${kind}`, method, payload);
      await Store.refresh();
      await loadComplications(true);
      listEditor(kind, title, p.id);
    };

    U.$$('[data-lact]').forEach(b => b.onclick = () => {
      const act = b.dataset.lact;
      const it = items.find(x => x.id === b.dataset.litem) || {};
      if (act === 'del') return save('DELETE', { id: it.id }).then(() => C.toast('Entry removed', 'info'));
      C.modal({
        title: (act === 'add' ? 'Add to ' : 'Edit ') + title.toLowerCase(), icon: 'edit', color: U.C.violet,
        body: C.form(fieldsFor(it)), okText: 'Save',
        async onOk(v) {
          try {
            await save(act === 'add' ? 'POST' : 'PATCH', act === 'add' ? v : Object.assign({ id: it.id }, v));
            C.toast('Saved' + (Store.isLive() ? ' to the database' : ''));
          } catch (e) { C.toast(e.message, 'err'); }
        },
      });
    });
  }

  function renderMain() {
    const main = U.$('#main');
    if (Store.dbEmpty()) {
      main.innerHTML = emptyDbPage();
      main.scrollTop = 0; bindMain(); return;
    }
    main.innerHTML = views().render(route);
    main.scrollTop = 0;
    window.scrollTo({ top: 0 });
    bindMain();
    startLive();
    if (route === 'wearable' || route === 'livedevice') bindDeviceUI();
    else DeviceLink.start(6000);
    if (route === 'complications') loadComplications(false);
  }

  function renderAll() { renderTop(); renderNav(); renderMain(); }

  function go(id) {
    if (!views().pages[id]) { C.toast('Section "' + id + '" is not available in this view', 'info'); return; }
    route = id;
    renderNav(); renderMain();
  }

  /* ------------------------------- live tick ----------------------------- */
  function paintLive(p) {
    const lc = U.$('#liveChart');
    if (lc) lc.innerHTML = PatientViews.liveChartHTML(p);
    U.$$('.vital[data-vital]').forEach(card => {
      const k = card.dataset.vital;
      const val = U.$('.v-val', card);
      const map = {
        hr: U.num(p.vitals.hr), hrv: U.num(p.vitals.hrv), temp: U.num(p.vitals.temp, 1),
        gsr: U.num(p.vitals.gsr, 2), steps: U.has(p.vitals.steps) ? p.vitals.steps.toLocaleString() : '—',
        spo2: U.num(p.vitals.spo2),
      };
      if (val && map[k] != null && val.childNodes[0]) val.childNodes[0].nodeValue = map[k];
      const sp = U.$('.v-spark', card);
      const col = { hr: U.C.pink, hrv: U.C.sky, temp: U.C.orange, gsr: U.C.violet, steps: U.C.green, spo2: U.C.cyan }[k];
      if (sp) sp.innerHTML = Chart.spark(p.live[k], col, 62, 34);
    });
  }

  function startLive() {
    clearInterval(liveTimer);
    if (role() !== 'patient' || route !== 'dashboard' && route !== 'live') return;
    if (!Store.state.settings.liveStream) return;

    /* LIVE MODE: re-read the real series from the database instead of
       animating invented values. Nothing moves unless new rows were written. */
    if (Store.isLive()) {
      const pid = Store.state.activePatient;
      liveTimer = setInterval(async () => {
        try {
          const fresh = await Store.api('/api/patients/' + encodeURIComponent(pid) + '/series');
          const p = Store.patient(pid);
          if (!p || !fresh) return;
          Object.keys(fresh.live || {}).forEach(k => { p.live[k] = fresh.live[k] || []; });
          Object.assign(p.vitals, fresh.vitals || {});
          paintLive(p);
        } catch (e) { /* backend hiccup: keep the last real reading on screen */ }
      }, 10000);
      return;
    }

    /* DEMO MODE: the built-in sample dataset animates so the UI feels live. */
    liveTimer = setInterval(() => {
      const p = Store.patient();
      if (!p) return;
      ['hr', 'hrv', 'temp', 'gsr', 'steps', 'spo2'].forEach(k => {
        const arr = p.live[k];
        if (!arr || !arr.length) return;
        const last = arr[arr.length - 1];
        const base = U.avg(arr);
        const amp = { hr: 2.2, hrv: 2.4, temp: 0.08, gsr: 0.02, steps: 6, spo2: 0.3 }[k];
        arr.push(+(last + (Math.random() - 0.5) * amp + (base - last) * 0.15).toFixed(3));
        arr.shift();
      });
      if (p.live.hr.length) {
        p.vitals.hr = Math.round(p.live.hr.at(-1));
        p.vitals.hrv = Math.round(p.live.hrv.at(-1));
        p.vitals.temp = U.round(p.live.temp.at(-1), 1);
        p.vitals.gsr = U.round(p.live.gsr.at(-1), 2);
        p.vitals.spo2 = Math.round(p.live.spo2.at(-1));
      }
      paintLive(p);
    }, 2200);
  }

  /* ------------------------------- actions ------------------------------- */
  const patientFields = (p = {}) => [
    { n: 'name', l: 'Full name *', v: p.name, ph: 'e.g. Priya Sharma' },
    { n: 'id', l: 'Participant ID', v: p.id, ph: 'auto', hint: p.id ? 'ID cannot be changed' : 'Leave blank to auto-generate' },
    { n: 'age', l: 'Age (years)', t: 'number', v: p.age, min: 8, max: 99 },
    { n: 'gender', l: 'Gender', t: 'select', o: ['Female', 'Male', 'Other', 'Prefer not to say'], v: p.gender },
    { n: 'phone', l: 'Phone', v: p.phone }, { n: 'email', l: 'Email', v: p.email },
    { n: 'city', l: 'City', v: p.city },
    { n: 'blood', l: 'Blood group', t: 'select', o: ['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-'], v: p.blood },
    { n: 'height', l: 'Height (cm)', t: 'number', v: p.height }, { n: 'weight', l: 'Weight (kg)', t: 'number', v: p.weight },
    { n: 'cycleLen', l: 'Cycle length (days)', t: 'number', v: p.cycleLen, min: 15, max: 90 },
    { n: 'cycleDay', l: 'Current cycle day', t: 'number', v: p.cycleDay, min: 1, max: 90 },
    { n: 'risk', l: 'Baseline risk signal (%)', t: 'number', v: p.risk == null ? 40 : p.risk, min: 0, max: 100, hint: 'Demo seed for synthetic physiology' },
    { n: 'adherence', l: 'Adherence (%)', t: 'number', v: p.adherence == null ? 80 : p.adherence, min: 0, max: 100 },
    { n: 'doctorId', l: 'Primary clinician', t: 'select', o: Store.doctors().map(d => ({ v: d.id, l: d.name })), v: p.doctorId },
    { n: 'cohort', l: 'Cohort', t: 'select', o: ['Chrono-PCOS Cohort A', 'Chrono-PCOS Cohort B', 'Control Cohort', 'Sleep / Circadian'], v: p.cohort },
    { n: 'status', l: 'Status', t: 'select', o: ['Active', 'Needs review', 'Escalated', 'Archived'], v: p.status },
    { n: 'device', l: 'Device', v: p.device || 'Not paired' },
  ];

  const doctorFields = (d = {}) => [
    { n: 'name', l: 'Full name *', v: d.name, ph: 'e.g. Dr. Ananya Rao' },
    { n: 'specialty', l: 'Specialty', t: 'select', o: ['Endocrinology', 'Gynaecology', 'Reproductive Medicine', 'Sleep & Chronobiology', 'Clinical Nutrition', 'Radiology', 'General'], v: d.specialty },
    { n: 'reg', l: 'Registration no.', v: d.reg }, { n: 'exp', l: 'Experience (years)', t: 'number', v: d.exp },
    { n: 'email', l: 'Email', v: d.email }, { n: 'phone', l: 'Phone', v: d.phone },
    { n: 'clinic', l: 'Clinic / site', v: d.clinic, full: true },
    { n: 'room', l: 'Room', v: d.room }, { n: 'status', l: 'Availability', t: 'select', o: ['Available', 'In consult', 'Off duty'], v: d.status },
    { n: 'days', l: 'Working days', v: d.days }, { n: 'slot', l: 'Hours', v: d.slot },
  ];

  /* --------------------- wearable + complications ----------------------- */
  function bindDeviceUI() {
    const st = PatientViews.wearState;
    if (!st.loaded) {
      st.loaded = true;
      DeviceLink.getCalibration().then(r => { st.cal = r.calibration || {}; renderMain(); }).catch(() => {});
      DeviceLink.ports().then(r => { st.ports = r; }).catch(() => {});
    }
    DeviceLink.start(1200);
  }

  function readCalInputs() {
    const patch = {};
    U.$$('[data-cal]').forEach(inp => {
      const [sensor, field] = inp.dataset.cal.split('.');
      const raw = inp.value;
      patch[sensor] = patch[sensor] || {};
      patch[sensor][field] = raw === '' ? null : (isNaN(+raw) ? raw : +raw);
    });
    return patch;
  }

  async function loadComplications(force) {
    const p = Store.patient();
    const st = PatientViews.compState;
    if (!p) return;
    if (!force && st.data && st.pid === p.id) return;
    st.loading = true; st.error = null; st.pid = p.id;
    renderMain();
    try {
      st.data = await Store.api('/api/patients/' + encodeURIComponent(p.id) + '/complications');
      st.error = st.data.error || null;
    } catch (e) {
      st.error = e.message; st.data = null;
    }
    st.loading = false;
    renderMain();
  }

  const clinicalFields = (p = {}) => [
    { n: 'height', l: 'Height (cm)', t: 'number', v: p.height },
    { n: 'weight', l: 'Weight (kg)', t: 'number', v: p.weight },
    { n: 'waist', l: 'Waist (cm)', t: 'number', v: p.waist, hint: 'Metabolic-syndrome criterion (≥80 cm in women)' },
    { n: 'bp', l: 'Blood pressure (mmHg)', v: (p.vitals || {}).bp || p.bp, ph: '118/76' },
    { n: 'sleepHours', l: 'Typical sleep (h)', t: 'number', v: p.sleepHours },
    { n: 'cycleLen', l: 'Average cycle length (days)', t: 'number', v: p.cycleLen },
    { n: 'smoker', l: 'Smoker', t: 'select', o: ['', 'No', 'Yes'], v: p.smoker },
    { n: 'alcohol', l: 'Alcohol', t: 'select', o: ['', 'None', 'Occasional', 'Weekly', 'Daily'], v: p.alcohol },
    { n: 'familyDiabetes', l: 'Family history: diabetes', t: 'select', o: ['', 'No', 'Yes'], v: p.familyDiabetes },
    { n: 'familyPcos', l: 'Family history: PCOS', t: 'select', o: ['', 'No', 'Yes'], v: p.familyPcos },
    { n: 'familyCvd', l: 'Family history: heart disease', t: 'select', o: ['', 'No', 'Yes'], v: p.familyCvd },
    { n: 'pregnancyPlan', l: 'Planning pregnancy', t: 'select', o: ['', 'No', 'Within a year', 'Trying now'], v: p.pregnancyPlan },
    { n: 'conditions', l: 'Known conditions', t: 'textarea', full: true, v: p.conditions },
    { n: 'allergies', l: 'Allergies', v: p.allergies },
  ];

  const LAB_PRESETS = ['Fasting glucose', 'HbA1c', 'LH / FSH ratio', 'Total testosterone', 'TSH',
    'Vitamin D', 'HDL cholesterol', 'LDL cholesterol', 'Triglycerides', 'ALT', 'Fasting insulin', 'AMH'];

  const actions = {
    /* ---- wearable ---- */
    async connectBle() {
      try { await DeviceLink.connectBLE(Store.state.activePatient); C.toast('Wearable paired over Bluetooth'); }
      catch (e) { C.toast(e.message, 'err'); }
      renderMain();
    },
    async connectUsb() {
      try { await DeviceLink.connectUSB(Store.state.activePatient); C.toast('Wearable connected over USB'); }
      catch (e) { C.toast(e.message, 'err'); }
      renderMain();
    },
    async connectWifi() {
      await DeviceLink.connectServer('wifi', { patientId: Store.state.activePatient });
      C.modal({
        title: 'Wi-Fi ingest armed', icon: 'wave', color: U.C.green,
        body: `<p class="muted" style="font-size:12.6px;line-height:1.6">Point the board (or any script) at this endpoint.
            Frames are the same <span class="mono">$CP2</span> lines the firmware already prints.</p>
          <div class="log-box"><div>POST ${location.origin}/api/device/ingest</div>
          <div>Content-Type: application/json</div>
          <div>{"lines": ["$CP2,1234,2100,-1,0.02,...,4096,AF"]}</div></div>
          <p class="muted" style="font-size:12.4px">curl example:</p>
          <div class="log-box"><div>curl -s ${location.origin}/api/device/ingest \\</div>
          <div>&nbsp;&nbsp;-H 'Content-Type: application/json' \\</div>
          <div>&nbsp;&nbsp;-d '{"lines":["$CP2,..."]}'</div></div>`,
        footer: `<button class="btn primary" data-close="1">Got it</button>`,
      });
      renderMain();
    },
    async connectSerial() {
      const ports = PatientViews.wearState.ports || await DeviceLink.ports();
      PatientViews.wearState.ports = ports;
      if (!ports.available) return C.toast(ports.hint || 'pyserial is not installed on the server', 'err');
      C.modal({
        title: 'Server serial port', icon: 'log', color: U.C.orange,
        body: C.form([
          { n: 'port', l: 'Port', t: 'select', o: ports.ports.map(x => ({ v: x.device, l: `${x.device} · ${x.description || ''}` })) },
          { n: 'baud', l: 'Baud', t: 'number', v: 115200 },
        ]), okText: 'Open port',
        async onOk(v) {
          try { await DeviceLink.connectServer('serial', { port: v.port, baud: +v.baud, patientId: Store.state.activePatient }); C.toast('Serial port opened'); }
          catch (e) { C.toast(e.message, 'err'); }
          C.closeModal(); renderMain();
        },
      });
    },
    async connectBridge() {
      await DeviceLink.connectServer('bridge', { patientId: Store.state.activePatient });
      C.toast('Watching data/bridge/inbox for frames', 'info');
      renderMain();
    },
    async deviceDisconnect() { await DeviceLink.disconnect(); C.toast('Wearable disconnected', 'info'); renderMain(); },
    async deviceRefresh() { await DeviceLink.refresh(); renderMain(); },
    deviceHelp() {
      C.modal({
        title: 'Wiring, firmware and frame format', icon: 'info', color: U.C.sky,
        body: `${C.kvs([
            { k: 'Board', v: 'ESP32-S3 (hardware/esp32/endo_twin_wearable)' },
            { k: 'Pulse sensor', v: 'analog SIG → ADC pin (PULSE_PIN)' },
            { k: 'Skin temp', v: 'DS18B20 → ONE_WIRE_BUS + 4.7 kΩ pull-up' },
            { k: 'GSR', v: 'electrodes → GSR_PIN through the divider' },
            { k: 'IMU', v: 'MPU6050 on the shared I²C bus' },
            { k: 'BLE service', v: `<span class="mono">${DeviceLink.SERVICE_UUID}</span>` },
            { k: 'Serial', v: '115200 baud, newline-delimited' },
          ])}
          <div class="card-sub mt-14">Frame</div>
          <div class="log-box"><div>$CP2,ms,pulse,-1,ax,ay,az,gx,gy,gz,tempC,nan,gsr,…,status,CRC</div></div>
          <div class="small muted mt-10">The red channel is -1 because the fitted sensor is a single-channel analog module,
          so SpO₂ stays unavailable instead of being estimated.</div>`,
        footer: `<button class="btn primary" data-close="1">Close</button>`,
      });
    },
    async startRecording() {
      try {
        await DeviceLink.startSession(Store.state.activePatient);
        C.toast('Recording into the database'); renderMain();
      } catch (e) { C.toast(e.message, 'err'); }
    },
    async stopRecording() {
      try {
        const r = await DeviceLink.stopSession();
        C.toast(`Session saved · ${(r.rows || 0).toLocaleString()} rows`);
        await Store.refresh(); renderMain();
      } catch (e) { C.toast(e.message, 'err'); }
    },
    async calSave() {
      try {
        const r = await DeviceLink.saveCalibration(readCalInputs(), Store.state.activePatient);
        PatientViews.wearState.cal = r.calibration || {};
        C.toast('Calibration saved to the database'); renderMain();
      } catch (e) { C.toast(e.message, 'err'); }
    },
    async calCapture(sensor) {
      try {
        const r = await DeviceLink.captureBaseline(sensor, Store.state.activePatient);
        PatientViews.wearState.cal = r.calibration || {};
        C.toast(`${sensor.toUpperCase()} baseline captured from the live buffer`); renderMain();
      } catch (e) { C.toast(e.message, 'err'); }
    },
    calReference(sensor) {
      const meta = {
        temp: { title: 'Thermometer reference', label: 'Reference temperature (°C)', ph: '36.6' },
        ppg: { title: 'Reference heart rate', label: 'Heart rate from a trusted monitor (bpm)', ph: '72' },
        gsr: { title: 'Reference conductance', label: 'Known conductance (µS)', ph: '5' },
        spo2: { title: 'Reference SpO₂', label: 'SpO₂ from a pulse oximeter (%)', ph: '98' },
      }[sensor] || { title: 'Reference value', label: 'Reference', ph: '' };
      C.modal({
        title: meta.title, icon: 'settings', color: U.C.violet,
        body: C.form([
          { n: 'reference', l: meta.label, t: 'number', ph: meta.ph },
          ...(sensor === 'temp' ? [{ n: 'point', l: 'Calibration point', t: 'select', o: [{ v: 'low', l: 'Point 1 (e.g. room / cool)' }, { v: 'high', l: 'Point 2 (e.g. body / warm)' }] }] : []),
        ]), okText: 'Apply calibration',
        async onOk(v) {
          try {
            const r = await DeviceLink.referencePoint(sensor, +v.reference, v.point || 'low', Store.state.activePatient);
            PatientViews.wearState.cal = r.calibration || {};
            C.closeModal(); renderMain(); C.toast('Calibration updated');
          } catch (e) { C.toast(e.message, 'err'); }
        },
      });
    },
    async calReset(sensor) {
      const r = await DeviceLink.resetCalibration(sensor, Store.state.activePatient);
      PatientViews.wearState.cal = r.calibration || {};
      C.toast(`${sensor.toUpperCase()} calibration reset to defaults`, 'info'); renderMain();
    },

    /* ---- complication prediction ---- */
    runComplications() { loadComplications(true); },
    async saveComplications() {
      const p = Store.patient();
      try {
        await Store.api('/api/patients/' + encodeURIComponent(p.id) + '/complications', 'POST', {});
        C.toast('Run stored in model_results');
      } catch (e) { C.toast(e.message, 'err'); }
    },
    editClinical(id) {
      const p = Store.patient(id) || Store.patient();
      C.modal({
        title: 'Clinical data · ' + p.name, sub: 'Everything here feeds the complication engine', icon: 'stethoscope', color: U.C.violet,
        body: C.form(clinicalFields(p)) + `<div class="card-sub mt-14">Labs, medications and goals are edited on their own tabs below.</div>
          <div class="flex gap-6 mt-10 wrap">
            <button class="btn sm" data-act="editLabs">${U.icon('flask')} Labs (${(p.labs || []).length})</button>
            <button class="btn sm" data-act="editMeds">${U.icon('pill')} Medications (${(p.meds || []).length})</button>
            <button class="btn sm" data-act="editGoals">${U.icon('goal')} Goals (${(p.goals || []).length})</button>
          </div>`,
        okText: 'Save clinical data',
        async onOk(v) {
          try {
            await Store.updatePatient(p.id, v);
            C.closeModal(); await loadComplications(true); renderAll();
            C.toast('Clinical data saved' + (Store.isLive() ? ' to the database' : ''));
          } catch (e) { C.toast(e.message, 'err'); }
        },
      });
    },
    editLabs(id) { listEditor('labs', 'Laboratory results', id); },
    editMeds(id) { listEditor('meds', 'Medications & supplements', id); },
    editGoals(id) { listEditor('goals', 'Goals & targets', id); },

    /* ---- data source ---- */
    showSource() { sourceModal(); },
    async seedCohort() {
      C.toast('Writing labelled demo cohort into the database…', 'info');
      try { await Store.seedDemoCohort(); renderAll(); C.toast('Demo cohort seeded — every panel now reads real rows'); }
      catch (e) { C.toast('Seeding failed: ' + e.message, 'err'); }
    },
    async clearCohort() {
      C.confirm('Remove seeded demo rows', 'Deletes every row tagged <span class="mono">SYNTHETIC_DEMO</span> from the database. Real recordings are untouched.',
        async () => { try { await Store.clearDemoCohort(); renderAll(); C.toast('Seeded demo rows removed', 'info'); } catch (e) { C.toast(e.message, 'err'); } }, 'Remove');
    },
    async useDemoData() { await Store.useDemo(); renderAll(); C.toast('Showing built-in demo data', 'info'); },
    async useLiveData() { await Store.useLive(); renderAll(); C.toast(Store.isLive() ? 'Connected to the platform database' : 'Database unreachable', Store.isLive() ? 'ok' : 'err'); },

    /* ---- patients ---- */
    addPatient() {
      C.modal({
        title: 'Add patient', sub: 'Creates a synthetic demo record in local storage', icon: 'plus', color: U.C.pink,
        body: C.form(patientFields({})), okText: 'Create patient',
        async onOk(v) {
          if (!v.name) return C.toast('Name is required', 'err');
          if (!v.id) delete v.id;
          try {
            const p = await Store.addPatient(v);
            C.closeModal(); Store.setActivePatient(p.id);
            if (role() === 'doctor') route = 'registry';
            renderAll();
            C.toast(`${p.name} added (${p.id})` + (Store.isLive() ? ' · saved to database' : ''));
          } catch (e) { C.toast('Could not save: ' + e.message, 'err'); }
        },
      });
    },
    editPatient(id) {
      const raw = (Store.isLive() ? Store.patients() : Store.state.patients).find(p => p.id === id)
        || (Store.isLive() ? Store.patients() : Store.state.patients)[0];
      if (!raw) return;
      C.modal({
        title: 'Edit patient · ' + raw.name, sub: raw.id, icon: 'edit', color: U.C.violet,
        body: C.form(patientFields(raw)), okText: 'Save changes',
        async onOk(v) {
          delete v.id;
          try { await Store.updatePatient(raw.id, v); C.closeModal(); renderAll(); C.toast('Record updated' + (Store.isLive() ? ' in the database' : '')); }
          catch (e) { C.toast('Update failed: ' + e.message, 'err'); }
        },
      });
      const idf = U.$('#f_id'); if (idf) idf.disabled = true;
    },
    deletePatient(id) {
      const p = (Store.isLive() ? Store.patients() : Store.state.patients).find(x => x.id === id) || { name: id };
      C.confirm('Delete patient record',
        `This removes <b>${U.esc(p.name)}</b> (${id})${Store.isLive() ? ' and every linked recording from the platform database' : ' from the local demo dataset'}. This cannot be undone.`,
        async () => { try { await Store.removePatient(id); renderAll(); C.toast('Record deleted', 'info'); } catch (e) { C.toast(e.message, 'err'); } }, 'Delete');
    },
    openPatient(id) { Store.setActivePatient(id); route = role() === 'doctor' ? 'chart' : 'dashboard'; renderAll(); },
    async markReviewed(id) { await Store.updatePatient(id, { status: 'Active' }); renderAll(); C.toast('Marked as reviewed'); },
    switchPatient(id) { Store.setActivePatient(id); renderAll(); },

    /* ---- doctors ---- */
    addDoctor() {
      C.modal({
        title: 'Add doctor', sub: 'Adds a clinician to this workstation', icon: 'plus', color: U.C.violet,
        body: C.form(doctorFields({ status: 'Available', days: 'Mon–Fri', slot: '09:00 – 17:00', clinic: 'ENDO-TWIN Research Clinic, Delhi' })),
        okText: 'Add doctor',
        async onOk(v) {
          if (!v.name) return C.toast('Name is required', 'err');
          if (!/^dr\.?\s/i.test(v.name)) v.name = 'Dr. ' + v.name;
          try {
            const d = await Store.addDoctor(v); C.closeModal();
            if (role() === 'doctor') route = 'doctors';
            renderAll(); C.toast(`${d.name} added (${d.id})` + (Store.isLive() ? ' · saved to database' : ''));
          } catch (e) { C.toast('Could not save: ' + e.message, 'err'); }
        },
      });
    },
    editDoctor(id) {
      const d = Store.doctors().find(x => x.id === id) || Store.doctor();
      C.modal({
        title: 'Edit doctor · ' + d.name, sub: d.id, icon: 'edit', color: U.C.violet,
        body: C.form(doctorFields(d)), okText: 'Save changes',
        async onOk(v) {
          try { await Store.updateDoctor(d.id, v); C.closeModal(); renderAll(); C.toast('Clinician updated' + (Store.isLive() ? ' in the database' : '')); }
          catch (e) { C.toast('Update failed: ' + e.message, 'err'); }
        },
      });
    },
    deleteDoctor(id) {
      if (Store.doctors().length <= 1) return C.toast('At least one clinician is required', 'err');
      const d = Store.doctors().find(x => x.id === id);
      C.confirm('Remove clinician', `Remove <b>${U.esc(d.name)}</b> from this workstation? Assigned patients keep their record but lose this clinician link.`,
        async () => { try { await Store.removeDoctor(id); renderAll(); C.toast('Clinician removed', 'info'); } catch (e) { C.toast(e.message, 'err'); } }, 'Remove');
    },
    signInDoctor(id) { Store.setCurrentDoctor(id); renderAll(); C.toast('Signed in as ' + Store.doctor().name); },
    switchDoctor(id) { Store.setCurrentDoctor(id); renderAll(); },

    /* ---- clinical ---- */
    addNote() {
      const p = Store.patient();
      C.modal({
        title: 'Add clinical note', sub: `${p.name} · ${p.id}`, icon: 'note', color: U.C.sky,
        body: C.form([
          { n: 'patient', l: 'Patient', t: 'select', o: Store.patients().map(x => ({ v: x.id, l: `${x.name} · ${x.id}` })), v: p.id },
          { n: 'by', l: 'Author', v: Store.doctor().name },
          { n: 'text', l: 'Note', t: 'textarea', full: true, ph: 'Observation, plan, research caveats…' },
        ]), okText: 'Save note',
        async onOk(v) {
          if (!v.text) return C.toast('Note text is required', 'err');
          try {
            await Store.addNote(v.patient, v.text, v.by); Store.setActivePatient(v.patient);
            C.closeModal(); renderAll(); C.toast('Note saved to chart' + (Store.isLive() ? ' (database)' : ''));
          } catch (e) { C.toast('Could not save note: ' + e.message, 'err'); }
        },
      });
    },
    logSymptom() {
      const p = Store.patient();
      C.modal({
        title: 'Log symptom', sub: p.name, icon: 'heartbeat', color: U.C.pink,
        body: C.form([
          { n: 'name', l: 'Symptom', t: 'select', o: DemoData.SYMPTOM_POOL },
          { n: 'severity', l: 'Severity (1–5)', t: 'number', v: 3, min: 1, max: 5 },
          { n: 'note', l: 'Note (optional)', t: 'textarea', full: true },
        ]), okText: 'Log it',
        async onOk(v) {
          Store.addLog(p.id, 'Symptom', `${v.name} · severity ${v.severity}${v.note ? ' · ' + v.note : ''}`);
          try { await Store.addSymptom(p.id, { name: v.name, severity: +v.severity, notes: v.note }); } catch (e) { C.toast(e.message, 'err'); }
          C.closeModal(); renderAll(); C.toast('Symptom logged' + (Store.isLive() ? ' to the database' : ''));
        },
      });
    },
    async quickSymptom(name) {
      const pid = Store.patient().id;
      Store.addLog(pid, 'Symptom', `${name} · severity 3`);
      try { await Store.addSymptom(pid, { name, severity: 3 }); renderMain(); } catch (e) {}
      C.toast(name + ' logged' + (Store.isLive() ? ' to the database' : ''));
    },
    addLog() {
      const p = Store.patient();
      C.modal({
        title: 'New log entry', sub: p.name, icon: 'log', color: U.C.sky,
        body: C.form([
          { n: 'type', l: 'Type', t: 'select', o: ['Symptom', 'Meal', 'Medication', 'Sleep', 'Activity', 'Note'] },
          { n: 'text', l: 'Detail', full: true, ph: 'e.g. Oats + curd, 320 kcal' },
        ]), okText: 'Add entry',
        onOk(v) { if (!v.text) return C.toast('Detail required', 'err'); Store.addLog(p.id, v.type, v.text); C.closeModal(); renderMain(); C.toast('Entry added'); },
      });
    },
    addMeal() { actions.addLog(); },
    addMed() {
      C.modal({
        title: 'Add medication / supplement', icon: 'pill', color: U.C.orange,
        body: C.form([{ n: 'n', l: 'Item' }, { n: 'd', l: 'Dose' },
          { n: 't', l: 'Schedule', t: 'select', o: ['Morning', 'Afternoon', 'Night', 'After dinner'] },
          { n: 'k', l: 'Type', t: 'select', o: ['Supplement', 'Logged medication'] }]),
        okText: 'Add',
        onOk(v) { Store.addLog(Store.patient().id, 'Medication', `${v.n} ${v.d} · ${v.t}`); C.closeModal(); C.toast('Added to log'); },
      });
    },
    markTaken(name) { Store.addLog(Store.patient().id, 'Medication', name + ' taken'); C.toast(name.split(' ')[0] + ' marked taken'); },
    addGoal() {
      C.modal({ title: 'New goal', icon: 'goal', color: U.C.green,
        body: C.form([{ n: 'k', l: 'Goal' }, { n: 'target', l: 'Target' }, { n: 'ends', l: 'Ends', t: 'date' }]),
        okText: 'Create goal', onOk(v) { C.closeModal(); C.toast('Goal created: ' + (v.k || 'Untitled')); } });
    },
    addPlan() { actions.addGoal(); },
    editCycle() {
      const p = Store.patient();
      C.modal({
        title: 'Cycle settings', sub: p.name, icon: 'calendar', color: U.C.pink,
        body: C.form([
          { n: 'cycleDay', l: 'Current cycle day', t: 'number', v: p.cycleDay, min: 1, max: 90 },
          { n: 'cycleLen', l: 'Average cycle length', t: 'number', v: p.cycleLen, min: 15, max: 90 },
        ]), okText: 'Save',
        async onOk(v) {
          try { await Store.updatePatient(p.id, { cycleDay: +v.cycleDay, cycleLen: +v.cycleLen }); C.closeModal(); renderAll(); C.toast('Cycle updated'); }
          catch (e) { C.toast(e.message, 'err'); }
        },
      });
    },
    async cycleShift(dir) {
      const p = Store.patient();
      const d = U.clamp((p.cycleDay || 1) + (+dir), 1, p.cycleLen || 28);
      await Store.updatePatient(p.id, { cycleDay: d }); renderMain();
    },
    addAppointment() {
      C.modal({
        title: 'Book appointment', icon: 'calendar', color: U.C.sky,
        body: C.form([
          { n: 'pid', l: 'Patient', t: 'select', o: Store.patients().map(p => ({ v: p.id, l: `${p.name} · ${p.id}` })) },
          { n: 'doc', l: 'Clinician', t: 'select', o: Store.doctors().map(d => ({ v: d.id, l: d.name })) },
          { n: 'when', l: 'When', v: 'Tomorrow · 10:00 AM' },
          { n: 'kind', l: 'Type', t: 'select', o: ['Follow-up', 'Onboarding', 'Imaging review', 'Cycle review', 'Escalation review', 'Nutrition plan'] },
          { n: 'mode', l: 'Mode', t: 'select', o: ['In-clinic', 'Tele'] },
          { n: 'status', l: 'Status', t: 'select', o: ['Confirmed', 'Pending'] },
        ]), okText: 'Book',
        onOk(v) { Store.addAppointment(v); C.closeModal(); renderAll(); C.toast('Appointment booked'); },
      });
    },

    /* ---- generic / demo ---- */
    rerunModel() {
      C.toast('Running pcos_risk_gbm v2.4.1…', 'info');
      setTimeout(() => { Store.invalidate(); renderMain(); C.toast('Model run complete · outputs refreshed'); }, 900);
    },
    trainModel() {
      C.modal({ title: 'New training run', sub: 'Leakage-safe patient-level split', icon: 'flask', color: U.C.violet,
        body: C.form([{ n: 'model', l: 'Model', t: 'select', o: DemoData.models.map(m => m.n) },
          { n: 'split', l: 'Split', t: 'select', o: ['70/15/15 patient-level', '60/20/20 patient-level', '5-fold grouped CV'] },
          { n: 'epochs', l: 'Epochs', t: 'number', v: 30 }]),
        okText: 'Queue run', onOk() { C.closeModal(); C.toast('Training run queued (demo)'); } });
    },
    runDiagnostics() {
      C.toast('Running diagnostics…', 'info');
      setTimeout(() => { renderMain(); C.toast('8 PASS · 2 WARN · 0 FAIL'); }, 800);
    },
    genReport(kind) {
      const p = Store.patient();
      const k = kind || 'doctor';
      if (k === 'csv' || k === 'json') {
        const rows = ['metric,value,provenance',
          `heart_rate,${p.vitals.hr},MEASURED`, `hrv_rmssd,${p.vitals.hrv},DERIVED`,
          `skin_temp,${p.vitals.temp},MEASURED`, `gsr,${p.vitals.gsr},MEASURED`,
          `steps,${p.vitals.steps},DERIVED`, `spo2,${p.vitals.spo2},MEASURED`,
          `cycle_day,${p.cycleDay},CLINICALLY_ENTERED`, `risk_signal,${p.risk},MODEL_INFERRED`].join('\n');
        U.download(`${p.id}_export.${k === 'csv' ? 'csv' : 'json'}`, k === 'csv' ? rows : JSON.stringify({ patient: p.id, vitals: p.vitals, risk: p.risk, provenance: 'see docs' }, null, 2));
        return C.toast('Export downloaded');
      }
      C.modal({
        title: (k === 'patient' ? 'Patient' : 'Doctor') + ' report preview', sub: `${p.name} · ${p.id}`, icon: 'report', color: U.C.pink,
        okText: 'Download',
        body: `<div class="log-box" style="max-height:340px">
          <div><b>ENDO-TWIN NEXUS — ${k === 'patient' ? 'Patient Summary' : 'Clinical Research Report'}</b></div>
          <div class="dim">Generated ${U.fmtDate(new Date())} ${U.fmtTime(new Date())}</div>
          <div>&nbsp;</div>
          <div>Participant : ${p.name} (${p.id}), ${p.age} y</div>
          <div>Clinician   : ${(Store.doctors().find(d => d.id === p.doctorId) || {}).name || '—'}</div>
          <div>Cohort      : ${p.cohort}</div>
          <div>&nbsp;</div>
          <div><b>OBSERVED</b>  HR ${p.vitals.hr} bpm · Skin temp ${p.vitals.temp} °C · SpO₂ ${p.vitals.spo2}% · Steps ${p.vitals.steps}</div>
          <div><b>DERIVED</b>   HRV ${p.vitals.hrv} ms · Sleep ${p.vitals.sleep} h · Stress ${p.vitals.gsr} µS</div>
          <div><b>ENTERED</b>   Cycle day ${p.cycleDay}/${p.cycleLen} · ${p.symptoms.length} active symptoms</div>
          <div><b>IMAGE</b>     Follicles ${p.ultrasound.follicles} · Volume ${p.ultrasound.volume} cm³ · ${p.ultrasound.pattern}</div>
          <div><b>MODEL</b>     Risk signal ${p.risk}% (${U.riskTone(p.risk).label}) · pcos_risk_gbm v2.4.1 · CI ±9</div>
          <div>&nbsp;</div>
          <div><b>Top drivers</b></div>
          ${p.drivers.slice(0, 4).map(d => `<div>  • ${d.k} (${d.v})</div>`).join('')}
          <div>&nbsp;</div>
          <div><b>Data quality</b> ${(p.quality * 100).toFixed(0)}% · adherence ${p.adherence}%</div>
          <div class="warn">LIMITATIONS: PPG-derived HRV is less accurate than ECG; no external validation;
            serum hormones unknown; ultrasound read is IMAGE-DERIVED and requires clinician interpretation.</div>
          <div class="err">Research / risk-screening output — not a medical diagnosis.</div>
        </div>`,
        onOk() {
          U.download(`${p.id}_${k}_report.txt`, U.$('#modalBody').innerText);
          C.closeModal(); C.toast('Report downloaded');
        },
      });
    },
    viewReport(id) { actions.genReport('doctor'); },
    exportCohort() {
      const rows = ['patient_id,name,age,cohort,risk,quality,adherence,cycle_len,status']
        .concat(Store.patients().map(p => [p.id, p.name, p.age, p.cohort, p.risk, p.quality, p.adherence, p.cycleLen, p.status].join(',')));
      U.download('endotwin_cohort_export.csv', rows.join('\n'));
      C.toast('Cohort CSV exported (de-identified demo data)');
    },
    shareDoctor() {
      const p = Store.patient();
      C.modal({ title: 'Secure share link', sub: p.name, icon: 'share', color: U.C.violet,
        body: `<p class="small muted" style="line-height:1.7">A one-time link has been created for the selected scope. It expires in 7 days and every access is written to the audit log.</p>
          <div class="log-box mt-10">https://share.endotwin.local/${p.id.toLowerCase()}/${Math.random().toString(36).slice(2, 10)}</div>`,
        okText: 'Copy link', onOk() { C.closeModal(); C.toast('Link copied (demo)'); } });
    },
    uploadScan() {
      C.modal({ title: 'Upload ultrasound', sub: 'JPEG / PNG / DICOM', icon: 'scan', color: U.C.orange,
        body: `<div class="empty" style="border:1px dashed var(--border-2);border-radius:14px">
          <div class="ec">${U.icon('export', 'ic', 'width:26px;height:26px')}</div>
          Drop a file here or click to browse<br><span class="small">Images are processed locally; nothing is uploaded.</span></div>`,
        okText: 'Simulate upload',
        onOk() { C.closeModal(); C.toast('Scan queued for segmentation (demo)'); } });
    },
    analyseScan() {
      C.toast('Running follicle_seg_unet v1.2.2…', 'info');
      setTimeout(() => { renderMain(); C.toast('Segmentation complete · IMAGE-DERIVED result'); }, 900);
    },
    signOff() { C.toast('Read signed off by ' + Store.doctor().name); },
    pairDevice() {
      C.modal({ title: 'Pair wearable', icon: 'bluetooth', color: U.C.cyan,
        body: `<div class="log-box"><div>Scanning BLE…</div><div class="ok">Found: ENDO-TWIN ESP32-S3 (ETN-W44) · -52 dBm</div>
          <div class="dim">Found: Unknown device · -81 dBm</div></div>`,
        okText: 'Pair ETN-W44', onOk() { C.closeModal(); C.toast('Device paired (demo)'); } });
    },
    recalibrate() { C.toast('Self-test passed · sensors calibrated'); },
    firmware() { C.toast('Firmware v8.7.1 is current', 'info'); },
    pauseStream() { Store.setSetting('liveStream', !Store.state.settings.liveStream); startLive(); C.toast(Store.state.settings.liveStream ? 'Streaming resumed' : 'Streaming paused', 'info'); },
    newPost() {
      C.modal({ title: 'New community post', icon: 'users', color: U.C.pink,
        body: C.form([{ n: 't', l: 'Title', full: true }, { n: 'b', l: 'Message', t: 'textarea', full: true }]),
        okText: 'Post', onOk() { C.closeModal(); C.toast('Posted to community (demo)'); } });
    },
    readArticle(title) { C.modal({ title: title, icon: 'book', color: U.C.sky, footer: null,
      body: `<p class="small" style="line-height:1.8;color:var(--text-2)">This is a demo stub for the reviewed explainer “${U.esc(title)}”.
        In the full build the Knowledge Hub renders reviewed markdown with citations, reading level and a
        last-reviewed date, plus an explicit statement of what the platform cannot tell you.</p>` }); },
    rsvp(t) { C.toast('RSVP confirmed: ' + t); },
    reply(pid) { Store.setActivePatient(pid); actions.addNote(); },
    editClinic() { C.toast('Clinic profile editing is available to site admins', 'info'); },
    resetDemo() {
      C.confirm('Reset demo data', 'This restores the original demo patients, doctors and settings, discarding your local changes.',
        () => { Store.reset(); route = 'dashboard'; renderAll(); C.toast('Demo data restored'); }, 'Reset');
    },
    setSetting(key, elm) {
      const v = elm.type === 'checkbox' ? elm.checked : elm.value;
      Store.setSetting(key, v);
      if (key === 'liveStream') startLive();
      C.toast('Preference saved', 'info');
    },
    toggleSeries(k) {
      PatientViews.liveState.visible[k] = !PatientViews.liveState.visible[k];
      renderMain();
    },
    liveWindow(_, elm) { PatientViews.liveState.window = elm.value; renderMain(); },
    recentTab(i) {
      const p = Store.patient();
      const sets = [
        [{ name: 'Risk %', color: U.C.violet, data: p.trend30.risk.filter((_, x) => x % 3 === 0) }],
        [{ name: 'HRV', color: U.C.pink, data: p.trend30.hrv.filter((_, x) => x % 3 === 0) }],
        [{ name: 'Symptom load', color: U.C.orange, data: p.trend30.gsr.map(x => x * 100).filter((_, x) => x % 3 === 0) }],
        [{ name: 'Sleep h', color: U.C.cyan, data: p.trend30.sleep.filter((_, x) => x % 3 === 0) }],
      ][+i];
      U.$('#recentChart').innerHTML = Chart.lines(sets, { h: 132, area: true, dots: true, xlabels: ['Jul', 'Aug', 'Sep', 'Oct'] });
      U.$$('[data-act="recentTab"]').forEach((b, x) => b.classList.toggle('on', x === +i));
    },
    expandLive() { route = 'live'; renderAll(); },
    deleteLog() { C.toast('Entry removed', 'info'); },
    scope() { C.toast('Share scope updated', 'info'); },
  };

  /* ------------------------------- binding ------------------------------- */
  function bindMain() {
    const main = U.$('#main');
    U.$$('[data-go]', main).forEach(e => e.onclick = ev => { ev.preventDefault(); go(e.dataset.go); });
    U.$$('[data-act]', main).forEach(e => {
      const fn = actions[e.dataset.act];
      if (!fn) return;
      const handler = ev => {
        ev.stopPropagation();
        const arg = e.dataset.arg != null ? e.dataset.arg : (e.tagName === 'SELECT' ? e.value : undefined);
        fn(arg, e);
      };
      if (e.tagName === 'SELECT' || e.type === 'checkbox') e.onchange = handler;
      else e.onclick = handler;
    });
    // registry live filter
    const rs = U.$('#registrySearch', main);
    if (rs) rs.oninput = () => {
      const q = rs.value.toLowerCase();
      U.$$('#registryTable tbody tr').forEach(tr => {
        tr.style.display = tr.innerText.toLowerCase().includes(q) ? '' : 'none';
      });
    };
  }

  function bindShell() {
    U.$$('#navList').forEach(() => {});
    document.addEventListener('click', e => {
      const nav = e.target.closest('#navList [data-go]');
      if (nav) { go(nav.dataset.go); return; }
      if (!e.target.closest('#profileSwitch')) U.$('#switchMenu').classList.remove('open');
      if (!e.target.closest('#searchBar')) U.$('#searchResults').classList.remove('open');
      const smAct = e.target.closest('#switchMenu [data-act]');
      if (smAct && actions[smAct.dataset.act]) { closeMenus(); actions[smAct.dataset.act](smAct.dataset.arg, smAct); }
      const smGo = e.target.closest('#switchMenu [data-go]');
      if (smGo) { closeMenus(); go(smGo.dataset.go); }
    });

    U.$('#profileSwitch').onclick = e => {
      if (e.target.closest('.switch-menu')) return;
      U.$('#switchMenu').classList.toggle('open');
    };

    const chip = U.$('#dsChip');
    if (chip) chip.onclick = () => sourceModal();

    U.$('#btnTheme').onclick = () => {
      const t = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
      document.documentElement.dataset.theme = t; Store.setTheme(t);
      renderMain(); C.toast(t === 'dark' ? 'Dark theme' : 'Light theme', 'info');
    };

    U.$('#btnNotify').onclick = () => {
      C.modal({ title: 'Notifications', icon: 'bell', color: U.C.pink, footer: null,
        body: Store.state.notifications.map(n => `<div class="tl-item">
          <div class="tl-ico" style="background:${U.soft(U.C.pink, .15)};color:${U.C.pink}">${U.icon('bell')}</div>
          <div><div class="tl-title">${n.t}</div><div class="small muted">${n.b}</div></div>
          <div class="tl-meta">${n.when}</div></div>`).join('') });
      Store.state.notifications.forEach(n => n.read = true); Store.save(); renderTop();
    };

    /* search */
    const input = U.$('#globalSearch'), box = U.$('#searchResults');
    const allTargets = () => {
      const t = [];
      views().nav.forEach(g => g.items.forEach(i => t.push({ label: i.label, kind: 'Page', go: i.id, icon: i.icon })));
      Store.patients().forEach(p => t.push({ label: `${p.name} · ${p.id}`, kind: 'Patient', patient: p.id, icon: 'user' }));
      Store.doctors().forEach(d => t.push({ label: `${d.name} · ${d.specialty}`, kind: 'Doctor', doctor: d.id, icon: 'stethoscope' }));
      DemoData.knowledge.forEach(k => t.push({ label: k.t, kind: 'Article', go: 'knowledge', icon: 'book' }));
      return t;
    };
    input.oninput = () => {
      const q = input.value.trim().toLowerCase();
      if (!q) { box.classList.remove('open'); return; }
      const hits = allTargets().filter(t => t.label.toLowerCase().includes(q)).slice(0, 10);
      box.innerHTML = hits.length ? hits.map((h, i) => `<div class="sr-item" data-i="${i}">
        ${U.icon(h.icon)}<span>${U.esc(h.label)}</span><span class="sr-kind">${h.kind}</span></div>`).join('')
        : `<div class="sr-empty">No matches for “${U.esc(input.value)}”</div>`;
      box.classList.add('open');
      U.$$('.sr-item', box).forEach((el, i) => el.onclick = () => {
        const h = hits[i];
        if (h.patient) { Store.setActivePatient(h.patient); route = role() === 'doctor' ? 'chart' : 'dashboard'; renderAll(); }
        else if (h.doctor) { Store.setCurrentDoctor(h.doctor); if (role() === 'doctor') route = 'doctors'; renderAll(); }
        else go(h.go);
        input.value = ''; box.classList.remove('open');
      });
    };
    document.addEventListener('keydown', e => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); input.focus(); }
      if (e.key === 'Escape') { C.closeModal(); closeMenus(); }
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'd') { e.preventDefault(); setRole(role() === 'doctor' ? 'patient' : 'doctor'); }
    });

    U.$('#devicePill').onclick = () => go(role() === 'doctor' ? 'fleet' : 'wearable');

    /* off-canvas sidebar (small screens) */
    const scrim = U.el('<div class="sidebar-scrim"></div>');
    document.body.appendChild(scrim);
    const toggleSidebar = open => {
      U.$('#sidebar').classList.toggle('open', open);
      scrim.classList.toggle('open', open);
    };
    U.$('#btnMenu').onclick = e => { e.stopPropagation(); toggleSidebar(!U.$('#sidebar').classList.contains('open')); };
    scrim.onclick = () => toggleSidebar(false);
    U.$('#navList').addEventListener('click', () => toggleSidebar(false));
  }

  function closeMenus() {
    U.$('#switchMenu').classList.remove('open');
    U.$('#searchResults').classList.remove('open');
  }

  /* -------------------------------- clock -------------------------------- */
  function tickClock() {
    const now = new Date();
    U.$('#clockDate').textContent = U.fmtDate(now);
    U.$('#clockTime').textContent = U.fmtTime(now);
  }

  /* --------------------------------- init -------------------------------- */
  async function init() {
    document.documentElement.dataset.theme = Store.state.theme || 'dark';
    bindShell();
    tickClock(); setInterval(tickClock, 1000 * 20);
    renderAll();                                  // paint immediately…
    await Store.boot();                           // …then bind to the real database
    /* let [data-act] buttons work inside modals too, not just in #main */
    const rawModal = C.modal;
    C.modal = function (o) {
      const root = rawModal(o);
      U.$$('[data-act]', root).forEach(e => {
        const fn = actions[e.dataset.act];
        if (!fn) return;
        e.onclick = ev => { ev.stopPropagation(); fn(e.dataset.arg, e); };
      });
      return root;
    };

    Store.onChange(renderAll);
    DeviceLink.onChange(() => {
      renderTop();
      if (route === 'wearable' || route === 'livedevice') renderMain();
    });
    DeviceLink.start(6000);
    renderAll();
    if (Store.isLive() && !Store.dbEmpty()) C.toast('Connected to the platform database', 'ok');
    else if (!Store.isLive()) C.toast('Backend not reachable — showing built-in demo data', 'info');
  }

  return { init, go, actions, renderAll, renderSourceChip, sourceModal, get route() { return route; } };
})();

document.addEventListener('DOMContentLoaded', App.init);
