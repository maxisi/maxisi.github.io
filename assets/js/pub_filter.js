// Topic filter for the publications page.  Chips carry data-topic; each entry
// in _layouts/bib.html carries data-keywords (from the bib "keywords" field).
// The active topic is mirrored in the ?topic= query parameter so that research
// pages can link to a pre-filtered list.
(function () {
  function apply(topic) {
    var rows = document.querySelectorAll('.publications ol.bibliography > li');
    rows.forEach(function (li) {
      var row = li.querySelector('.row');
      var kws = (row && row.getAttribute('data-keywords')) || '';
      var show = !topic || kws.split(',').map(function (s) { return s.trim(); }).indexOf(topic) !== -1;
      li.classList.toggle('pub-hidden', !show);
    });
    // hide year headings with no visible entries
    document.querySelectorAll('.publications h2.year').forEach(function (h) {
      var list = h.nextElementSibling;
      var visible = list && list.querySelector('li:not(.pub-hidden)');
      h.classList.toggle('pub-hidden', !visible);
      if (list) list.classList.toggle('pub-hidden', !visible);
    });
    document.querySelectorAll('.pub-filter .chip').forEach(function (chip) {
      chip.classList.toggle('active', (chip.getAttribute('data-topic') || '') === (topic || ''));
    });
  }

  function setTopic(topic, push) {
    apply(topic);
    if (!push) return;
    var url = new URL(window.location.href);
    if (topic) url.searchParams.set('topic', topic); else url.searchParams.delete('topic');
    history.replaceState(null, '', url);
  }

  document.addEventListener('DOMContentLoaded', function () {
    var filter = document.querySelector('.pub-filter');
    if (!filter) return;
    filter.addEventListener('click', function (e) {
      var chip = e.target.closest('.chip');
      if (!chip) return;
      e.preventDefault();
      setTopic(chip.getAttribute('data-topic') || '', true);
    });
    var initial = new URL(window.location.href).searchParams.get('topic') || '';
    setTopic(initial, false);
  });
})();
