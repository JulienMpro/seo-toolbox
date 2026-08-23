(() => {
  const dataNode = document.getElementById('tool-data');
  if (!dataNode) return;
  const tool = JSON.parse(dataNode.textContent);
  const ui = tool.ui;
  const mount = document.getElementById('tool-mount');
  const result = document.getElementById('tool-result');
  const esc = value => { const node = document.createElement('div'); node.textContent = value ?? ''; return node.innerHTML; };
  const display = value => value === null || value === undefined || value === '' ? 'N/D' : Array.isArray(value) ? value.join(', ') || 'N/D' : typeof value === 'object' ? JSON.stringify(value) : String(value);
  const cta = ui.cta;
  document.querySelector('[data-tool-icon]').innerHTML = ToolCatalog.icon(ui.archetype);

  function field(arg) {
    const id = `tool-arg-${arg.name}`;
    const label = arg.label || arg.name.replaceAll('_', ' ');
    const required = arg.required ? '<span class="required" aria-label="required"> *</span>' : '';
    const help = arg.help ? `<span class="tool-help">${esc(arg.help)}</span>` : '';
    if (arg.widget === 'checkbox') {
      const checked = arg.default === true || arg.default === 'true' ? ' checked' : '';
      return `<label class="tool-check" for="${esc(id)}"><input id="${esc(id)}" name="${esc(arg.name)}" type="checkbox" data-type="bool"${checked}><span>${esc(label)}${required}${help}</span></label>`;
    }
    const common = `id="${esc(id)}" name="${esc(arg.name)}" data-type="${esc(arg.type)}" placeholder="${esc(arg.placeholder || '')}"${arg.required ? ' required' : ''}`;
    let control;
    if (arg.widget === 'textarea') control = `<textarea ${common}>${arg.default ?? ''}</textarea>`;
    else if (arg.widget === 'select') control = `<select ${common}>${(arg.choices || []).map(choice => `<option value="${esc(choice)}"${String(arg.default) === choice ? ' selected' : ''}>${esc(choice)}</option>`).join('')}</select>`;
    else {
      const type = arg.widget === 'number' ? 'number' : (arg.name === 'url' ? 'url' : 'text');
      const step = arg.type === 'float' ? ' step="any"' : '';
      const value = arg.default !== null && arg.default !== undefined ? ` value="${esc(arg.default)}"` : '';
      control = `<input ${common} type="${type}"${step}${value}>`;
    }
    const wide = arg.widget === 'textarea' ? ' wide' : '';
    return `<label class="tool-field${wide}" for="${esc(id)}"><span>${esc(label)}${required}</span>${control}${help}</label>`;
  }

  const hasSample = tool.no_api && Object.keys(ui.examples || {}).length > 0;
  mount.innerHTML = `<form class="tool-form" id="tool-form"><div class="tool-fields">${tool.args.map(field).join('') || '<div class="empty">This tool has no arguments.</div>'}</div><div class="tool-actions"><button class="btn btn-primary tool-run" type="submit">${esc(cta)}</button>${hasSample ? '<button class="btn btn-ghost" type="button" data-sample>Try sample</button><span class="sample-hint" hidden>Sample — replace with your own.</span>' : ''}</div></form>`;
  const form = document.getElementById('tool-form');
  const runButton = form.querySelector('.tool-run');
  form.querySelector('[data-sample]')?.addEventListener('click', () => {
    Object.entries(ui.examples).forEach(([name,value]) => { const input=form.elements[name]; if (!input) return; if (input.type==='checkbox') input.checked=value===true||value==='true'; else input.value=value; });
    form.querySelector('.sample-hint').hidden=false;
  });
  document.getElementById('copy-command')?.addEventListener('click', event => copy(document.getElementById('example-command').textContent, event.currentTarget));

  function values() {
    const payload = {};
    tool.args.forEach(arg => {
      const input = form.elements[arg.name];
      if (arg.widget === 'checkbox') payload[arg.name] = input.checked;
      else if (input.value !== '') payload[arg.name] = input.value;
    });
    return payload;
  }

  async function copy(value, button) {
    const original = button.textContent;
    try { await navigator.clipboard.writeText(value); button.textContent = 'Copied'; }
    catch (_) { button.textContent = 'Copy failed'; }
    window.setTimeout(() => { button.textContent = original; }, 1500);
  }
  function download(value, extension) {
    const url = URL.createObjectURL(new Blob([value], {type:'text/plain;charset=utf-8'}));
    const link = document.createElement('a'); link.href = url; link.download = `${tool.name}.${extension}`;
    document.body.appendChild(link); link.click(); link.remove(); URL.revokeObjectURL(url);
  }
  function wireTextActions(value, extension = 'txt') {
    result.querySelector('[data-copy]')?.addEventListener('click', event => copy(value, event.currentTarget));
    result.querySelector('[data-download]')?.addEventListener('click', () => download(value, extension));
  }
  function summary(rows) {
    let nd = 0, ok = 0, warn = 0, error = 0;
    rows.forEach(row => Object.entries(row).filter(([key]) => /status|valid|issue|result|code/i.test(key) || Object.hasOwn(ui.badge_columns, key)).forEach(([, raw]) => {
      const value = display(raw).toLowerCase();
      if (value === 'n/d') nd += 1;
      if (/^(ok|valid|pass|passed|200)$/.test(value)) ok += 1;
      else if (/warn|redirect/.test(value)) warn += 1;
      else if (/error|invalid|fail|404|500/.test(value)) error += 1;
    }));
    const chips = [`${rows.length} row${rows.length === 1 ? '' : 's'}`];
    if (ui.archetype === 'checker') chips.push(`${ok} OK`, `${warn} WARN`, `${error} ERROR`);
    else if (nd) chips.push(`${nd} N/D`);
    return `<div class="summary-chips">${chips.map(item => `<span class="summary-chip">${esc(item)}</span>`).join('')}</div>`;
  }
  function badge(value, key) {
    const normalized = display(value).toLowerCase();
    const configured = ui.badge_columns[key] || (key.toLowerCase().match(/status|valid|issue|result/) ? ui.badge_columns.status : null);
    if (!configured) return esc(display(value));
    const kind = (configured.ok || []).some(item => normalized.includes(item)) ? 'ok' : (configured.warn || []).some(item => normalized.includes(item)) ? 'warn' : (configured.err || []).some(item => normalized.includes(item)) ? 'error' : '';
    return kind ? `<span class="status-badge status-${kind}">${esc(display(value))}</span>` : esc(display(value));
  }
  function table(rows) {
    if (!rows.length) return '<div class="empty">N/D — no results returned.</div>';
    const headers = Array.from(new Set(rows.flatMap(row => Object.keys(row))));
    const best = {};
    if (ui.best_highlight) headers.forEach(key => {
      const nums = rows.map(row => Number(row[key])).filter(Number.isFinite); if (nums.length) best[key] = Math.max(...nums);
    });
    return `${summary(rows)}<div class="table-wrap"><table class="exportable" data-export-name="${esc(tool.name)}"><thead><tr>${headers.map(key => `<th>${esc(key.replaceAll('_',' '))}</th>`).join('')}</tr></thead><tbody>${rows.map(row => `<tr>${headers.map(key => `<td${best[key] === Number(row[key]) ? ' style="background:#ecfdf3;font-weight:700"' : ''}>${badge(row[key], key)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
  }
  function cards(output) {
    const rows = Array.isArray(output) ? output : [{result: output}];
    if (!rows.length) return '<div class="empty">N/D — no results returned.</div>';
    const headline = rows.length > 1 && ui.archetype === 'calculator' ? rows[rows.length - 1] : rows[0];
    return `<div class="metrics">${Object.entries(headline).map(([key,value]) => `<div class="metric"><span>${esc(key.replaceAll('_',' '))}</span><strong>${esc(display(value))}</strong></div>`).join('')}</div>${rows.length > 1 ? table(rows) : ''}`;
  }
  function serp(rows) {
    if (!rows.length) return '<div class="empty">N/D — no results returned.</div>';
    return `${summary(rows)}<div class="serp-list">${rows.map((row,index) => {
      const url = row.url || row.link || ''; const title = row.title || row.keyword || row.question || `Result ${index + 1}`;
      const snippet = row.description || row.snippet || row.text || Object.entries(row).filter(([key]) => !['url','link','title'].includes(key)).map(([key,value]) => `${key}: ${display(value)}`).join(' · ');
      return `<article class="card serp-item"><span class="rank">#${esc(row.position || row.rank || index + 1)}</span><h3>${url ? `<a href="${esc(url)}" rel="noopener noreferrer">${esc(title)}</a>` : esc(title)}</h3>${url ? `<div class="domain">${esc(url)}</div>` : ''}<p>${esc(snippet || 'N/D')}</p></article>`;
    }).join('')}</div>`;
  }
  function sets(output) {
    const rows = Array.isArray(output) ? output : [];
    const zones = {both:[], first:[], second:[]};
    rows.forEach(row => {
      const text = display(row.url ?? row.keyword ?? row.value ?? Object.values(row)[0]);
      const statuses = Object.entries(row).filter(([key]) => /status|valid|issue|result|code/i.test(key) || Object.hasOwn(ui.badge_columns, key)).map(([, value]) => display(value).toLowerCase());
      if (text.toLowerCase() === 'total' || statuses.some(value => value === 'total' || value.includes('='))) return;
      if (statuses.length) {
        const status = statuses.join(' ');
        if (/\b(new|added)\b/.test(status)) zones.second.push(text);
        else if (/\b(removed|gone)\b/.test(status)) zones.first.push(text);
        else if (/\b(unchanged|stable|gained|lost)\b/.test(status) || (/\bindexed\b/.test(status) && !/not indexed|unknown|excluded/.test(status))) zones.both.push(text);
        else zones.second.push(text);
        return;
      }
      const marker = Object.values(row).map(display).join(' ').toLowerCase();
      if (/both|unchanged|common|stable|gained|lost|indexed/.test(marker) && !/not indexed/.test(marker)) zones.both.push(text);
      else if (/removed|gone|before|only.*first|missing/.test(marker)) zones.first.push(text);
      else zones.second.push(text);
    });
    const labels = [{key:'both',title:'✅ In both'}, {key:'first',title:`🔵 Only in ${ui.result_labels.first || 'first list'}`}, {key:'second',title:`🟠 Only in ${ui.result_labels.second || 'second list'}`}];
    result.innerHTML = `<div class="result-zones">${labels.map(zone => `<section class="result-zone"><h3>${esc(zone.title)} (${zones[zone.key].length})</h3><button class="zone-copy" type="button" data-zone="${zone.key}">Copy</button><pre>${esc(zones[zone.key].join('\n') || 'N/D')}</pre></section>`).join('')}</div>`;
    result.querySelectorAll('[data-zone]').forEach(button => button.addEventListener('click', () => copy(zones[button.dataset.zone].join('\n'), button)));
  }
  function diff(value) {
    const text = display(value);
    result.innerHTML = `<div class="result-tools"><button type="button" data-copy>Copy</button><button type="button" data-download>Download</button></div><div class="panel">${text.split('\n').map(line => `<span class="diff-line${line.startsWith('+') ? ' diff-add' : line.startsWith('-') ? ' diff-remove' : ''}">${esc(line)}</span>`).join('')}</div>`;
    wireTextActions(text);
  }
  function code(value) {
    const text = value === null || value === undefined || value === '' ? 'N/D' : String(value);
    const extension = ui.syntax === 'xml' ? 'xml' : ui.syntax === 'json' ? 'json' : 'txt';
    if (ui.archetype === 'converter') result.innerHTML = `<div class="result-tools"><button type="button" data-copy>Copy</button><button type="button" data-download>Download .txt</button></div><textarea class="output-text" readonly placeholder="N/D">${esc(text)}</textarea>`;
    else result.innerHTML = `<div class="result-tools"><button type="button" data-copy>Copy</button><button type="button" data-download>Download .${extension}</button></div><pre class="code-output"><code>${esc(text)}</code></pre>${ui.archetype === 'schema' ? '<p><a href="/tools/jsonld_validate">Validate this JSON-LD →</a> Copy the output, then paste it into the validator.</p>' : ''}`;
    wireTextActions(text, extension);
  }
  function checklist(output) {
    const enabled = tool.args.filter(arg => form.elements[arg.name]?.checked).length;
    const scoreMatch = String(output).match(/(?:score[^0-9]*)?(\d+(?:\.\d+)?)\s*(?:\/\s*100|%)/i);
    const score = Math.min(100, Number(scoreMatch?.[1] ?? (enabled / tool.args.length * 100)));
    result.innerHTML = `<div class="score">${score.toFixed(0)}/100</div><div class="score-track" aria-label="Score ${score.toFixed(0)} out of 100"><div class="score-fill" style="width:${score}%"></div></div>${table(tool.args.map(arg => ({signal:arg.label, enabled:form.elements[arg.name].checked ? 'On' : 'Off'})))}`;
    window.initExportableTables(result);
  }
  function render(payload) {
    if (ui.result_mode === 'sets') return sets(payload.output);
    if (ui.result_mode === 'diff') return diff(payload.output);
    if (ui.archetype === 'checklist') return checklist(payload.output);
    if (ui.result_mode === 'code' && payload.returns === 'str') return code(payload.output);
    if (ui.serp_style && Array.isArray(payload.output)) result.innerHTML = serp(payload.output);
    else if (ui.result_mode === 'cards' || (ui.archetype === 'single' && Array.isArray(payload.output) && payload.output.length === 1)) result.innerHTML = cards(payload.output);
    else result.innerHTML = table(Array.isArray(payload.output) ? payload.output : [{result:payload.output}]);
    window.initExportableTables(result);
  }

  let sequence = 0;
  async function run() {
    if (!form.reportValidity()) return;
    const current = ++sequence; runButton.disabled = true; runButton.textContent = 'Running…';
    result.innerHTML = '<div class="empty loading-state"><span class="spinner" aria-hidden="true"></span><span>Running…</span></div>';
    try {
      const response = await fetch(`/api/tools/${encodeURIComponent(tool.name)}/run`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(values())});
      const payload = await response.json(); if (!response.ok || payload.error) throw new Error(payload.error || `Request failed (${response.status})`);
      if (current === sequence) render(payload);
    } catch (error) { if (current === sequence) { const credentials = !tool.no_api && mount.dataset.credentialsMissing === 'true'; result.innerHTML = `<div class="tool-error"><strong>N/D — ${esc(error.message || 'the tool could not be run.')}</strong><p>${credentials ? 'Set DATAFORSEO_USERNAME and DATAFORSEO_PASSWORD, or try a No API tool.' : 'Check the inputs and try again.'}</p></div>`; } }
    finally { if (current === sequence) { runButton.disabled = false; runButton.textContent = cta; } }
  }
  form.addEventListener('submit', event => { event.preventDefault(); run(); });
  if (ui.archetype === 'converter') {
    let timer; form.addEventListener('input', () => { window.clearTimeout(timer); timer = window.setTimeout(run, 350); });
  }
})();
