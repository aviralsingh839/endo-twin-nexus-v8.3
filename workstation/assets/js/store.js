/* ============================================================
   ENDO-TWIN NEXUS — state store (localStorage backed)
   ============================================================ */
const Store = (() => {
  const KEY = 'endotwin-nexus-workstation-v1';

  /* =====================================================================
     DATA SOURCE
     ---------------------------------------------------------------------
     'live'  -> every record comes from the real SQLite database that the
                PySide6 platform writes to (via /api/*). Nothing is invented:
                missing measurements stay null and render as '—'.
     'demo'  -> the browser-only sample dataset (no backend reachable, or the
                user explicitly asked for it). Clearly flagged in the UI.
     ===================================================================== */
  let mode = 'demo';                 // resolved by boot()
  let server = { health: null, patients: [], doctors: [], error: null };
  const listeners = [];
  const onChange = fn => listeners.push(fn);
  const emit = () => listeners.forEach(fn => { try { fn(); } catch (e) {} });

  async function api(path, method = 'GET', body) {
    const res = await fetch(path, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      cache: 'no-store',
    });
    const txt = await res.text();
    let json = {};
    try { json = txt ? JSON.parse(txt) : {}; } catch (e) { json = { error: txt }; }
    if (!res.ok) throw new Error(json.error || ('HTTP ' + res.status));
    return json;
  }

  /** Contact the backend and decide live vs demo. Never throws. */
  async function boot() {
    if (state.settings.dataSource === 'demo') { mode = 'demo'; return mode; }
    try {
      const b = await api('/api/bootstrap');
      server = { health: b.health, patients: b.patients || [], doctors: b.doctors || [], error: null };
      mode = 'live';
      if (server.patients.length && !server.patients.some(p => p.id === state.activePatient))
        state.activePatient = server.patients[0].id;
      if (server.doctors.length && !server.doctors.some(d => d.id === state.currentDoctor))
        state.currentDoctor = server.doctors[0].id;
      invalidate();
    } catch (e) {
      server = { health: null, patients: [], doctors: [], error: String(e.message || e) };
      mode = 'demo';
    }
    return mode;
  }
  async function refresh() {
    if (mode !== 'live') return;
    try {
      const b = await api('/api/bootstrap');
      server = { health: b.health, patients: b.patients || [], doctors: b.doctors || [], error: null };
      invalidate(); emit();
    } catch (e) { /* keep last good snapshot */ }
  }
  const isLive = () => mode === 'live';
  const health = () => server.health;
  const dbEmpty = () => mode === 'live' && (!server.patients || !server.patients.length);
  const sourceLabel = () => (mode === 'live'
    ? (dbEmpty() ? 'LIVE DB · EMPTY' : 'LIVE DATABASE')
    : 'DEMO DATA');

  async function useDemo() { state.settings.dataSource = 'demo'; mode = 'demo'; invalidate(); save(); emit(); }
  async function useLive() { state.settings.dataSource = 'auto'; save(); await boot(); emit(); }
  async function seedDemoCohort() { await api('/api/seed-demo', 'POST', {}); await refresh(); }
  async function clearDemoCohort() { await api('/api/clear-demo', 'POST', {}); await refresh(); }

  /* --------- shape a database record like DemoData.hydrate() does -------
     Anything the database does not hold stays null / empty — we never
     fabricate a measurement just to fill a chart.                        */
  function hydrateLive(rec) {
    const arr = v => (Array.isArray(v) ? v : []);
    const live = Object.assign({ hr: [], hrv: [], temp: [], gsr: [], steps: [], spo2: [] }, rec.live || {});
    const trend30 = Object.assign({ hr: [], hrv: [], temp: [], gsr: [], sleep: [], steps: [], risk: [], weight: [] }, rec.trend30 || {});
    Object.keys(live).forEach(k => { live[k] = arr(live[k]); });
    Object.keys(trend30).forEach(k => { trend30[k] = arr(trend30[k]); });

    const vitals = Object.assign({ hr: null, hrv: null, temp: null, gsr: null, steps: null, spo2: null, sleep: null, resp: null, bp: null, bmi: null }, rec.vitals || {});
    if (vitals.bmi == null && rec.height && rec.weight) vitals.bmi = U.round(rec.weight / Math.pow(rec.height / 100, 2), 1);

    const ultrasound = rec.ultrasound || { date: null, follicles: null, largest: null, volume: null, pattern: 'No study on file', quality: null, source: null };

    const timeline = [];
    if (rec.lastSync) timeline.push({ t: rec.lastSync, icon: 'watch', color: U.C.green, title: 'Sensor session recorded', meta: (rec.sessionCount || 0) + ' sessions on file' });
    arr(rec.symptoms).slice(0, 3).forEach(s => timeline.push({ t: s.when || '—', icon: 'heartbeat', color: U.C.pink, title: 'Symptom logged', meta: `${s.name} · severity ${s.severity}` }));
    arr(rec.notes).slice(0, 2).forEach(n => timeline.push({ t: n.when || '—', icon: 'note', color: U.C.sky, title: 'Clinician note', meta: n.by || 'Clinician' }));
    if (ultrasound.date) timeline.push({ t: ultrasound.date, icon: 'scan', color: U.C.violet, title: 'Ultrasound study', meta: ultrasound.pattern || '—' });

    const goals = [
      { k: 'Data consistency', v: rec.adherence == null ? null : Math.round(rec.adherence), color: 'linear-gradient(90deg,#5b4bf0,#7c5cff)' },
      { k: 'Activity goal', v: vitals.steps == null ? null : U.clamp(Math.round((vitals.steps / 8000) * 100), 0, 100), color: 'linear-gradient(90deg,#fb923c,#fbbf24)' },
      { k: 'Sleep goal', v: vitals.sleep == null ? null : U.clamp(Math.round((vitals.sleep / 8) * 100), 0, 100), color: 'linear-gradient(90deg,#22d3ee,#38bdf8)' },
      { k: 'Signal quality', v: rec.quality == null ? null : Math.round(rec.quality * 100), color: 'linear-gradient(90deg,#ff4d8d,#f43f75)' },
    ];

    const appt = state.appointments.find(a => a.pid === rec.id);
    return Object.assign({
      meds: [], labs: [], symptoms: [], notes: [], reports: [], drivers: [],
    }, rec, {
      initials: U.initials(rec.name || rec.id),
      bmi: rec.bmi != null ? rec.bmi : vitals.bmi,
      lastSync: rec.lastSync || 'No sync yet',
      nextVisit: appt ? (appt.when || appt.date || null) : null,
      live, trend30, vitals, ultrasound, timeline, goals,
      notes: (state.notes[rec.id] || []).concat(arr(rec.notes)),
      isLive: true,
    });
  }

  const defaults = () => ({
    version: 1,
    role: 'patient',                 // 'patient' | 'doctor'
    theme: 'dark',
    activePatient: 'ETN-2041',       // patient viewed in patient mode / opened in doctor mode
    currentDoctor: 'DR-1001',
    patients: DemoData.base.map(p => Object.assign({}, p)),
    doctors: DemoData.doctors.map(d => Object.assign({}, d)),
    notes: {},                       // pid -> [{by,when,text}]
    logs: {},                        // pid -> [{when, type, text}]
    appointments: DemoData.appointments.map(a => Object.assign({}, a)),
    settings: {
      units: 'metric', liveStream: true, notifications: true, shareWithDoctor: true,
        localOnly: true, autoReport: false, sampleRate: '50 Hz', language: 'English',
      dataSource: 'auto',            // 'auto' -> real database when reachable, else demo
    },
    notifications: [
      { t: 'Model run complete', b: 'pcos_risk_gbm v2.4.1 finished for 3 records.', when: '6 min ago', read: false },
      { t: 'Wearable battery low', b: 'ETN-W02 is at 23%.', when: '38 min ago', read: false },
      { t: 'New doctor note', b: 'Dr. Ananya Rao added a note to ETN-2042.', when: '2 h ago', read: false },
    ],
  });

  let cache = {};
  let state = load();

  function load() {
    try {
      const raw = localStorage.getItem(KEY);
      if (!raw) return defaults();
      const s = JSON.parse(raw);
      const d = defaults();
      // shallow merge so new fields appear after upgrades
      return Object.assign(d, s, { settings: Object.assign(d.settings, s.settings || {}) });
    } catch (e) { return defaults(); }
  }
  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {}
  }
  function reset() { state = defaults(); cache = {}; save(); }

  /* -------------------------- cached hydration -------------------------- */
  function invalidate(id) { if (id) delete cache[id]; else cache = {}; }
  function patient(id) {
    id = id || state.activePatient;
    if (mode === 'live') {
      const rec = server.patients.find(p => p.id === id) || server.patients[0];
      if (!rec) return null;
      const key = 'live|' + JSON.stringify(rec).length + '|' + (state.notes[rec.id] || []).length;
      if (!cache[rec.id] || cache[rec.id].__key !== key) {
        const h = hydrateLive(rec); h.__key = key; cache[rec.id] = h;
      }
      return cache[rec.id];
    }
    const raw = state.patients.find(p => p.id === id) || state.patients[0];
    if (!raw) return null;
    const key = raw.id + '|' + JSON.stringify(raw).length + '|' + raw.risk + raw.cycleDay + raw.weight;
    if (!cache[raw.id] || cache[raw.id].__key !== key) {
      const h = DemoData.hydrate(raw);
      h.__key = key;
      h.notes = (state.notes[raw.id] || []).concat(h.notes);
      cache[raw.id] = h;
    }
    return cache[raw.id];
  }
  const rawPatients = () => (mode === 'live' ? server.patients : state.patients);
  const patients = () => rawPatients().map(p => patient(p.id)).filter(Boolean);
  const doctors = () => (mode === 'live' ? server.doctors : state.doctors);
  const doctor = id => doctors().find(d => d.id === (id || state.currentDoctor)) || doctors()[0] || null;

  /* ------------------------------- CRUD -------------------------------- */
  async function addPatient(rec) {
    if (mode === 'live') {
      const res = await api('/api/patients', 'POST', rec || {});
      await refresh();
      return res.patient || res;
    }
    const p = Object.assign({
      id: 'ETN-' + (2051 + state.patients.length),
      name: 'New Participant', age: 25, gender: 'Female', city: '—', phone: '—', email: '—',
      height: 162, weight: 60, blood: 'O+', cycleLen: 28, cycleDay: 1, risk: 40,
      doctorId: state.currentDoctor, status: 'Active', cohort: 'Chrono-PCOS Cohort A',
      joined: new Date().toISOString().slice(0, 10), device: 'Not paired', battery: 0,
      adherence: 60, quality: 0.8,
    }, rec);
    if (state.patients.some(x => x.id === p.id)) p.id = U.uid('ETN');
    state.patients.unshift(p);
    invalidate(p.id); save();
    return p;
  }
  async function updatePatient(id, patch) {
    if (mode === 'live') {
      const res = await api('/api/patients/' + encodeURIComponent(id), 'PATCH', patch || {});
      await refresh();
      return res.patient || res;
    }
    const i = state.patients.findIndex(p => p.id === id);
    if (i < 0) return null;
    state.patients[i] = Object.assign({}, state.patients[i], patch);
    invalidate(id); save();
    return state.patients[i];
  }
  async function removePatient(id) {
    if (mode === 'live') {
      await api('/api/patients/' + encodeURIComponent(id), 'DELETE', {});
      if (state.activePatient === id) state.activePatient = (server.patients.find(p => p.id !== id) || {}).id || state.activePatient;
      await refresh();
      return;
    }
    state.patients = state.patients.filter(p => p.id !== id);
    if (state.activePatient === id && state.patients[0]) state.activePatient = state.patients[0].id;
    invalidate(id); save();
  }
  async function addDoctor(rec) {
    if (mode === 'live') {
      const res = await api('/api/doctors', 'POST', rec || {});
      await refresh();
      return res.doctor || res;
    }
    const d = Object.assign({
      id: 'DR-' + (1001 + state.doctors.length), name: 'New Clinician', specialty: 'General',
      reg: '—', clinic: 'ENDO-TWIN Research Clinic, Delhi', email: '—', phone: '—',
      exp: 1, room: '—', status: 'Available', days: 'Mon–Fri', slot: '09:00 – 17:00',
    }, rec);
    if (state.doctors.some(x => x.id === d.id)) d.id = U.uid('DR');
    state.doctors.push(d); save();
    return d;
  }
  async function updateDoctor(id, patch) {
    if (mode === 'live') {
      const res = await api('/api/doctors/' + encodeURIComponent(id), 'PATCH', patch || {});
      await refresh();
      return res.doctor || res;
    }
    const i = state.doctors.findIndex(d => d.id === id);
    if (i < 0) return null;
    state.doctors[i] = Object.assign({}, state.doctors[i], patch);
    save(); return state.doctors[i];
  }
  async function removeDoctor(id) {
    if (mode === 'live') {
      await api('/api/doctors/' + encodeURIComponent(id), 'DELETE', {});
      await refresh();
      return;
    }
    state.doctors = state.doctors.filter(d => d.id !== id);
    if (state.currentDoctor === id && state.doctors[0]) state.currentDoctor = state.doctors[0].id;
    save();
  }
  async function addNote(pid, text, by) {
    if (mode === 'live') {
      await api('/api/notes', 'POST', { patientId: pid, text, by: by || (doctor() || {}).name });
      await refresh();
      return;
    }
    if (!state.notes[pid]) state.notes[pid] = [];
    state.notes[pid].unshift({ by: by || doctor().name, when: U.fmtShort(new Date()), text });
    invalidate(pid); save();
  }
  function addLog(pid, type, text) {
    if (!state.logs[pid]) state.logs[pid] = [];
    state.logs[pid].unshift({ when: U.fmtTime(new Date()), type, text });
    save();
  }
  const logs = pid => state.logs[pid] || [];
  function addAppointment(a) { state.appointments.unshift(a); save(); }

  /* ------------------------------ setters ------------------------------- */
  function setRole(r) { state.role = r; save(); }
  function setActivePatient(id) { state.activePatient = id; save(); }
  function setCurrentDoctor(id) { state.currentDoctor = id; save(); }
  function setTheme(t) { state.theme = t; save(); }
  function setSetting(k, v) { state.settings[k] = v; save(); }

  /** Log a symptom / cycle entry / report into the real database when live. */
  async function addSymptom(pid, entry) {
    if (mode === 'live') { await api('/api/symptoms', 'POST', Object.assign({ patientId: pid }, entry)); await refresh(); return true; }
    addLog(pid, 'symptom', `${entry.name} · severity ${entry.severity}`);
    return false;
  }
  async function addCycleEntry(pid, entry) {
    if (mode === 'live') { await api('/api/cycles', 'POST', Object.assign({ patientId: pid }, entry)); await refresh(); return true; }
    addLog(pid, 'cycle', 'Cycle entry ' + (entry.startDate || ''));
    return false;
  }
  async function saveReport(pid, report) {
    if (mode === 'live') { await api('/api/reports', 'POST', Object.assign({ patientId: pid }, report)); await refresh(); return true; }
    addLog(pid, 'report', report.title || 'Report');
    return false;
  }

  return {
    get state() { return state; },
    save, reset, load, invalidate,
    patient, patients, doctors, doctor,
    addPatient, updatePatient, removePatient,
    addDoctor, updateDoctor, removeDoctor,
    addNote, addLog, logs, addAppointment,
    setRole, setActivePatient, setCurrentDoctor, setTheme, setSetting,
    addSymptom, addCycleEntry, saveReport,
    boot, refresh, isLive, health, dbEmpty, sourceLabel, useDemo, useLive,
    seedDemoCohort, clearDemoCohort, onChange, api,
    get mode() { return mode; },
    get serverError() { return server.error; },
  };
})();
