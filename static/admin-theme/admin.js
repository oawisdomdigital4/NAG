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
});
