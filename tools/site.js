(function () {
  var items = Array.prototype.slice.call(document.querySelectorAll('.docs > li'));
  var buttons = Array.prototype.slice.call(document.querySelectorAll('.aud'));
  var active = null;
  function apply(key) {
    var docs = key ? key.getAttribute('data-docs').split(' ') : null;
    items.forEach(function (li) {
      var rec = docs && docs.indexOf(li.getAttribute('data-doc')) !== -1;
      li.classList.toggle('rec', !!rec);
      li.classList.toggle('dim', !!docs && !rec);
    });
    buttons.forEach(function (b) { b.setAttribute('aria-pressed', b === key ? 'true' : 'false'); });
  }
  buttons.forEach(function (b) {
    b.addEventListener('click', function () {
      active = active === b ? null : b;
      apply(active);
      if (active) {
        var first = active.getAttribute('data-docs').split(' ')[0];
        var target = document.getElementById('doc-' + first);
        if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
  apply(null);
  // Expand the sub-list of the document currently in view.
  if ('IntersectionObserver' in window) {
    var sections = Array.prototype.slice.call(document.querySelectorAll('section.doc'));
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        var id = e.target.id.replace('doc-', '');
        items.forEach(function (li) { li.classList.toggle('open', li.getAttribute('data-doc') === id); });
      });
    }, { rootMargin: '-10% 0px -70% 0px' });
    sections.forEach(function (s) { io.observe(s); });
  }
  var toggle = document.getElementById('menu-toggle');
  var list = document.getElementById('rail-list');
  toggle.addEventListener('click', function () {
    var open = list.classList.toggle('show');
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
  });
  list.addEventListener('click', function (e) {
    if (e.target.tagName === 'A' && window.innerWidth <= 900) { list.classList.remove('show'); toggle.setAttribute('aria-expanded', 'false'); }
  });
})();
