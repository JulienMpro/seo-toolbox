(() => {
  const popular=['serp_compare','link_gap','cannibalization','roi_seo','keyword_expansion','redirect_generator','http_status_bulk','jsonld_faq','keyword_density','sitemap_generator','brand_visibility_ia','eeat_score'];
  let toolsPromise;
  const loadTools=()=>toolsPromise ||= fetch('/api/tools').then(r=>{if(!r.ok)throw new Error('Tool catalog unavailable');return r.json();});
  window.SEO_POPULAR=popular;

  const overlay=document.getElementById('command-palette'), input=document.getElementById('palette-search'), results=document.getElementById('palette-results');
  let opener=null,items=[],active=0;
  const render=async()=>{
    try {
      const tools=await loadTools(), q=input.value.trim();
      const ranked=tools.map(t=>[t,ToolCatalog.score(t,q)]).filter(([,s])=>s).sort((a,b)=>b[1]-a[1]||a[0].display_name.localeCompare(b[0].display_name)).map(([t])=>t).slice(0,30);
      const groups=[];
      if(!q){const pop=popular.map(n=>ranked.find(t=>t.name===n)).filter(Boolean);if(pop.length)groups.push(['Popular',pop]);}
      const rest=q?ranked:ranked.filter(t=>!popular.includes(t.name));
      [...new Set(rest.map(t=>t.category))].forEach(c=>groups.push([c,rest.filter(t=>t.category===c)]));
      results.innerHTML=groups.map(([label,group])=>`<div class="palette-group">${ToolCatalog.escapeHtml(label)}</div>${group.map(t=>`<a class="palette-item" role="option" href="/tools/${encodeURIComponent(t.name)}"><span class="palette-icon">${ToolCatalog.icon(t.archetype)}</span><span><strong>${ToolCatalog.highlight(t.display_name,q)}</strong><small>${ToolCatalog.escapeHtml(t.description)}</small></span><span class="badge badge-${t.archetype}">${ToolCatalog.escapeHtml(t.archetype)}</span></a>`).join('')}`).join('')||'<div class="empty">No matching tools. Try “redirect” or “jsonld”.</div>';
      items=[...results.querySelectorAll('.palette-item')];active=0;select();
    } catch(_) {results.innerHTML='<div class="error">N/D — tool catalog unavailable.</div>';}
  };
  const select=()=>items.forEach((el,i)=>{el.classList.toggle('active',i===active);el.setAttribute('aria-selected',String(i===active));});
  function openPalette(source){opener=source||document.activeElement;overlay.classList.add('open');overlay.setAttribute('aria-hidden','false');input.value='';render();requestAnimationFrame(()=>input.focus());}
  function closePalette(){overlay.classList.remove('open');overlay.setAttribute('aria-hidden','true');opener?.focus();}
  document.querySelectorAll('[data-palette-open]').forEach(b=>b.addEventListener('click',()=>openPalette(b)));
  document.addEventListener('keydown',e=>{
    if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='k'){e.preventDefault();overlay.classList.contains('open')?closePalette():openPalette();return;}
    if(e.key==='/'&&!overlay.classList.contains('open')&&location.pathname==='/tools'&&!/input|textarea|select/i.test(document.activeElement.tagName)){e.preventDefault();document.getElementById('tool-search')?.focus();}
    if(!overlay.classList.contains('open'))return;
    if(e.key==='Escape'){e.preventDefault();closePalette();}
    if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();active=(active+(e.key==='ArrowDown'?1:-1)+items.length)%items.length;select();items[active]?.scrollIntoView({block:'nearest'});}
    if(e.key==='Enter'&&items[active]){e.preventDefault();items[active].click();}
    if(e.key==='Tab'){const focusable=[input,...items];const i=focusable.indexOf(document.activeElement);e.preventDefault();focusable[(i+(e.shiftKey?-1:1)+focusable.length)%focusable.length]?.focus();}
  });
  overlay.addEventListener('mousedown',e=>{if(e.target===overlay)closePalette();});input.addEventListener('input',render);

  const BOM='\ufeff';
  function cells(table,separator){return [...table.querySelectorAll('tr')].map(row=>[...row.querySelectorAll('th,td')].map(cell=>{let v=cell.textContent.trim();if(v==='N/D')v='';return separator===';'&&/[;"\r\n]/.test(v)?`"${v.replaceAll('"','""')}"`:v.replace(/[\t\r\n]+/g,' ')}).join(separator)).join(separator===';'?'\r\n':'\n');}
  async function copyText(value){if(navigator.clipboard?.writeText)return navigator.clipboard.writeText(value);const t=document.createElement('textarea');t.value=value;document.body.append(t);t.select();document.execCommand('copy');t.remove();}
  window.copyText=copyText;
  window.initExportableTables=(root=document)=>root.querySelectorAll('table.exportable').forEach(table=>{if(table.dataset.exportReady)return;table.dataset.exportReady='true';const bar=document.createElement('div');bar.className='table-export';bar.innerHTML='<button class="table-export-button" type="button">Copy</button><button class="table-export-button" type="button">CSV</button>';const [copy,csv]=bar.children;copy.onclick=async()=>{await copyText(cells(table,'\t'));const old=copy.textContent;copy.textContent='Copied';setTimeout(()=>copy.textContent=old,1500)};csv.onclick=()=>{const blob=new Blob([BOM+cells(table,';')],{type:'text/csv;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`${table.dataset.exportName||'table'}.csv`;a.click();URL.revokeObjectURL(url)};(table.closest('.table-wrap')||table).before(bar)});
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>window.initExportableTables());else window.initExportableTables();
})();
