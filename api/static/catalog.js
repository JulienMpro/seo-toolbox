(() => {
  const paths = {
    converter:'<path d="M7 7h11m-3-3 3 3-3 3M17 17H6m3 3-3-3 3-3"/>',
    compare:'<path d="M8 5v14m8-14v14M5 8l3-3 3 3m2 8 3 3 3-3"/>',
    list:'<path d="M9 6h10M9 12h10M9 18h10M5 6h.01M5 12h.01M5 18h.01"/>',
    single:'<circle cx="12" cy="12" r="7"/><path d="m17 17 3 3"/>',
    checker:'<path d="m5 12 4 4L19 6"/>', analyzer:'<path d="M4 19V9m6 10V5m6 14v-7m4 7H2"/>',
    calculator:'<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M8 7h8M8 12h.01M12 12h.01M16 12h.01M8 16h.01M12 16h.01M16 16h.01"/>',
    checklist:'<path d="M9 6h11M9 12h11M9 18h11M4 6l1 1 2-2M4 12l1 1 2-2M4 18l1 1 2-2"/>',
    generator:'<path d="m12 3 1.4 4.1L17.5 8.5l-4.1 1.4L12 14l-1.4-4.1-4.1-1.4 4.1-1.4L12 3Zm6 10 .8 2.2L21 16l-2.2.8L18 19l-.8-2.2L15 16l2.2-.8L18 13Z"/>',
    schema:'<path d="M8 4H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h3m8-16h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3M10 8l-3 4 3 4m4-8 3 4-3 4"/>'
  };
  const normalize = value => String(value || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[-_]+/g,' ');
  const escapeHtml = value => { const node=document.createElement('div');node.textContent=value??'';return node.innerHTML; };
  function icon(type) { return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[type]||paths.single}</svg>`; }
  function score(tool, raw) {
    const q=normalize(raw).trim(); if(!q) return 1;
    const name=normalize(tool.name), display=normalize(tool.display_name), description=normalize(tool.description);
    if(name.startsWith(q)) return 100; if(display.startsWith(q)) return 90;
    if(name.split(' ').some(w=>w.startsWith(q))||display.split(' ').some(w=>w.startsWith(q))) return 70;
    if(name.includes(q)||display.includes(q)) return 50; if(description.includes(q)) return 20; return 0;
  }
  function highlight(value, raw) {
    const q=normalize(raw).trim(); if(!q) return escapeHtml(value);
    const text=String(value), normalized=normalize(text), index=normalized.indexOf(q);
    if(index<0) return escapeHtml(text);
    return `${escapeHtml(text.slice(0,index))}<mark>${escapeHtml(text.slice(index,index+q.length))}</mark>${escapeHtml(text.slice(index+q.length))}`;
  }
  window.ToolCatalog={icon,score,highlight,escapeHtml,normalize};
})();
