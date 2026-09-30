---
layout: page
permalink: /publications/
title: publications
description: publications led by the group or its collaborators (excluding LIGO–Virgo–KAGRA collaboration papers), newest first; all papers are listed on <a href="https://inspirehep.net/literature?sort=mostrecent&size=25&page=1&q=a+Maximiliano.Isi.1">INSPIRE</a>. <i>An asterisk (*) marks a student or postdoc mentored by the group.</i>
years: [2026, 2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015, 2013]
nav: true
nav_order: 3
---
<!-- _pages/publications.md -->
{% include inspire_stats.html %}

<p class="pub-filter">
  <span class="pub-filter-label">Filter by topic:</span>
  <a class="chip active" href="{{ '/publications/' | relative_url }}" data-topic="">all</a>
  {%- assign areas = site.research | sort: "order" -%}
  {%- for area in areas %}
  <a class="chip" href="{{ '/publications/' | relative_url }}?topic={{ area.keywords }}" data-topic="{{ area.keywords }}">{{ area.title | downcase }}</a>
  {%- endfor %}
</p>
<script defer src="{{ '/assets/js/pub_filter.js' | relative_url | bust_file_cache }}"></script>


<div class="publications">

{%- for y in page.years %}
  <h2 class="year">{{y}}</h2>
  {% bibliography -f {{ site.scholar.bibliography }} -q @*[year={{y}}]* %}
{% endfor %}

</div>
