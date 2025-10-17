document.addEventListener('DOMContentLoaded', function(){
  const btn = document.getElementById('sidebarToggle');
  const sb = document.querySelector('.sidebar');
  if(btn && sb){
    btn.addEventListener('click', ()=> sb.classList.toggle('open'))
  }
});
