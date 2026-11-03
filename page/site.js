// Copy exactly the visible source plus any explicitly linked prefix (Mermaid theme).
const ICONS = {
  copy: '<svg viewBox="0 0 16 16" aria-hidden="true"><rect x="5.5" y="5.5" width="8" height="8" rx="1.5"/><path d="M10.5 3.5v-.5A1 1 0 0 0 9.5 2H3a1 1 0 0 0-1 1v6.5a1 1 0 0 0 1 1h.5"/></svg>',
  done: '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="m3 8.5 3.2 3.2L13 4.8"/></svg>',
};
const show = (button, name, title) => {
  button.innerHTML = ICONS[name];
  button.title = title;
  button.classList.toggle('done', name === 'done');
};
const status = document.createElement('p');
status.className = 'sr-only';
status.setAttribute('role', 'status');
document.body.append(status);
for (const button of document.querySelectorAll('[data-copy]')) {
  const source = document.getElementById('code-' + button.dataset.copy);
  const prefix = button.dataset.copyPrefix
    ? document.getElementById('code-' + button.dataset.copyPrefix) : null;
  if (!source || (button.dataset.copyPrefix && !prefix)) continue;
  show(button, 'copy', '复制');
  button.hidden = false;
  const label = button.getAttribute('aria-label') || '复制代码';
  let timer;
  button.addEventListener('click', async () => {
    const text = (prefix ? prefix.textContent.trim() + '\n' : '') + source.textContent;
    const container = button.closest('.copy-row, .codebox, .block');
    clearTimeout(timer);
    status.textContent = '';
    try {
      await navigator.clipboard.writeText(text);
      container.querySelector('.copy-fallback')?.remove();
      show(button, 'done', '已复制');
      status.textContent = label + '：已复制';
    } catch {
      // Keep the theme in the manual fallback too; never select only the example body.
      let field = container.querySelector('.copy-fallback');
      if (!field) {
        field = document.createElement('textarea');
        field.className = 'copy-fallback';
        field.readOnly = true;
        field.setAttribute('aria-label', label + '：手动复制完整内容');
        container.append(field);
      }
      field.value = text;
      field.focus();
      field.select();
      button.title = '已选中，请手动复制';
      status.textContent = '自动复制未成功，完整内容已选中，请按系统复制快捷键。';
    }
    timer = setTimeout(() => show(button, 'copy', '复制'), 1800);
  });
}
