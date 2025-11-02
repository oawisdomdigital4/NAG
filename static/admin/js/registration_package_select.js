(function(){
  // Small admin enhancer: replace the plain native select with a styled dropdown
  // that shows color swatches and emoji for options. Keeps the original select
  // in sync (hidden) so server-side processing remains unchanged.
  function buildSwatchStyle(val){
    if(!val) return '';
    if(val.indexOf('gray') !== -1) return 'linear-gradient(90deg,#4b5563,#374151)';
    if(val.indexOf('gold') !== -1 || val.indexOf('amber') !== -1) return 'linear-gradient(90deg,#f6e05e,#f59e0b)';
    if(val.indexOf('red') !== -1) return 'linear-gradient(90deg,#ef4444,#b91c1c)';
    if(val.indexOf('blue') !== -1) return 'linear-gradient(90deg,#3b82f6,#2563eb)';
    return '#ddd';
  }

  function enhanceSelect(select){
    if(!select) return;
    // Do not double-enhance
    if(select.dataset.enhanced) return;
    select.dataset.enhanced = '1';

    // If there are no options, don't hide the native select — leave it visible
    if(!select.options || select.options.length === 0){
      console.warn('registration_package_select: select has no options, skipping enhancement', select);
      return;
    }

    // hide original select
    select.style.display = 'none';

    // container
    var container = document.createElement('div');
    container.className = 'rp-select-container';
    container.style.marginBottom = '8px';
    container.style.position = 'relative';
    container.style.maxWidth = '420px';

    // display box
    var display = document.createElement('button');
    display.type = 'button';
    display.className = 'rp-select-display';
    display.style.width = '100%';
    display.style.textAlign = 'left';
    display.style.padding = '6px 10px';
    display.style.border = '1px solid #d1d5db';
    display.style.borderRadius = '6px';
    display.style.background = '#fff';
    display.style.cursor = 'pointer';

    // list
    var list = document.createElement('div');
    list.className = 'rp-select-list';
    list.style.position = 'absolute';
    list.style.left = '0';
    list.style.right = '0';
    list.style.top = '110%';
    list.style.zIndex = '60';
    list.style.background = '#fff';
    list.style.border = '1px solid #e5e7eb';
    list.style.boxShadow = '0 6px 18px rgba(15,23,42,0.12)';
    list.style.borderRadius = '8px';
    list.style.maxHeight = '220px';
    list.style.overflow = 'auto';
    list.style.display = 'none';

    // build items
    Array.from(select.options).forEach(function(opt){
      var item = document.createElement('div');
      item.className = 'rp-select-item';
      item.dataset.value = opt.value;
      item.style.padding = '8px 10px';
      item.style.display = 'flex';
      item.style.alignItems = 'center';
      item.style.gap = '10px';
      item.style.cursor = 'pointer';

      // for color select, show swatch
      if(select.id.indexOf('color') !== -1){
        var sw = document.createElement('span');
        sw.style.display = 'inline-block';
        sw.style.width = '28px';
        sw.style.height = '14px';
        sw.style.borderRadius = '4px';
        var bg = buildSwatchStyle(opt.value);
        if(bg.indexOf('linear-gradient') === 0) sw.style.background = bg;
        else sw.style.background = bg;
        item.appendChild(sw);
      }

      // for icon select, show emoji
      if(select.id.indexOf('icon') !== -1){
        var emoji = document.createElement('span');
        emoji.style.fontSize = '18px';
        emoji.style.lineHeight = '1';
        emoji.textContent = opt.value || '';
        item.appendChild(emoji);
      }

  var label = document.createElement('span');
  // use text, fallback to value, then a placeholder
  label.textContent = (opt.text && opt.text.trim()) ? opt.text : (opt.value && opt.value.trim() ? opt.value : '(none)');
      item.appendChild(label);

      // click handler
      item.addEventListener('click', function(e){
        var v = this.dataset.value;
        select.value = v;
        // trigger change on original select
        var ev = document.createEvent('HTMLEvents');
        ev.initEvent('change', true, false);
        select.dispatchEvent(ev);

        // update display text
        updateDisplay();
        list.style.display = 'none';
      });

      list.appendChild(item);
    });

    function updateDisplay(){
      var val = select.value;
      var opt = select.options[select.selectedIndex];
      display.innerHTML = '';
      if(select.id.indexOf('color') !== -1){
        var sw = document.createElement('span');
        sw.style.display = 'inline-block';
        sw.style.width = '28px';
        sw.style.height = '14px';
        sw.style.borderRadius = '4px';
        sw.style.marginRight = '10px';
        var bg = buildSwatchStyle(val);
        if(bg.indexOf && bg.indexOf('linear-gradient') === 0) sw.style.background = bg; else sw.style.background = bg;
        display.appendChild(sw);
      }
      if(select.id.indexOf('icon') !== -1){
        var emoji = document.createElement('span');
        emoji.style.fontSize = '18px';
        emoji.style.lineHeight = '1';
        emoji.style.marginRight = '8px';
        emoji.textContent = val || '';
        display.appendChild(emoji);
      }
      var text = document.createElement('span');
      text.textContent = opt ? opt.text : '';
      display.appendChild(text);
    }

    display.addEventListener('click', function(e){
      e.preventDefault();
      list.style.display = (list.style.display === 'none' || list.style.display === '') ? 'block' : 'none';
    });

    // close on outside click
    document.addEventListener('click', function(ev){
      if(!container.contains(ev.target)){
        list.style.display = 'none';
      }
    });

    container.appendChild(display);
    container.appendChild(list);
    select.parentNode.insertBefore(container, select.nextSibling);

    // update initial display
    updateDisplay();

    // When the underlying select changes (e.g. via admin JS), update display
    select.addEventListener('change', updateDisplay);
  }

  document.addEventListener('DOMContentLoaded', function(){
    // Enhance any select whose id or name contains 'icon' or 'color'.
    // This covers inlines which may have ids like 'id_form-0-color' or similar.
    var selects = Array.from(document.querySelectorAll('select'));
    selects.forEach(function(s){
      var id = (s.id || '').toLowerCase();
      var name = (s.name || '').toLowerCase();
      if(id.indexOf('icon') !== -1 || name.indexOf('icon') !== -1 || id.indexOf('color') !== -1 || name.indexOf('color') !== -1){
        enhanceSelect(s);
      }
    });

    // Watch for dynamically added inline forms and enhance their selects
    var observer = new MutationObserver(function(mutations){
      mutations.forEach(function(m){
        Array.from(m.addedNodes || []).forEach(function(node){
          try{
            if(node.querySelectorAll){
              var newSelects = Array.from(node.querySelectorAll('select'));
              newSelects.forEach(function(ns){
                var nid = (ns.id||'').toLowerCase();
                var nname = (ns.name||'').toLowerCase();
                if(nid.indexOf('icon') !== -1 || nname.indexOf('icon') !== -1 || nid.indexOf('color') !== -1 || nname.indexOf('color') !== -1){
                  enhanceSelect(ns);
                }
              });
            }
          }catch(e){
            console.error('registration_package_select: mutation observer error', e);
          }
        });
      });
    });
    observer.observe(document.body, { childList: true, subtree: true });
  });
})();
