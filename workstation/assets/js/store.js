/* ============================================================
   ENDO-TWIN NEXUS — state store (localStorage backed)
   ============================================================ */
const Store = (() => {
  const KEY = 'endotwin-nexus-workstation-v1';

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
  const patients = () => state.patients.map(p => patient(p.id));
  const doctors = () => state.doctors;
  const doctor = id => state.doctors.find(d => d.id === (id || state.currentDoctor)) || state.doctors[0];

  /* ------------------------------- CRUD -------------------------------- */
  function addPatient(rec) {
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
  function updatePatient(id, patch) {
    const i = state.patients.findIndex(p => p.id === id);
    if (i < 0) return null;
    state.patients[i] = Object.assign({}, state.patients[i], patch);
    invalidate(id); save();
    return state.patients[i];
  }
  function removePatient(id) {
    state.patients = state.patients.filter(p => p.id !== id);
    if (state.activePatient === id && state.patients[0]) state.activePatient = state.patients[0].id;
    invalidate(id); save();
  }
  function addDoctor(rec) {
    const d = Object.assign({
      id: 'DR-' + (1001 + state.doctors.length), name: 'New Clinician', specialty: 'General',
      reg: '—', clinic: 'ENDO-TWIN Research Clinic, Delhi', email: '—', phone: '—',
      exp: 1, room: '—', status: 'Available', days: 'Mon–Fri', slot: '09:00 – 17:00',
    }, rec);
    if (state.doctors.some(x => x.id === d.id)) d.id = U.uid('DR');
    state.doctors.push(d); save();
    return d;
  }
  function updateDoctor(id, patch) {
    const i = state.doctors.findIndex(d => d.id === id);
    if (i < 0) return null;
    state.doctors[i] = Object.assign({}, state.doctors[i], patch);
    save(); return state.doctors[i];
  }
  function removeDoctor(id) {
    state.doctors = state.doctors.filter(d => d.id !== id);
    if (state.currentDoctor === id && state.doctors[0]) state.currentDoctor = state.doctors[0].id;
    save();
  }
  function addNote(pid, text, by) {
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

  return {
    get state() { return state; },
    save, reset, load, invalidate,
    patient, patients, doctors, doctor,
    addPatient, updatePatient, removePatient,
    addDoctor, updateDoctor, removeDoctor,
    addNote, addLog, logs, addAppointment,
    setRole, setActivePatient, setCurrentDoctor, setTheme, setSetting,
  };
})();
