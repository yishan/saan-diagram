// Run before styles to apply saved appearance and resolve the automatic entry URL.
(() => {
  const root = document.documentElement;
  const keys = { language: 'saankits.language', theme: 'saankits.theme' };
  const read = key => { try { return localStorage.getItem(key); } catch { return null; } };
  const save = (key, value) => { try { localStorage.setItem(key, value); } catch { /* Preferences still work for this visit. */ } };
  const language = value => /^zh(?:-|$)/i.test(value || '') ? 'zh' : /^en(?:-|$)/i.test(value || '') ? 'en' : null;
  const currentLanguage = language(root.lang) || 'en';
  const url = new URL(location.href);
  const explicitLanguage = ['en', 'zh'].includes(url.searchParams.get('lang')) ? url.searchParams.get('lang') : null;
  // The collection homepage used to host Diagram. Keep its old section links.
  if (root.dataset.legacyDiagram && url.hash.length > 1 && url.hash !== '#collection-install') {
    const target = new URL(root.dataset.legacyDiagram, url);
    target.search = url.search;
    target.hash = url.hash;
    if (!explicitLanguage && root.dataset.languageEntry === 'explicit') {
      target.searchParams.set('lang', currentLanguage);
    }
    location.replace(target.href);
    return;
  }
  const alternate = lang => document.querySelector(`link[rel="alternate"][hreflang="${lang === 'zh' ? 'zh-CN' : 'en'}"]`);
  if (alternate('en') && alternate('zh')) {
    const browserLanguage = (navigator.languages || [navigator.language]).map(language).find(Boolean) || 'en';
    const desiredLanguage = explicitLanguage || (root.dataset.languageEntry === 'auto'
      ? language(read(keys.language)) || browserLanguage : currentLanguage);
    if (explicitLanguage) save(keys.language, explicitLanguage);
    if (desiredLanguage !== currentLanguage) {
      const target = new URL(alternate(desiredLanguage).href);
      target.search = url.search;
      target.hash = url.hash;
      location.replace(target.href);
    }
  }

  const media = matchMedia('(prefers-color-scheme: dark)');
  let theme = read(keys.theme);
  if (!['light', 'dark', 'system'].includes(theme)) theme = 'system';
  const applyTheme = () => {
    if (theme === 'system') delete root.dataset.theme;
    else root.dataset.theme = theme;
    root.style.colorScheme = theme === 'system' ? (media.matches ? 'dark' : 'light') : theme;
    document.querySelectorAll('[data-theme-choice]').forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.themeChoice === theme));
    });
    document.querySelectorAll('[data-theme-icon]').forEach(icon => { icon.toggleAttribute('hidden', icon.dataset.themeIcon !== theme); });
    const trigger = document.querySelector('[data-theme-controls] summary');
    const selected = document.querySelector(`[data-theme-choice="${theme}"]`);
    if (trigger && selected) {
      const label = trigger.dataset.preferenceLabel + (currentLanguage === 'zh' ? '：' : ': ') + selected.textContent.trim();
      trigger.setAttribute('aria-label', label);
      trigger.title = label;
    }
  };
  applyTheme();
  media.addEventListener('change', applyTheme);
  addEventListener('storage', event => {
    if (event.key !== keys.theme && event.key !== null) return;
    const stored = read(keys.theme);
    theme = ['light', 'dark', 'system'].includes(stored) ? stored : 'system';
    applyTheme();
  });
  document.addEventListener('DOMContentLoaded', () => {
    const pickers = [...document.querySelectorAll('[data-preference]')];
    const closePicker = (picker, restoreFocus = false) => {
      if (!picker) return;
      picker.open = false;
      if (restoreFocus) picker.querySelector('summary').focus();
    };
    pickers.forEach(picker => {
      const trigger = picker.querySelector('summary');
      picker.addEventListener('toggle', () => {
        if (picker.open) pickers.filter(other => other !== picker).forEach(other => closePicker(other));
      });
      picker.addEventListener('focusout', event => {
        if (!picker.contains(event.relatedTarget)) closePicker(picker);
      });
      picker.addEventListener('keydown', event => {
        if (event.key === 'Escape' && picker.open) {
          event.preventDefault();
          closePicker(picker, true);
          return;
        }
        const items = [...picker.querySelectorAll('.preference-menu a, .preference-menu button')];
        if (event.target === trigger && ['ArrowDown', 'ArrowUp'].includes(event.key)) {
          event.preventDefault();
          picker.open = true;
          items[event.key === 'ArrowDown' ? 0 : items.length - 1].focus();
        } else if (items.includes(event.target) && ['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) {
          event.preventDefault();
          const index = items.indexOf(event.target);
          const next = event.key === 'Home' ? 0 : event.key === 'End' ? items.length - 1
            : (index + (event.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length;
          items[next].focus();
        }
      });
    });
    document.addEventListener('pointerdown', event => {
      pickers.filter(picker => !picker.contains(event.target)).forEach(picker => closePicker(picker));
    });
    document.querySelectorAll('[data-language]').forEach(link => {
      const updateTarget = () => {
        const target = new URL(link.href);
        target.search = location.search;
        target.searchParams.set('lang', link.dataset.language);
        target.hash = location.hash;
        link.href = target.href;
      };
      updateTarget();
      addEventListener('hashchange', updateTarget);
      link.addEventListener('click', () => {
        updateTarget();
        save(keys.language, link.dataset.language);
        closePicker(link.closest('[data-preference]'));
      });
    });
    document.querySelectorAll('[data-theme-choice]').forEach(button => {
      button.addEventListener('click', () => {
        theme = button.dataset.themeChoice;
        save(keys.theme, theme);
        applyTheme();
        closePicker(button.closest('[data-preference]'), true);
      });
    });
    document.querySelectorAll('[data-theme-controls]').forEach(control => { control.hidden = false; });
    applyTheme();
  });
})();
