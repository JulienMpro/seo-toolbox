(() => {
  const tools=JSON.parse(document.getElementById('tools-data').textContent),directory=document.getElementById('tools-directory'),search=document.getElementById('tool-search'),count=document.getElementById('tool-results');
  const popular=window.SEO_POPULAR.filter(name=>tools.some(t=>t.name===name));let category='all',archetype='all',noApi=false;
  const card=(tool,q='')=>`<a class="tool-card" href="/tools/${encodeURIComponent(tool.name)}"><div class="tool-card-top"><span class="tool-icon">${ToolCatalog.icon(tool.archetype)}</span><span class="badge badge-${tool.archetype}">${ToolCatalog.escapeHtml(tool.archetype)}</span>${tool.no_api?'<span class="badge badge-no-api" title="Uses no DataForSEO credits; it may still fetch public URLs.">No API</span>':''}</div><h3>${ToolCatalog.highlight(tool.display_name,q)}</h3><p>${ToolCatalog.highlight(tool.description,q)}</p><span class="tool-open">Open →</span></a>`;
  const grid=(items,q)=>`<div class="tools-grid">${items.map(t=>card(t,q)).join('')}</div>`;
  function sorted(items,q){return items.map(t=>[t,ToolCatalog.score(t,q)]).filter(([,s])=>s).sort((a,b)=>b[1]-a[1]||(popular.includes(b[0].name)-popular.includes(a[0].name))||a[0].display_name.localeCompare(b[0].display_name)).map(([t])=>t);}
  function render(){
    const q=search.value.trim();let visible=tools.filter(t=>(category==='all'||t.category===category)&&(archetype==='all'||t.archetype===archetype)&&(!noApi||t.no_api));visible=sorted(visible,q);count.textContent=`${visible.length} tool${visible.length===1?'':'s'}`;
    if(!visible.length){directory.innerHTML='<div class="empty tools-empty"><strong>No matching tools.</strong><br>Try “redirect” or “jsonld”, or clear a filter.</div>';return;}
    if(q||category!=='all'||archetype!=='all'||noApi){directory.innerHTML=grid(visible,q);return;}
    const popularTools=popular.map(n=>tools.find(t=>t.name===n)).filter(Boolean);
    const categories=[...new Set(tools.map(t=>t.category))].sort();
    directory.innerHTML=`<section class="tool-section popular-section"><div class="section-heading"><div><h2>Popular tools</h2><p>Fast paths for frequent SEO work.</p></div><span>${popularTools.length}</span></div>${grid(popularTools,'')}</section>`+categories.map(cat=>{const items=visible.filter(t=>t.category===cat);return `<section class="tool-section" id="${encodeURIComponent(cat)}"><div class="section-heading"><div><h2>${ToolCatalog.escapeHtml(cat[0].toUpperCase()+cat.slice(1))}</h2><p>Browse ${ToolCatalog.escapeHtml(cat)} tools.</p></div><span>${items.length}</span></div>${grid(items,'')}</section>`}).join('');
  }
  document.getElementById('category-chips').onclick=e=>{const chip=e.target.closest('[data-category]');if(!chip)return;category=chip.dataset.category;document.querySelectorAll('[data-category]').forEach(x=>x.classList.toggle('active',x===chip));history.replaceState(null,'',category==='all'?'/tools':`#${encodeURIComponent(category)}`);render();};
  document.getElementById('archetype-chips').onclick=e=>{const chip=e.target.closest('[data-archetype]');if(chip){archetype=chip.dataset.archetype;document.querySelectorAll('[data-archetype]').forEach(x=>x.classList.toggle('active',x===chip));render();}};
  document.getElementById('no-api-chip').onclick=e=>{noApi=!noApi;e.currentTarget.classList.toggle('active',noApi);e.currentTarget.setAttribute('aria-pressed',String(noApi));render();};search.oninput=render;
  const initial=decodeURIComponent(location.hash.slice(1));const initialChip=[...document.querySelectorAll('[data-category]')].find(x=>x.dataset.category===initial);if(initialChip)initialChip.click();else render();
})();
