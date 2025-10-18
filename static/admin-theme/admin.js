document.addEventListener('DOMContentLoaded', function(){
  const btn = document.getElementById('sidebarToggle');
  const sb = document.getElementById('adminSidebar');
  const closeBtn = document.getElementById('sidebarClose');

  function toggleSidebar(){
    if(!sb) return;
    sb.classList.toggle('open');
  }

  if(btn) btn.addEventListener('click', toggleSidebar);
  if(closeBtn) closeBtn.addEventListener('click', toggleSidebar);

  // Close sidebar on outside click (mobile)
  document.addEventListener('click', function(e){
    if(!sb) return;
    if(sb.classList.contains('open') && !sb.contains(e.target) && e.target.id !== 'sidebarToggle'){
      sb.classList.remove('open');
    }
  });
  
  // Per-app collapse state
  const appToggles = document.querySelectorAll('.app-toggle');
  const storageKey = 'nag_admin_sidebar_state_v1';
  let state = {};
  try{
    state = JSON.parse(localStorage.getItem(storageKey) || '{}');
  }catch(e){ state = {}; }

  function setModelListVisibility(toggleBtn, open){
    const li = toggleBtn.closest('.sidebar-app');
    const list = li ? li.querySelector('.model-list') : null;
    if(!list) return;
    toggleBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    if(open){ list.removeAttribute('hidden'); toggleBtn.textContent = '▾ ' + toggleBtn.querySelector('.app-name').textContent; }
    else{ list.setAttribute('hidden', ''); toggleBtn.textContent = '▸ ' + toggleBtn.querySelector('.app-name').textContent; }
  }

  appToggles.forEach(btn =>{
    const appKey = btn.closest('.sidebar-app')?.dataset.app || btn.querySelector('.app-name')?.textContent;
    const open = !!state[appKey];
    setModelListVisibility(btn, open);
    btn.addEventListener('click', ()=>{
      const current = btn.getAttribute('aria-expanded') === 'true';
      const next = !current;
      setModelListVisibility(btn, next);
      state[appKey] = next;
      localStorage.setItem(storageKey, JSON.stringify(state));
    });
  });
});
