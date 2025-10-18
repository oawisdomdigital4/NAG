// Ensure any element that has a class that starts with "bi-" also has the base "bi" class.
// This helps the CSS rules targeting .bi to apply even when templates only render the specific class.
(function () {
  function addBiClass(root) {
    const walker = document.createTreeWalker(root || document.body, NodeFilter.SHOW_ELEMENT, null, false);
    let node = walker.currentNode;
    while (node) {
      for (let i = 0; i < node.classList.length; i++) {
        const cls = node.classList[i];
        if (cls && cls.indexOf && cls.indexOf('bi-') === 0) {
          if (!node.classList.contains('bi')) node.classList.add('bi');
          break;
        }
      }
      node = walker.nextNode();
    }
  }

  // Run on DOMContentLoaded and also after short delay for dynamically rendered parts
  document.addEventListener('DOMContentLoaded', function () { addBiClass(document); setTimeout(() => addBiClass(document), 2500); });
})();
