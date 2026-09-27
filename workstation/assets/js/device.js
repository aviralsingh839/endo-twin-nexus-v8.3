/* ============================================================
   ENDO-TWIN NEXUS — wearable link (browser side)

   Connects the ESP32-S3 band directly from this page:
     • Web Bluetooth  -> the firmware's GATT service (no driver, no install)
     • Web Serial     -> USB CDC at 115200 baud (Chrome / Edge)
   Frames are decoded for the instant on-screen view AND forwarded to
   /api/device/ingest so the server calibrates them, derives HR/HRV/EDA/temp
   and writes them into the platform database.

   Server-side transports (pyserial, Wi-Fi POST, bridge folder) are driven by
   the same status/stream polling, so the UI behaves identically.
   ============================================================ */
const DeviceLink = (() => {
  /* UUIDs from hardware/esp32/endo_twin_wearable/endo_twin_wearable.ino */
  const SERVICE_UUID = '7f300001-6c12-4f70-9e6b-8e9f7b8b1001';
  const DATA_UUID    = '7f300002-6c12-4f70-9e6b-8e9f7b8b1001';
  const CMD_UUID     = '7f300003-6c12-4f70-9e6b-8e9f7b8b1001';

  const state = {
    status: null,          // last /api/device/status payload
    stream: { samples: [], waveform: [] },
    seq: 0,
    browserTransport: null,// 'ble' | 'usb'
    browserError: null,
    busy: false,
    frames: 0,
    lastFrame: null,
  };

  const listeners = [];
  const onChange = fn => { listeners.push(fn); return () => listeners.splice(listeners.indexOf(fn), 1); };
  const emit = () => listeners.forEach(fn => { try { fn(state); } catch (e) {} });

  const supports = {
    ble: typeof navigator !== 'undefined' && !!navigator.bluetooth,
    usb: typeof navigator !== 'undefined' && !!navigator.serial,
    secure: typeof window !== 'undefined' && (window.isSecureContext !== false),
  };

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

  /* ----------------------------- frame queue ---------------------------- */
  let queue = [];
  let flushTimer = null;
  function push(line) {
    state.frames++;
    state.lastFrame = line;
    queue.push(line);
    if (queue.length > 400) queue = queue.slice(-400);
    if (!flushTimer) flushTimer = setTimeout(flush, 250);
  }
  async function flush() {
    flushTimer = null;
    if (!queue.length) return;
    const lines = queue; queue = [];
    try {
      const r = await api('/api/device/ingest', 'POST', {
        lines, transport: state.browserTransport,
        name: btDevice ? (btDevice.name || 'ENDO-TWIN Wearable') : 'ENDO-TWIN Wearable (USB)',
      });
      if (r.status) { state.status = r.status; emit(); }
    } catch (e) { state.browserError = e.message; }
  }

  /* --------------------------- Web Bluetooth ---------------------------- */
  let btDevice = null, btChar = null;
  async function connectBLE(patientId) {
    if (!supports.ble) throw new Error('This browser has no Web Bluetooth. Use Chrome/Edge over https or localhost, or connect over USB / Wi-Fi.');
    state.busy = true; state.browserError = null; emit();
    try {
      btDevice = await navigator.bluetooth.requestDevice({
        filters: [{ services: [SERVICE_UUID] }, { namePrefix: 'ENDO' }],
        optionalServices: [SERVICE_UUID],
      });
      btDevice.addEventListener('gattserverdisconnected', () => {
        state.browserTransport = null; state.browserError = 'Bluetooth link dropped'; emit();
      });
      const server = await btDevice.gatt.connect();
      const service = await server.getPrimaryService(SERVICE_UUID);
      btChar = await service.getCharacteristic(DATA_UUID);
      await btChar.startNotifications();
      const dec = new TextDecoder();
      let partial = '';
      btChar.addEventListener('characteristicvaluechanged', ev => {
        partial += dec.decode(ev.target.value);
        const lines = partial.split(/[\r\n]+/);
        partial = lines.pop() || '';
        lines.forEach(l => { if (l.trim()) push(l.trim()); });
        if (partial.startsWith('$CP') && partial.length > 40 && /,[0-9A-F]{2}$/i.test(partial)) {
          push(partial.trim()); partial = '';
        }
      });
      state.browserTransport = 'ble';
      await api('/api/device/connect', 'POST', {
        transport: 'ble', name: btDevice.name || 'ENDO-TWIN Wearable',
        endpoint: btDevice.id, patientId,
      });
      return true;
    } finally { state.busy = false; emit(); }
  }

  /* ----------------------------- Web Serial ----------------------------- */
  let port = null, reader = null, keepReading = false;
  async function connectUSB(patientId, baud = 115200) {
    if (!supports.usb) throw new Error('This browser has no Web Serial. Use Chrome/Edge, or let the server read the port (pyserial), or POST over Wi-Fi.');
    state.busy = true; state.browserError = null; emit();
    try {
      port = await navigator.serial.requestPort();
      await port.open({ baudRate: baud });
      state.browserTransport = 'usb';
      await api('/api/device/connect', 'POST', { transport: 'usb', name: 'ENDO-TWIN Wearable (USB)', patientId });
      keepReading = true;
      readLoop();
      return true;
    } finally { state.busy = false; emit(); }
  }
  async function readLoop() {
    const dec = new TextDecoder();
    let partial = '';
    while (keepReading && port && port.readable) {
      reader = port.readable.getReader();
      try {
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          partial += dec.decode(value, { stream: true });
          const lines = partial.split(/[\r\n]+/);
          partial = lines.pop() || '';
          lines.forEach(l => { if (l.trim()) push(l.trim()); });
        }
      } catch (e) {
        state.browserError = e.message;
      } finally {
        try { reader.releaseLock(); } catch (e) {}
      }
    }
  }

  async function disconnect() {
    keepReading = false;
    try { if (reader) await reader.cancel(); } catch (e) {}
    try { if (port) await port.close(); } catch (e) {}
    try { if (btDevice && btDevice.gatt.connected) btDevice.gatt.disconnect(); } catch (e) {}
    port = null; reader = null; btDevice = null; btChar = null;
    state.browserTransport = null;
    try { await api('/api/device/disconnect', 'POST', {}); } catch (e) {}
    await refresh();
  }

  /* --------------------------- server transports ------------------------ */
  async function connectServer(transport, opts = {}) {
    state.busy = true; emit();
    try {
      state.status = await api('/api/device/connect', 'POST', Object.assign({ transport }, opts));
      return state.status;
    } finally { state.busy = false; emit(); }
  }

  /* ------------------------------- polling ------------------------------ */
  let poll = null;
  async function refresh() {
    try {
      const r = await api('/api/device/stream?since=' + state.seq);
      state.status = r.status;
      state.seq = r.seq || state.seq;
      if (r.samples && r.samples.length) {
        state.stream.samples = state.stream.samples.concat(r.samples).slice(-600);
      }
      if (r.waveform && r.waveform.length) state.stream.waveform = r.waveform;
      emit();
    } catch (e) { /* server not reachable: keep the last snapshot */ }
    return state.status;
  }
  function start(ms = 1000) { stop(); refresh(); poll = setInterval(refresh, ms); }
  function stop() { if (poll) clearInterval(poll); poll = null; }

  /* ------------------------------ recording ----------------------------- */
  const startSession = patientId => api('/api/device/session/start', 'POST', { patientId });
  const stopSession = () => api('/api/device/session/stop', 'POST', {});

  /* ----------------------------- calibration ---------------------------- */
  const getCalibration = patientId => api('/api/device/calibration' + (patientId ? '?p=' + patientId : ''));
  const saveCalibration = (calibration, patientId) =>
    api('/api/device/calibration', 'PUT', { calibration, patientId });
  const captureBaseline = (sensor, patientId) =>
    api('/api/device/calibration/capture', 'POST', { sensor, patientId });
  const referencePoint = (sensor, reference, point, patientId) =>
    api('/api/device/calibration/reference', 'POST', { sensor, reference, point, patientId });
  const resetCalibration = (sensor, patientId) =>
    api('/api/device/calibration/reset', 'POST', { sensor, patientId });
  const ports = () => api('/api/device/ports');

  return {
    state, supports, onChange, refresh, start, stop,
    connectBLE, connectUSB, connectServer, disconnect,
    startSession, stopSession,
    getCalibration, saveCalibration, captureBaseline, referencePoint, resetCalibration, ports,
    api, SERVICE_UUID, DATA_UUID, CMD_UUID,
  };
})();
