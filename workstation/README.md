# ENDO-TWIN NEXUS — Unified Workstation (Web UI)

One console that joins the **Patient Workstation** and the **Doctor Workstation**.
Switch between them from the profile control in the **top-right** corner
(or press <kbd>Ctrl</kbd>+<kbd>D</kbd>).

> Research prototype — not a medical device, not a diagnosis.
> Records shown in **live mode** come from the platform's own SQLite database;
> records shown in **demo mode** are synthetic sample data and are labelled as such.

---

## Run it

```bash
./START.sh              # from the repo root -> http://localhost:8787
./START.sh ui 9000      # choose a port
./START.sh menu         # full launcher menu (option 1 = this UI)
python3 workstation/serve.py --port 8787 --no-browser
```

No build step, no npm, no external CDN — plain HTML/CSS/JS + Python's stdlib
HTTP server. Works offline.

---

## Where the data comes from

`workstation/api.py` is a dependency-free data layer over
`data/chrono_twin_nexus_v8_3_plus.db` — the same SQLite file the PySide6
applications use. `serve.py` routes `/api/*` to it.

| Route | Purpose |
|---|---|
| `GET /api/health` | table counts, file size, whether the DB is empty |
| `GET /api/bootstrap` | health + every patient (with signals) + every clinician |
| `GET/POST /api/patients` · `GET/PATCH/DELETE /api/patients/<id>` | registry CRUD |
| `GET /api/patients/<id>/series` | raw downsampled sensor series |
| `GET/POST /api/doctors` · `PATCH/DELETE /api/doctors/<id>` | clinician CRUD (`providers` table) |
| `POST /api/notes` · `/api/symptoms` · `/api/cycles` · `/api/reports` | clinical writes |
| `POST /api/seed-demo` · `/api/clear-demo` | add / remove rows tagged `SYNTHETIC_DEMO` |

Rules the UI follows:

* **Nothing is invented.** Vitals, trends, risk, cycle day, ultrasound metrics
  and data quality are computed from rows in the database. A measurement that
  was never recorded renders as `—`, and its chart shows an explicit
  *"No data recorded yet"* placeholder.
* **The source is always visible.** The chip in the top bar reads
  `LIVE DATABASE`, `LIVE DB · EMPTY` or `DEMO DATA`; click it for the file path
  and per-table row counts.
* **Writes are real.** Creating or editing a patient/clinician, logging a
  symptom or saving a note inserts into SQLite. Check with:

```bash
./START.sh db-status
python3 workstation/api.py --seed      # 10 participants + 5 clinicians, tagged
python3 workstation/api.py --clear     # remove exactly those tagged rows
```

* **Demo data stays separable.** Everything written by the seeder carries
  `label = 'SYNTHETIC_DEMO'` (clinicians carry it inside `services_json`), so one
  click removes it without touching real recordings.
* **Offline fallback.** With no backend the UI switches to `DemoData` and flags
  itself as DEMO DATA rather than pretending to be live.

---

## Layout

```
┌──────────────────────────────────────────────────────────────────────────┐
│ brand │ global search (Ctrl+K) │ wearable pill │ clock │ 🔔 │ ☀ │ PROFILE ▾│ ← role switch
├──────────┬───────────────────────────────────────────────────────────────┤
│ sidebar  │ page content (dashboard, charts, tables, modals)              │
│ grouped  │                                                               │
│ sections │                                                               │
└──────────┴───────────────────────────────────────────────────────────────┘
```

### Patient view (25 sections)
`Dashboard` · **Monitor**: Live Monitoring, Wearable Device, Data Logger, Cycle & Symptoms ·
**Analysis**: AI Risk Analysis, Hormonal Twin, Cycle Prediction, Trends & Insights, Comparative Analysis ·
**Health management**: Symptoms Tracker, Nutrition & Lifestyle, Sleep & Stress, Medications & Supplements, Goals & Plans ·
**Reports**: Reports & Export, Doctor Sharing, Clinic & Product Finder ·
**Community**: Community, Knowledge Hub, Events & Awareness ·
**Settings**: Profile & Preferences, Device Settings, Data & Privacy, About ·
plus the Ultrasound Analysis workspace.

Dashboard reproduces the reference design: greeting banner + digital-twin card,
six live vital cards with sparklines, live multi-sensor chart with series chips,
hormonal health score donut, cycle tracker, AI insights, today's timeline,
8 quick actions, progress rings, recent analysis tabs, ultrasound panel,
report tiles and reminders. Vitals and the live chart tick in real time.

### Doctor view (25 sections)
`Dashboard` · **Patients**: Patient Registry (add / edit / delete / open), Patient Chart,
Pending Reviews, Cohorts & Groups · **Clinical**: Physiological Signals, Longitudinal Analysis,
Ultrasound Review, AI/ML Laboratory, Explainability, Data Provenance ·
**Care**: Appointments, Clinical Notes, Care Plans, Messages ·
**Reports**: Clinical Reports, Cohort Analytics, Export & Sharing ·
**Practice**: Doctors & Staff (add / edit / remove / sign in as), Clinic Profile,
Device Fleet, Database, Diagnostics, Audit Log · **Settings**: Preferences, About.

---

## Demo data & editing

* **10 synthetic patients** (`ETN-2041 … ETN-2050`) across four cohorts, each with
  deterministic physiology: live streams, 30-day trends, symptoms, medications,
  labs, ultrasound read, notes, reports and risk drivers.
* **5 clinicians** (`DR-1001 … DR-1005`).
* Add / edit patients: Doctor view → *Patient Registry* → **Add patient**, row **✎**,
  or the profile menu. Add / edit doctors: Doctor view → *Doctors & Staff*.
* The patient dropdown in the profile menu switches which participant the
  patient dashboard shows.
* Everything you change is stored in `localStorage`
  (key `endotwin-nexus-workstation-v1`). *Reset demo data* in the profile menu
  restores the originals.

## Files

```
workstation/
├── index.html              shell (topbar, sidebar, main, modal + toast roots)
├── serve.py                stdlib static server (no-cache, port fallback)
└── assets/
    ├── css/app.css         design system: dark + light themes, all components
    ├── img/                favicon, hero art
    └── js/
        ├── util.js         seeded RNG, series synthesis, icons, dates, colors
        ├── charts.js       SVG charts: sparkline, lines, donut, ring, bars,
        │                   radar, heatmap, scatter, waveform, h-bars
        ├── data.js         synthetic dataset (patients, doctors, content)
        ├── store.js        state + localStorage + CRUD
        ├── components.js   card, table, form, modal, toast, tiles, tags
        ├── views-patient.js  patient navigation + 26 pages
        ├── views-doctor.js   doctor navigation + 25 pages
        └── app.js          shell, routing, role switch, all actions
```

## Shortcuts

| Keys | Action |
|---|---|
| <kbd>Ctrl</kbd>+<kbd>K</kbd> | focus global search (patients, doctors, pages, articles) |
| <kbd>Ctrl</kbd>+<kbd>D</kbd> | toggle Patient ⇄ Doctor workspace |
| <kbd>Esc</kbd> | close modal / menus |
