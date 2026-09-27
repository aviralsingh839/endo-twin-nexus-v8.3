/* ============================================================
   ENDO-TWIN NEXUS — demo dataset (synthetic, research demo only)
   NOTE: every value here is SYNTHETIC. No real patient data.
   ============================================================ */
const DemoData = (() => {

  /* ------------------------------ DOCTORS ------------------------------ */
  const doctors = [
    { id: 'DR-1001', name: 'Dr. Ananya Rao',      specialty: 'Endocrinology',            reg: 'MCI-88213', clinic: 'ENDO-TWIN Research Clinic, Delhi', email: 'a.rao@endotwin.health',    phone: '+91 98110 22113', exp: 12, room: 'Consult 2', status: 'Available',  days: 'Mon–Fri', slot: '09:00 – 16:00', lead: true },
    { id: 'DR-1002', name: 'Dr. Kabir Menon',     specialty: 'Gynaecology',              reg: 'MCI-71904', clinic: 'ENDO-TWIN Research Clinic, Delhi', email: 'k.menon@endotwin.health',  phone: '+91 98110 55210', exp: 9,  room: 'Consult 4', status: 'In consult', days: 'Mon–Sat', slot: '10:00 – 18:00' },
    { id: 'DR-1003', name: 'Dr. Meera Iyer',      specialty: 'Reproductive Medicine',    reg: 'MCI-64118', clinic: 'Noida Satellite Unit',            email: 'm.iyer@endotwin.health',   phone: '+91 99990 44512', exp: 15, room: 'Consult 1', status: 'Available',  days: 'Tue–Sat', slot: '11:00 – 17:00' },
    { id: 'DR-1004', name: 'Dr. Rohan Desai',     specialty: 'Sleep & Chronobiology',    reg: 'MCI-59033', clinic: 'ENDO-TWIN Research Clinic, Delhi', email: 'r.desai@endotwin.health',  phone: '+91 90011 78345', exp: 7,  room: 'Lab A',     status: 'Off duty',   days: 'Wed–Sun', slot: '08:00 – 14:00' },
    { id: 'DR-1005', name: 'Dr. Sara Fernandes',  specialty: 'Clinical Nutrition',       reg: 'RD-20871',  clinic: 'Ghaziabad Care Point',            email: 's.fernandes@endotwin.health', phone: '+91 87000 11229', exp: 6, room: 'Consult 3', status: 'Available', days: 'Mon–Thu', slot: '12:00 – 19:00' },
  ];

  /* ------------------------------ PATIENTS ----------------------------- */
  /* base records; full physiology is derived deterministically from id     */
  const base = [
    { id: 'ETN-2041', name: 'Aviral Singh',   age: 21, gender: 'Female', city: 'Ghaziabad, UP', phone: '+91 98765 41020', email: 'aviral@demo.health',  height: 163, weight: 58, blood: 'O+',  cycleLen: 28, cycleDay: 14, risk: 73, doctorId: 'DR-1001', status: 'Active',        cohort: 'Chrono-PCOS Cohort A', joined: '2026-02-11', device: 'ESP32-S3 · ETN-W12', battery: 85, adherence: 92, quality: 0.91, self: true },
    { id: 'ETN-2042', name: 'Priya Sharma',   age: 27, gender: 'Female', city: 'New Delhi',     phone: '+91 98111 23344', email: 'priya.s@demo.health', height: 158, weight: 67, blood: 'B+',  cycleLen: 34, cycleDay: 22, risk: 81, doctorId: 'DR-1001', status: 'Needs review',  cohort: 'Chrono-PCOS Cohort A', joined: '2026-01-04', device: 'ESP32-S3 · ETN-W04', battery: 62, adherence: 78, quality: 0.86 },
    { id: 'ETN-2043', name: 'Neha Verma',     age: 24, gender: 'Female', city: 'Noida, UP',     phone: '+91 99900 77812', email: 'neha.v@demo.health',  height: 166, weight: 54, blood: 'A+',  cycleLen: 27, cycleDay: 6,  risk: 34, doctorId: 'DR-1002', status: 'Active',        cohort: 'Control Cohort',       joined: '2026-03-21', device: 'ESP32-S3 · ETN-W19', battery: 94, adherence: 96, quality: 0.94 },
    { id: 'ETN-2044', name: 'Ritika Nair',    age: 31, gender: 'Female', city: 'Gurugram, HR',  phone: '+91 90000 65401', email: 'ritika.n@demo.health',height: 161, weight: 72, blood: 'AB+', cycleLen: 41, cycleDay: 33, risk: 88, doctorId: 'DR-1003', status: 'Needs review',  cohort: 'Chrono-PCOS Cohort B', joined: '2025-11-19', device: 'ESP32-S3 · ETN-W07', battery: 41, adherence: 64, quality: 0.72 },
    { id: 'ETN-2045', name: 'Aisha Khan',     age: 19, gender: 'Female', city: 'Lucknow, UP',   phone: '+91 87654 30099', email: 'aisha.k@demo.health', height: 155, weight: 49, blood: 'O-',  cycleLen: 30, cycleDay: 11, risk: 46, doctorId: 'DR-1002', status: 'Active',        cohort: 'Chrono-PCOS Cohort B', joined: '2026-04-02', device: 'ESP32-S3 · ETN-W22', battery: 77, adherence: 88, quality: 0.89 },
    { id: 'ETN-2046', name: 'Divya Menon',    age: 29, gender: 'Female', city: 'Bengaluru, KA', phone: '+91 96000 41277', email: 'divya.m@demo.health', height: 169, weight: 63, blood: 'B-',  cycleLen: 29, cycleDay: 19, risk: 52, doctorId: 'DR-1004', status: 'Active',        cohort: 'Sleep / Circadian',    joined: '2026-02-27', device: 'ESP32-S3 · ETN-W31', battery: 58, adherence: 81, quality: 0.83 },
    { id: 'ETN-2047', name: 'Sanya Kapoor',   age: 35, gender: 'Female', city: 'Mumbai, MH',    phone: '+91 91111 20087', email: 'sanya.k@demo.health', height: 160, weight: 78, blood: 'A-',  cycleLen: 45, cycleDay: 38, risk: 91, doctorId: 'DR-1001', status: 'Escalated',     cohort: 'Chrono-PCOS Cohort B', joined: '2025-10-08', device: 'ESP32-S3 · ETN-W02', battery: 23, adherence: 55, quality: 0.68 },
    { id: 'ETN-2048', name: 'Fatima Sheikh',  age: 23, gender: 'Female', city: 'Hyderabad, TS', phone: '+91 93333 88120', email: 'fatima.s@demo.health',height: 157, weight: 56, blood: 'O+',  cycleLen: 26, cycleDay: 3,  risk: 28, doctorId: 'DR-1005', status: 'Active',        cohort: 'Control Cohort',       joined: '2026-05-14', device: 'ESP32-S3 · ETN-W28', battery: 88, adherence: 93, quality: 0.92 },
    { id: 'ETN-2049', name: 'Tanvi Joshi',    age: 26, gender: 'Female', city: 'Pune, MH',      phone: '+91 95555 30014', email: 'tanvi.j@demo.health', height: 164, weight: 61, blood: 'B+',  cycleLen: 32, cycleDay: 27, risk: 59, doctorId: 'DR-1003', status: 'Active',        cohort: 'Chrono-PCOS Cohort A', joined: '2026-01-30', device: 'ESP32-S3 · ETN-W16', battery: 70, adherence: 85, quality: 0.87 },
    { id: 'ETN-2050', name: 'Ishita Bose',    age: 33, gender: 'Female', city: 'Kolkata, WB',   phone: '+91 98300 55471', email: 'ishita.b@demo.health',height: 168, weight: 69, blood: 'AB-', cycleLen: 36, cycleDay: 15, risk: 67, doctorId: 'DR-1004', status: 'Archived',      cohort: 'Chrono-PCOS Cohort B', joined: '2025-09-12', device: 'ESP32-S3 · ETN-W09', battery: 0,  adherence: 38, quality: 0.61 },
  ];

  const SYMPTOM_POOL = ['Mood swing','Acne','Fatigue','Bloating','Hair fall','Cramps','Headache','Sugar craving','Sleep trouble','Oily skin','Back pain','Low energy'];
  const MED_POOL = [
    { n: 'Inositol (Myo + D-Chiro)', d: '2 g', t: 'Morning', k: 'Supplement' },
    { n: 'Vitamin D3', d: '2000 IU', t: 'Morning', k: 'Supplement' },
    { n: 'Omega-3', d: '1000 mg', t: 'Night', k: 'Supplement' },
    { n: 'Metformin (research log)', d: '500 mg', t: 'After dinner', k: 'Logged medication' },
    { n: 'Magnesium glycinate', d: '300 mg', t: 'Night', k: 'Supplement' },
    { n: 'Iron + Folate', d: '1 tab', t: 'Afternoon', k: 'Supplement' },
  ];

  /* --------- derive rich synthetic physiology for a patient record -------- */
  function hydrate(p) {
    const r = U.rng(p.id);
    const riskFactor = p.risk / 100;
    const hrBase = 64 + riskFactor * 16;
    const hrvBase = 68 - riskFactor * 34;
    const tempBase = 33.4 + riskFactor * 1.4;
    const gsrBase = 0.16 + riskFactor * 0.3;
    const stepsBase = 6200 - riskFactor * 3600;
    const spo2Base = 99 - riskFactor * 2.2;

    const live = {
      hr:    U.series(p.id + 'hr', 60, hrBase, 9),
      hrv:   U.series(p.id + 'hrv', 60, hrvBase, 8),
      temp:  U.series(p.id + 'tp', 60, tempBase, 0.7),
      gsr:   U.series(p.id + 'gs', 60, gsrBase, 0.12),
      steps: U.series(p.id + 'st', 60, 40 + riskFactor * 10, 28),
      spo2:  U.series(p.id + 'sp', 60, spo2Base, 1.1),
    };
    const trend30 = {
      hr:    U.series(p.id + 'T1', 30, hrBase, 6),
      hrv:   U.series(p.id + 'T2', 30, hrvBase, 7),
      temp:  U.series(p.id + 'T3', 30, tempBase, 0.5),
      gsr:   U.series(p.id + 'T4', 30, gsrBase, 0.08),
      sleep: U.series(p.id + 'T5', 30, 7.4 - riskFactor * 1.8, 1.2),
      steps: U.series(p.id + 'T6', 30, stepsBase, 2200),
      risk:  U.series(p.id + 'T7', 30, p.risk, 7),
      weight:U.series(p.id + 'T8', 30, p.weight, 0.8),
    };

    const vitals = {
      hr:    Math.round(live.hr.at(-1)),
      hrv:   Math.round(live.hrv.at(-1)),
      temp:  U.round(live.temp.at(-1), 1),
      gsr:   U.round(live.gsr.at(-1), 2),
      steps: Math.round(stepsBase + (r() - 0.5) * 900),
      spo2:  Math.round(live.spo2.at(-1)),
      sleep: U.round(7.5 - riskFactor * 1.9 + r() * 0.5, 1),
      resp:  Math.round(14 + riskFactor * 4),
      bp:    `${Math.round(112 + riskFactor * 16)}/${Math.round(72 + riskFactor * 9)}`,
      bmi:   U.round(p.weight / Math.pow(p.height / 100, 2), 1),
    };

    const nSym = 2 + Math.floor(r() * 4);
    const symptoms = [];
    for (let i = 0; i < nSym; i++) {
      const s = SYMPTOM_POOL[(Math.floor(r() * SYMPTOM_POOL.length) + i) % SYMPTOM_POOL.length];
      if (!symptoms.find(x => x.name === s))
        symptoms.push({ name: s, severity: 1 + Math.floor(r() * 5), days: 1 + Math.floor(r() * 12), trend: r() > .5 ? 'up' : 'down' });
    }

    const meds = MED_POOL.filter((_, i) => (i + p.id.charCodeAt(6)) % 2 === 0 || i < 2)
      .slice(0, 2 + Math.floor(r() * 3))
      .map(m => Object.assign({ taken: r() > 0.25 }, m));

    const ultrasound = {
      date: U.fmtShort(U.daysAgo(5 + Math.floor(r() * 90))),
      follicles: Math.round(6 + riskFactor * 16),
      largest: U.round(6 + r() * 6, 1),
      volume: U.round(6 + riskFactor * 8, 1),
      pattern: p.risk >= 70 ? 'Possible' : p.risk >= 45 ? 'Indeterminate' : 'Not suggested',
      quality: U.round(0.62 + r() * 0.34, 2),
    };

    const labs = [
      { k: 'Fasting glucose', v: `${Math.round(84 + riskFactor * 26)} mg/dL`, ref: '70–99', flag: riskFactor > .6 },
      { k: 'HbA1c',           v: `${U.round(5.1 + riskFactor * 1.1, 1)} %`,   ref: '<5.7',  flag: riskFactor > .55 },
      { k: 'LH / FSH ratio',  v: `${U.round(1.1 + riskFactor * 1.6, 1)}`,     ref: '<2.0',  flag: riskFactor > .6 },
      { k: 'Total testosterone', v: `${Math.round(28 + riskFactor * 46)} ng/dL`, ref: '15–70', flag: riskFactor > .75 },
      { k: 'TSH',             v: `${U.round(1.6 + r() * 2.4, 2)} µIU/mL`,     ref: '0.4–4.0', flag: false },
      { k: 'Vitamin D',       v: `${Math.round(14 + r() * 30)} ng/mL`,        ref: '30–100', flag: r() > .5 },
    ];

    const timeline = [
      { t: '08:00 AM', icon: 'moon',      color: U.C.violet, title: 'Sleep recorded',     meta: `${vitals.sleep}h ${Math.floor(r() * 50)}m` },
      { t: '10:15 AM', icon: 'watch',     color: U.C.green,  title: 'Wearable connected', meta: 'ESP32-S3' },
      { t: '12:32 PM', icon: 'heartbeat', color: U.C.pink,   title: 'Symptoms logged',    meta: symptoms.slice(0, 2).map(s => s.name).join(', ') || 'None' },
      { t: '02:10 PM', icon: 'run',       color: U.C.cyan,   title: 'Activity',           meta: `${vitals.steps.toLocaleString()} steps` },
      { t: '06:00 PM', icon: 'pill',      color: U.C.orange, title: 'Medicine',           meta: meds[0] ? meds[0].n.split(' ')[0] : 'None' },
      { t: '10:30 PM', icon: 'scan',      color: U.C.sky,    title: 'Scan reminder',      meta: 'Pelvic ultrasound' },
    ];

    const notes = [
      { by: 'Dr. Ananya Rao', when: U.fmtShort(U.daysAgo(3 + Math.floor(r() * 10))), text: `Longitudinal HRV suppression persists across ${3 + Math.floor(r() * 6)} weeks. Continue lifestyle log, re-image next cycle. Research signal only.` },
      { by: 'Dr. Kabir Menon', when: U.fmtShort(U.daysAgo(24 + Math.floor(r() * 30))), text: 'Cycle variability discussed with participant. Sleep regularity to be prioritised before any further inference.' },
    ];

    const reports = [
      { id: 'RPT-' + p.id.slice(-3) + '1', title: 'Longitudinal Physiology Report', date: U.fmtShort(U.daysAgo(4)),  kind: 'Doctor', pages: 12 },
      { id: 'RPT-' + p.id.slice(-3) + '2', title: 'Patient Summary (plain language)', date: U.fmtShort(U.daysAgo(11)), kind: 'Patient', pages: 4 },
      { id: 'RPT-' + p.id.slice(-3) + '3', title: 'Ultrasound Research Read', date: ultrasound.date, kind: 'Imaging', pages: 6 },
      { id: 'RPT-' + p.id.slice(-3) + '4', title: 'Data Quality & Provenance', date: U.fmtShort(U.daysAgo(2)), kind: 'Audit', pages: 3 },
    ];

    const drivers = [
      { k: 'Cycle length variability', v: Math.round(18 + riskFactor * 46) },
      { k: 'HRV below personal baseline', v: Math.round(12 + riskFactor * 44) },
      { k: 'Night skin-temp elevation', v: Math.round(10 + riskFactor * 34) },
      { k: 'Sleep fragmentation', v: Math.round(8 + riskFactor * 30) },
      { k: 'Activity decline', v: Math.round(6 + riskFactor * 26) },
      { k: 'Ultrasound follicle count', v: Math.round(5 + riskFactor * 40) },
    ].sort((a, b) => b.v - a.v);

    const goals = [
      { k: 'Data consistency', v: Math.round(p.adherence), color: 'linear-gradient(90deg,#5b4bf0,#7c5cff)' },
      { k: 'Activity goal',    v: U.clamp(Math.round((vitals.steps / 8000) * 100), 5, 100), color: 'linear-gradient(90deg,#fb923c,#fbbf24)' },
      { k: 'Sleep goal',       v: U.clamp(Math.round((vitals.sleep / 8) * 100), 5, 100), color: 'linear-gradient(90deg,#22d3ee,#38bdf8)' },
      { k: 'Symptom tracking', v: U.clamp(Math.round(p.quality * 100 - 8), 5, 100), color: 'linear-gradient(90deg,#ff4d8d,#f43f75)' },
    ];

    return Object.assign({}, p, {
      initials: U.initials(p.name),
      bmi: vitals.bmi,
      lastSync: `${1 + Math.floor(r() * 12)} min ago`,
      nextVisit: U.fmtShort(new Date(Date.now() + (2 + Math.floor(r() * 20)) * 864e5)),
      live, trend30, vitals, symptoms, meds, ultrasound, labs, timeline, notes, reports, drivers, goals,
    });
  }

  /* ---------------------------- static content --------------------------- */
  const quotes = [
    'Small daily insights, big healthier tomorrows',
    'Your baseline is yours alone — track it, don\'t compare it',
    'Consistency beats intensity in longitudinal tracking',
    'Signals, not verdicts. Patterns, not panic.',
  ];

  const insights = [
    { icon: 'arrowUp', color: U.C.green,  text: 'Your HRV is 12% higher this week which indicates better recovery.' },
    { icon: 'temp',    color: U.C.pink,   text: 'Your skin temperature shows a slight rise, possible ovulation phase.' },
    { icon: 'check',   color: U.C.lime,   text: 'Stress levels are stable. Keep it up!' },
    { icon: 'moon',    color: U.C.violet, text: 'Consider improving sleep duration for better hormonal balance.' },
    { icon: 'wave',    color: U.C.cyan,   text: 'PPG signal quality improved after the strap-fit change on Tuesday.' },
  ];

  const reminders = [
    { icon: 'note',     color: U.C.pink,   title: "Log today's symptoms",     when: 'In 2 hrs' },
    { icon: 'pill',     color: U.C.orange, title: 'Take supplement (Inositol)', when: 'In 4 hrs' },
    { icon: 'watch',    color: U.C.yellow, title: 'Wearable battery low',     when: 'Charge soon' },
    { icon: 'stethoscope', color: U.C.sky, title: 'Doctor appointment',       when: '30 Sep, 4:00 PM' },
    { icon: 'scan',     color: U.C.violet, title: 'Ultrasound scan',          when: '5 Oct, 10:00 AM' },
  ];

  const quickActions = [
    { k: 'Log Symptoms',     icon: 'plus',     c1: 'rgba(255,77,141,.22)', c2: 'rgba(244,63,117,.10)', color: U.C.pink,   go: 'symptoms' },
    { k: 'Add Cycle Date',   icon: 'calendar', c1: 'rgba(124,92,255,.22)', c2: 'rgba(91,75,240,.10)',  color: U.C.violet, go: 'cycle' },
    { k: 'Scan Ultrasound',  icon: 'scan',     c1: 'rgba(251,146,60,.20)', c2: 'rgba(251,191,36,.08)', color: U.C.orange, go: 'ultrasound' },
    { k: 'Connect Wearable', icon: 'bluetooth',c1: 'rgba(34,211,238,.20)', c2: 'rgba(20,184,166,.08)', color: U.C.cyan,   go: 'wearable' },
    { k: 'AI Risk Analysis', icon: 'brain',    c1: 'rgba(59,130,246,.22)', c2: 'rgba(56,189,248,.08)', color: U.C.sky,    go: 'risk' },
    { k: 'View Reports',     icon: 'report',   c1: 'rgba(148,163,184,.18)',c2: 'rgba(148,163,184,.06)',color: '#cbd5e1',  go: 'reports' },
    { k: 'Find Doctors',     icon: 'user',     c1: 'rgba(52,211,153,.20)', c2: 'rgba(16,185,129,.08)', color: U.C.green,  go: 'finder' },
    { k: 'Lifestyle Plan',   icon: 'leaf',     c1: 'rgba(255,77,141,.18)', c2: 'rgba(167,139,250,.10)',color: U.C.pink,   go: 'nutrition' },
  ];

  const knowledge = [
    { t: 'What PCOS actually is (and is not)', c: 'Basics', m: '6 min read', tag: 'Reviewed' },
    { t: 'Why HRV matters for hormonal health', c: 'Physiology', m: '8 min read', tag: 'Reviewed' },
    { t: 'Reading your chrono-metabolic fingerprint', c: 'Platform', m: '5 min read', tag: 'Guide' },
    { t: 'Sleep regularity vs sleep duration', c: 'Circadian', m: '7 min read', tag: 'Reviewed' },
    { t: 'How ultrasound findings are described here', c: 'Imaging', m: '4 min read', tag: 'Safety' },
    { t: 'Limitations of PPG-derived HRV', c: 'Signal Quality', m: '9 min read', tag: 'Research' },
  ];

  const community = [
    { u: 'Ritika N.', t: 'Cycle tracking finally makes sense', b: 'Six months of logging and my variability dropped from 11 days to 4. Sleep schedule was the biggest lever for me.', l: 128, c: 24, when: '2 h' },
    { u: 'Aisha K.',  t: 'Strap fit tips for cleaner PPG?',   b: 'My signal quality was poor until I moved the sensor two fingers above the wrist bone. Any other tricks?', l: 64, c: 31, when: '5 h' },
    { u: 'Divya M.',  t: 'Late shifts and skin temperature',  b: 'Rotating night shifts clearly shift my temperature curve. Sharing my 60-day export with my doctor.', l: 91, c: 12, when: '1 d' },
    { u: 'Tanvi J.',  t: 'Inositol log — 90 days',           b: 'Logging honestly, including the days I missed. Adherence chart helped more than the supplement talk.', l: 203, c: 57, when: '2 d' },
  ];

  const events = [
    { t: 'PCOS Awareness Webinar', d: '02 Oct 2026', p: 'Online · 6:00 PM', k: 'Webinar' },
    { t: 'Chrono-Health Study Meetup', d: '11 Oct 2026', p: 'Delhi NCR', k: 'Meetup' },
    { t: 'Wearable Fit & Signal Clinic', d: '19 Oct 2026', p: 'Noida Unit', k: 'Workshop' },
    { t: 'Nutrition Q&A with Dr. Fernandes', d: '27 Oct 2026', p: 'Online', k: 'Q&A' },
  ];

  const clinics = [
    { n: 'ENDO-TWIN Research Clinic', a: 'Connaught Place, New Delhi', d: '6.2 km', k: 'Clinic', r: 4.8 },
    { n: 'City Diagnostics — Pelvic USG', a: 'Sector 18, Noida', d: '9.4 km', k: 'Imaging', r: 4.5 },
    { n: 'Hormone Lab (NABL)', a: 'Vaishali, Ghaziabad', d: '3.1 km', k: 'Lab', r: 4.6 },
    { n: 'Wellness Pharmacy', a: 'Indirapuram, Ghaziabad', d: '2.4 km', k: 'Pharmacy', r: 4.3 },
  ];

  const products = [
    { n: 'ENDO-TWIN Wristband (ESP32-S3)', p: '₹ 4,499', k: 'Hardware', s: 'In stock' },
    { n: 'Replacement PPG strap', p: '₹ 399', k: 'Accessory', s: 'In stock' },
    { n: 'Skin-temp patch (DS18B20)', p: '₹ 899', k: 'Sensor', s: 'Low stock' },
    { n: 'Charging dock', p: '₹ 1,299', k: 'Accessory', s: 'In stock' },
  ];

  const appointments = [
    { when: 'Today · 3:00 PM',  pid: 'ETN-2042', kind: 'Follow-up',    mode: 'In-clinic', doc: 'DR-1001', status: 'Confirmed' },
    { when: 'Today · 4:30 PM',  pid: 'ETN-2047', kind: 'Escalation review', mode: 'In-clinic', doc: 'DR-1001', status: 'Confirmed' },
    { when: 'Tomorrow · 11:00 AM', pid: 'ETN-2044', kind: 'Imaging review', mode: 'Tele', doc: 'DR-1003', status: 'Pending' },
    { when: '29 Sep · 10:15 AM', pid: 'ETN-2045', kind: 'Onboarding',   mode: 'In-clinic', doc: 'DR-1002', status: 'Confirmed' },
    { when: '30 Sep · 4:00 PM',  pid: 'ETN-2041', kind: 'Cycle review',  mode: 'Tele', doc: 'DR-1001', status: 'Confirmed' },
    { when: '01 Oct · 12:00 PM', pid: 'ETN-2049', kind: 'Nutrition plan', mode: 'Tele', doc: 'DR-1005', status: 'Pending' },
  ];

  const models = [
    { n: 'pcos_risk_gbm',      v: '2.4.1', task: 'Risk pre-screen', auc: 0.79, cal: 0.92, samples: 1420, state: 'Registered', date: '12 Aug 2026' },
    { n: 'ppg_quality_cnn',    v: '1.8.0', task: 'Signal quality',  auc: 0.94, cal: 0.88, samples: 9800, state: 'Registered', date: '02 Jul 2026' },
    { n: 'cycle_phase_hmm',    v: '0.9.3', task: 'Phase estimate',  auc: 0.71, cal: 0.80, samples: 640,  state: 'Research',   date: '19 Sep 2026' },
    { n: 'follicle_seg_unet',  v: '1.2.2', task: 'Ultrasound seg',  auc: 0.83, cal: 0.85, samples: 512,  state: 'Research',   date: '28 Aug 2026' },
    { n: 'chrono_fingerprint', v: '3.0.0', task: 'Fingerprint',     auc: null, cal: null, samples: 2100, state: 'Registered', date: '05 Sep 2026' },
  ];

  const auditLog = [
    { t: '12:41', who: 'Dr. Ananya Rao', act: 'Opened patient record', obj: 'ETN-2042', lvl: 'info' },
    { t: '12:28', who: 'system',         act: 'Model inference completed', obj: 'pcos_risk_gbm v2.4.1', lvl: 'ok' },
    { t: '11:57', who: 'Dr. Kabir Menon',act: 'Added clinical note', obj: 'ETN-2045', lvl: 'info' },
    { t: '11:30', who: 'system',         act: 'Data quality gate WARN', obj: 'ETN-2047 · PPG 0.68', lvl: 'warn' },
    { t: '10:52', who: 'Dr. Meera Iyer', act: 'Exported de-identified CSV', obj: 'Cohort B (n=4)', lvl: 'info' },
    { t: '09:14', who: 'system',         act: 'Device sync failed (retry ok)', obj: 'ETN-2050 · ETN-W09', lvl: 'err' },
  ];

  const devices = [
    { id: 'ETN-W12', fw: '8.7.1', pid: 'ETN-2041', batt: 85, rssi: -54, state: 'Online' },
    { id: 'ETN-W04', fw: '8.7.1', pid: 'ETN-2042', batt: 62, rssi: -61, state: 'Online' },
    { id: 'ETN-W19', fw: '8.7.0', pid: 'ETN-2043', batt: 94, rssi: -48, state: 'Online' },
    { id: 'ETN-W07', fw: '8.6.4', pid: 'ETN-2044', batt: 41, rssi: -72, state: 'Weak link' },
    { id: 'ETN-W22', fw: '8.7.1', pid: 'ETN-2045', batt: 77, rssi: -55, state: 'Online' },
    { id: 'ETN-W31', fw: '8.7.1', pid: 'ETN-2046', batt: 58, rssi: -66, state: 'Online' },
    { id: 'ETN-W02', fw: '8.5.9', pid: 'ETN-2047', batt: 23, rssi: -78, state: 'Needs update' },
    { id: 'ETN-W09', fw: '8.5.9', pid: 'ETN-2050', batt: 0,  rssi: null, state: 'Offline' },
  ];

  return { doctors, base, hydrate, quotes, insights, reminders, quickActions, knowledge,
    community, events, clinics, products, appointments, models, auditLog, devices,
    SYMPTOM_POOL, MED_POOL };
})();
