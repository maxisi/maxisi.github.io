---
layout: page
permalink: /publications/
title: publications
description: my non-collaboration publications in reverse chronological order&mdash;you can also see these in <b><a href=https://inspirehep.net/literature?sort=mostrecent&size=25&page=1&q=author%3Aisi%20-%20abbott>iNSPIRE</a></b>.<br><i>an asterisk (*) indicates a mentee.</i>
years: [2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015, 2013]
nav: true
nav_order: 1
---
<!-- _pages/publications.md -->
h-index
<big><b>[98](https://inspirehep.net/literature?sort=mostrecent&size=25&page=1&q=author%3Aisi&ui-citation-summary=true)</b>
/
<b>[29](https://inspirehep.net/literature?sort=mostrecent&size=25&page=1&q=author%3Aisi%20-%20abbott&ui-citation-summary=true)</b></big>
&nbsp;<big>\|</big>&nbsp; publications <big><b>210</b> / <b>61</b></big>
&nbsp;<big>\|</big>&nbsp; citations <big><b>96k</b> / <b>3.5k</b></big>

<i><small>first number includes LIGO collaboration papers; second number excludes them</small></i>


<div class="publications">

{%- for y in page.years %}
  <h2 class="year">{{y}}</h2>
  {% bibliography -f {{ site.scholar.bibliography }} -q @*[year={{y}}]* %}
{% endfor %}

</div>
