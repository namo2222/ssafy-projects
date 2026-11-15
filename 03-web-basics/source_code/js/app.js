/* ThRead demo behavior: tabs/modal/carousel use Bootstrap 5.3 bundle. */
document.addEventListener('DOMContentLoaded', () => {
  // Pagination is real client-side pagination: 3 threads per page.
  const threadGroups = document.querySelectorAll('[data-thread-root]');
  threadGroups.forEach(section => {
    const items = Array.from(section.querySelectorAll('[data-thread-item]'));
    const pages = Array.from(section.querySelectorAll('[data-thread-page]'));
    if (!items.length) return;
    const showPage = n => {
      items.forEach((card, index) => { card.hidden = (Math.floor(index / 3) + 1 !== n); });
      pages.forEach(page => {
        const active = Number(page.dataset.threadPage) === n;
        page.classList.toggle('active', active);
        page.querySelector('a')?.setAttribute('aria-current', active ? 'page' : 'false');
      });
    };
    pages.forEach(page => {
      page.querySelector('a')?.addEventListener('click', e => {
        e.preventDefault(); showPage(Number(page.dataset.threadPage));
      });
    });
    showPage(1);
  });
  // This project is a static screen exercise: closing the logout modal does NOT create an auth session.
  document.querySelectorAll('[data-logout-confirm]').forEach(button => {
    button.addEventListener('click', () => {
      const modal = button.closest('.modal');
      if (window.bootstrap && modal) bootstrap.Modal.getOrCreateInstance(modal).hide();
      showToast('화면 구현 예제입니다. 실제 로그아웃은 서버 인증 연동 후 사용할 수 있습니다.');
    });
  });
  const save = document.querySelector('[data-save-book]');
  if (save) {
    let selected = false;
    try { selected = localStorage.getItem('thread_saved_vegetarian') === 'true'; } catch(e){}
    const render = () => {
      save.setAttribute('aria-pressed', String(selected));
      save.textContent = selected ? '✓ 담긴 도서' : '▣ 도서 담기';
    };
    save.addEventListener('click', () => {
      selected = !selected;
      try { localStorage.setItem('thread_saved_vegetarian', String(selected)); } catch(e){}
      render();
      showToast(selected ? '도서를 이 브라우저에 저장했습니다.' : '저장한 도서를 해제했습니다.');
    });
    render();
  }
  document.querySelectorAll('[data-demo-action]').forEach(button => {
    button.addEventListener('click', () => showToast(button.dataset.demoAction + ' 기능은 향후 백엔드 연동 단계에서 구현합니다.'));
  });
});
function showToast(message) {
  let host = document.querySelector('#demo-toast');
  if (!host) { host = document.createElement('div'); host.id='demo-toast';host.className='toast-container position-fixed bottom-0 end-0 p-3';document.body.appendChild(host); }
  const entry=document.createElement('div'); entry.className='toast align-items-center text-bg-dark border-0';entry.setAttribute('role','status');
  const flex=document.createElement('div');flex.className='d-flex';
  const text=document.createElement('div');text.className='toast-body';text.textContent=message;
  const close=document.createElement('button');close.type='button';close.className='btn-close btn-close-white me-2 m-auto';close.setAttribute('data-bs-dismiss','toast');close.setAttribute('aria-label','닫기');
  flex.append(text,close);entry.append(flex);host.append(entry);
  if(window.bootstrap){const toast=new bootstrap.Toast(entry,{delay:3200});entry.addEventListener('hidden.bs.toast',()=>entry.remove());toast.show();}
  else {entry.style.display='block';close.addEventListener('click',()=>entry.remove());}
}
