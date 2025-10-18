// Ensure any element that has a class that starts with "bi-" also has the base "bi" class.
// This helps the CSS rules targeting .bi to apply even when templates only render the specific class.
(function () {
  function addBiClassToElement(el) {
    if (!el || !el.classList) return;
    for (let i = 0; i < el.classList.length; i++) {
      const cls = el.classList[i];
      if (cls && cls.indexOf && cls.indexOf('bi-') === 0) {
        if (!el.classList.contains('bi')) el.classList.add('bi');
        break;
      }
    }
  }

  function scan(root) {
    root = root || document.body;
    if (!root) return;
    // quick selector for any element with a bi- class
    root.querySelectorAll('[class*="bi-"]').forEach(el => addBiClassToElement(el));
  }

  // Immediately run if possible
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    scan(document);
  } else {
    document.addEventListener('DOMContentLoaded', () => scan(document));
  }

  // Observe DOM changes so dynamically added items get the bi class too
  const obs = new MutationObserver(mutations => {
    for (const m of mutations) {
      if (m.type === 'childList') {
        m.addedNodes.forEach(node => {
          if (node.nodeType === 1) {
            // node itself
            if (node.matches && node.matches('[class*="bi-"]')) addBiClassToElement(node);
            // and any descendants
            node.querySelectorAll && node.querySelectorAll('[class*="bi-"]').forEach(el => addBiClassToElement(el));
          }
        });
      } else if (m.type === 'attributes' && m.attributeName === 'class') {
        const target = m.target;
        if (target && target.matches && target.matches('[class*="bi-"]')) addBiClassToElement(target);
      }
    }
  });

  if (window.MutationObserver) {
    obs.observe(document.documentElement || document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['class'] });
  }
})();
