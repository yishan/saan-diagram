// Copy exactly the visible source plus any explicitly linked prefix (Mermaid theme).
const status = document.createElement('p');
status.className = 'sr-only';
status.setAttribute('role', 'status');
document.body.append(status);
for (const button of document.querySelectorAll('[data-copy]')) {
  const source = document.getElementById('code-' + button.dataset.copy);
  const prefix = button.dataset.copyPrefix
    ? document.getElementById('code-' + button.dataset.copyPrefix) : null;
  if (!source || (button.dataset.copyPrefix && !prefix)) continue;
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
      button.textContent = '已复制';
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
      button.textContent = '已选中';
      status.textContent = '自动复制未成功，完整内容已选中，请按系统复制快捷键。';
    }
    timer = setTimeout(() => { button.textContent = '复制'; }, 1800);
  });
}
