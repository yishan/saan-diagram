// Copy exactly the visible source plus any explicitly linked prefix (Mermaid theme).
const ICONS = {
  copy: '<svg viewBox="0 0 16 16" aria-hidden="true"><rect x="5.5" y="5.5" width="8" height="8" rx="1.5"/><path d="M10.5 3.5v-.5A1 1 0 0 0 9.5 2H3a1 1 0 0 0-1 1v6.5a1 1 0 0 0 1 1h.5"/></svg>',
  done: '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="m3 8.5 3.2 3.2L13 4.8"/></svg>',
};
const copyText = document.documentElement.lang.toLowerCase().startsWith('en')
  ? { copy: 'Copy', code: 'Copy code', done: 'Copied', separator: ': ', manual: 'Copy the full text manually', selected: 'Selected; copy manually', failed: 'Could not copy automatically. The full text is selected; use the Copy menu, ⌘C, or Ctrl+C.' }
  : { copy: '复制', code: '复制代码', done: '已复制', separator: '：', manual: '手动复制完整内容', selected: '已选中，请手动复制', failed: '未能自动复制。完整内容已选中，可用复制菜单或 ⌘C / Ctrl+C 复制。' };
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
  show(button, 'copy', copyText.copy);
  button.hidden = false;
  const label = button.getAttribute('aria-label') || copyText.code;
  let timer;
  button.addEventListener('click', async () => {
    const text = (prefix ? prefix.textContent.trim() + '\n' : '') + source.textContent;
    const container = button.closest('.copy-row, .codebox, .block');
    clearTimeout(timer);
    status.textContent = '';
    try {
      await navigator.clipboard.writeText(text);
      container.querySelector('.copy-fallback')?.remove();
      show(button, 'done', copyText.done);
      status.textContent = label + copyText.separator + copyText.done;
    } catch {
      // Keep the theme in the manual fallback too; never select only the example body.
      let field = container.querySelector('.copy-fallback');
      if (!field) {
        field = document.createElement('textarea');
        field.className = 'copy-fallback';
        field.readOnly = true;
        field.setAttribute('aria-label', label + copyText.separator + copyText.manual);
        container.append(field);
      }
      field.value = text;
      field.focus();
      field.select();
      button.title = copyText.selected;
      status.textContent = copyText.failed;
    }
    timer = setTimeout(() => show(button, 'copy', copyText.copy), 1800);
  });
}
