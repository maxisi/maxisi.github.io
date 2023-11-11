---
layout: page
permalink: /publications/
title: publications
description: my non-collaboration publications in reverse chronological order. you can also see these in <a href=https://inspirehep.net/literature?sort=mostrecent&size=25&page=1&q=author%3Aisi%20-%20abbott>iNSPIRE</a>. An asterisk (*) indicates a mentee.
years: [2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015, 2013]
nav: true
nav_order: 1
---
<!-- _pages/publications.md -->
<div class="publications">

{%- for y in page.years %}
  <h2 class="year">{{y}}</h2>
  {% bibliography -f {{ site.scholar.bibliography }} -q @*[year={{y}}]* %}
{% endfor %}

</div>
