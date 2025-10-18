// remove-bullets.js
document.addEventListener("DOMContentLoaded", function () {
  try {
    // Candidate selectors which sometimes contain the circles
    const candidateSelectors = [
      ".sidebar .nav-sidebar li",
      ".sidebar .nav-list li",
      ".app-list .module li",
      ".module .model-links li",
      ".model-list li"
    ];

    candidateSelectors.forEach(sel => {
      document.querySelectorAll(sel).forEach(li => {
        // If li has a leading element (span/i) that looks like a small circle, remove it.
        const firstEl = Array.from(li.children).find(c => {
          const s = window.getComputedStyle(c);
          const w = parseFloat(s.width) || c.offsetWidth || 0;
          const h = parseFloat(s.height) || c.offsetHeight || 0;
          const bg = s.backgroundColor || s.color || "";
          // If the element looks like a known icon (has bi/fa/svg/icon classes), skip it
          if (c.className && /(^|\s)(fa|bi|svg|icon)/i.test(c.className)) {
            return false;
          }
          // small roughly-circular element heuristic or named decorative classes
          return (w > 6 && w <= 26 && Math.abs(w - h) < 8) ||
                 (c.className && /(dot|bullet|circle|marker|indicator|sidebar-dot)/i.test(c.className));
        });

        if (firstEl) {
          // only remove if it appears to be purely decorative (no text)
          if (!firstEl.textContent || firstEl.textContent.trim().length === 0) {
            firstEl.style.display = "none";
            firstEl.remove();
          }
        }
      });
    });

    // As a final sweep: hide any small round elements by computed style
    document.querySelectorAll(".sidebar *").forEach(el => {
      const s = window.getComputedStyle(el);
      const w = parseFloat(s.width) || el.offsetWidth || 0;
      const h = parseFloat(s.height) || el.offsetHeight || 0;
      const br = parseFloat((s.borderRadius || '').toString().replace("px","")) || 0;
      // Skip known icon elements
      if (el.className && /(^|\s)(fa|bi|svg|icon)/i.test(el.className)) return;
      // small, with border-radius -> likely the bullet
      if (w > 6 && w <= 26 && Math.abs(w - h) < 8 && br >= Math.min(w,h)/2 - 2) {
        el.style.display = "none";
      }
    });
  } catch (e) {
    // fail silently
    console.warn("remove-bullets script error:", e);
  }
});
