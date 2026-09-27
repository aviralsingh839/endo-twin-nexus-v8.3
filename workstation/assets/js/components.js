/* ============================================================
   ENDO-TWIN NEXUS — reusable UI components
   ============================================================ */
const C = (() => {

  /* -------------------------------- card -------------------------------- */
  function card(o) {
    const head = (o.title || o.right) ? `
      <div class="card-head">
        ${o.icon ? `<span style="color:${o.iconColor || 'var(--violet)'}">${U.icon(o.icon)}</span>` : ''}
        <div>
          ${o.title ? `<div class="card-title">${o.title}</div>` : ''}
          ${o.sub ? `<div class="card-sub">${o.sub}</div>` : ''}
        </div>
        <div class="spacer"></div>
        ${o.right || ''}
      </div>` : '';
    return `<section class="card ${o.cls || ''}" ${o.style ? `style="${o.style}"` : ''} ${o.id ? `id="${o.id}"` : ''}>${head}${o.body || ''}</section>`;
  }

  function pageHead(title, sub, right = '') {
    return `<div class="page-head">
      <div><div class="page-title">${title}</div><div class="page-sub">${sub || ''}</div></div>
      <div class="spacer"></div>${right}
    </div>`;
  }

  /* ------------------------------ vital card ----------------------------- */
  function vital(v) {
    return `<div class="vital" data-vital="${v.key || ''}">
      <div class="v-ico" style="background:${U.soft(v.color, .16)};color:${v.color}">${U.icon(v.icon)}</div>
      <div style="min-width:0">
        <div class="v-name">${v.name}</div>
        <div class="v-val">${v.value}<small>${v.unit || ''}</small></div>
        <span class="tag ${v.tone || 'good'}">${v.state}</span>
      </div>
      <div class="v-spark">${Chart.spark(v.series, v.color, 62, 34)}</div>
    </div>`;
  }

  /* -------------------------------- table -------------------------------- */
  function table(cols, rows, opts = {}) {
    return `<div class="tbl-wrap ${opts.cls || ''}"><table class="tbl">
      <thead><tr>${cols.map(c => `<th${c.w ? ` style="width:${c.w}"` : ''}>${c.t}</th>`).join('')}</tr></thead>
      <tbody>${rows.length ? rows.map(r => `<tr ${r.attrs || ''}>${r.cells.map(c => `<td>${c}</td>`).join('')}</tr>`).join('')
        : `<tr><td colspan="${cols.length}"><div class="empty">Nothing here yet</div></td></tr>`}</tbody>
    </table></div>`;
  }

  /* ------------------------------- key/value ----------------------------- */
  const kvs = items => items.map(i => `<div class="kv"><span class="k">${i.k}</span><span class="v">${i.v}</span></div>`).join('');

  /* --------------------------------- tile -------------------------------- */
  function tile(t) {
    return `<div class="tile" ${t.go ? `data-go="${t.go}"` : ''} ${t.act ? `data-act="${t.act}"` : ''} ${t.arg ? `data-arg="${t.arg}"` : ''}>
      <div class="t-ico" style="background:${U.soft(t.color, .16)};color:${t.color}">${U.icon(t.icon)}</div>
      <div style="min-width:0"><div class="t-title">${t.title}</div><div class="t-sub">${t.sub || ''}</div></div>
    </div>`;
  }

  /* -------------------------------- forms -------------------------------- */
  /* fields: [{n,l,t:'text|number|select|textarea|date',o:[...],v,full,hint,step,min,max}] */
  function form(fields) {
    return `<div class="form-grid">${fields.map(f => {
      const common = `id="f_${f.n}" name="${f.n}" ${f.ph ? `placeholder="${U.esc(f.ph)}"` : ''}`;
      let input;
      if (f.t === 'select') {
        input = `<select class="sel" ${common}>${(f.o || []).map(o => {
          const val = typeof o === 'object' ? o.v : o, lab = typeof o === 'object' ? o.l : o;
          return `<option value="${U.esc(val)}" ${String(f.v) === String(val) ? 'selected' : ''}>${U.esc(lab)}</option>`;
        }).join('')}</select>`;
      } else if (f.t === 'textarea') {
        input = `<textarea ${common}>${U.esc(f.v || '')}</textarea>`;
      } else {
        input = `<input type="${f.t || 'text'}" ${common} value="${U.esc(f.v == null ? '' : f.v)}"
          ${f.step ? `step="${f.step}"` : ''} ${f.min != null ? `min="${f.min}"` : ''} ${f.max != null ? `max="${f.max}"` : ''}>`;
      }
      return `<div class="field ${f.full ? 'full' : ''}">
        <label for="f_${f.n}">${f.l}</label>${input}
        ${f.hint ? `<div class="hint">${f.hint}</div>` : ''}</div>`;
    }).join('')}</div>`;
  }
  function readForm(root) {
    const out = {};
    U.$$('input,select,textarea', root).forEach(i => {
      if (!i.name) return;
      out[i.name] = i.type === 'number' ? (i.value === '' ? null : +i.value)
        : i.type === 'checkbox' ? i.checked : i.value.trim();
    });
    return out;
  }

  /* -------------------------------- modal -------------------------------- */
  const root = () => document.getElementById('modalRoot');
  function modal(o) {
    root().innerHTML = `
      <div class="modal-back" data-close="1"></div>
      <div class="modal" role="dialog" aria-modal="true">
        <div class="modal-head">
          ${o.icon ? `<div class="t-ico" style="background:${U.soft(o.color || U.C.purple, .18)};color:${o.color || U.C.purple};width:32px;height:32px;border-radius:10px;display:grid;place-items:center">${U.icon(o.icon)}</div>` : ''}
          <div><div class="mh-title">${o.title}</div>${o.sub ? `<div class="mh-sub">${o.sub}</div>` : ''}</div>
          <div class="spacer" style="flex:1"></div>
          <button class="icon-btn" data-close="1">${U.icon('close')}</button>
        </div>
        <div class="modal-body" id="modalBody">${o.body || ''}</div>
        ${o.footer === null ? '' : `<div class="modal-foot">${o.footer || `
          <button class="btn ghost" data-close="1">Cancel</button>
          <button class="btn primary" id="modalOk">${o.okText || 'Save'}</button>`}</div>`}
      </div>`;
    root().classList.add('open');
    U.$$('[data-close]', root()).forEach(b => b.onclick = closeModal);
    const ok = U.$('#modalOk', root());
    if (ok && o.onOk) ok.onclick = () => o.onOk(readForm(U.$('#modalBody', root())), U.$('#modalBody', root()));
    if (o.after) o.after(U.$('#modalBody', root()));
    return root();
  }
  function closeModal() { root().classList.remove('open'); root().innerHTML = ''; }

  function confirm(title, text, onYes, okText = 'Confirm') {
    modal({
      title, sub: 'Please confirm', icon: 'info', color: U.C.orange,
      body: `<p style="font-size:12.5px;line-height:1.6;color:var(--text-2)">${text}</p>`,
      okText,
      onOk: () => { closeModal(); onYes(); },
    });
    const ok = U.$('#modalOk', root());
    if (ok) ok.classList.add('danger');
  }

  /* -------------------------------- toast -------------------------------- */
  function toast(text, kind = 'ok') {
    const w = document.getElementById('toastWrap');
    const t = U.el(`<div class="toast ${kind === 'ok' ? '' : kind}">
      <span style="color:${kind === 'err' ? U.C.red : kind === 'info' ? U.C.sky : U.C.green}">${U.icon(kind === 'err' ? 'close' : kind === 'info' ? 'info' : 'check')}</span>
      <span>${text}</span></div>`);
    w.appendChild(t);
    setTimeout(() => { t.style.opacity = '0'; t.style.transform = 'translateY(8px)'; t.style.transition = '.3s'; }, 2600);
    setTimeout(() => t.remove(), 3000);
  }

  /* ------------------------------ misc bits ------------------------------ */
  const legend = items => `<div class="legend">${items.map(i => `<span><i style="background:${i.c}"></i>${i.k}</span>`).join('')}</div>`;

  const statMini = items => `<div class="stat-strip">${items.map(s => `
    <div class="stat-mini"><div class="sm-k"><span style="color:${s.color}">${U.icon(s.icon, 'ic', 'width:12px;height:12px')}</span>${s.k}</div>
    <div class="sm-v">${s.v}</div></div>`).join('')}</div>`;

  function avatar(name, cls = '') {
    return `<div class="avatar ${cls}">${U.initials(name)}</div>`;
  }

  function statusTag(status) {
    const map = {
      'Active': 'good', 'Needs review': 'warn', 'Escalated': 'bad', 'Archived': 'plain',
      'Available': 'good', 'In consult': 'info', 'Off duty': 'plain', 'Online': 'good',
      'Offline': 'bad', 'Weak link': 'warn', 'Needs update': 'warn', 'Confirmed': 'good',
      'Pending': 'warn', 'Registered': 'info', 'Research': 'violet',
    };
    return `<span class="tag ${map[status] || 'plain'}" style="margin-top:0">${status}</span>`;
  }

  const disclaimer = (txt) => `<div class="disclaimer">${txt || 'Research / risk-screening output — not a medical diagnosis. ENDO-TWIN NEXUS is a research prototype and is not a medical device. All data shown in this demo is synthetic.'}</div>`;

  const sectionGrid = (cls, cards) => `<div class="row ${cls}">${cards.join('')}</div>`;

  return { card, pageHead, vital, table, kvs, tile, form, readForm, modal, closeModal,
    confirm, toast, legend, statMini, avatar, statusTag, disclaimer, sectionGrid };
})();
