---
layout: page
permalink: /research/
title: research
description: the group's three main lines of research, each with its people, software and key papers. Jump to a topic&#58; <a href="#ringdown">ringdowns</a> &middot; <a href="#populations">populations</a> &middot; <a href="#methods">methods</a>.
nav: true
nav_order: 1
wide: true
---

{%- assign areas = site.research | sort: "order" -%}
{% for area in areas %}
<section class="research-area" id="{{ area.slug }}">
  <div class="row">
    <div class="col-md-8 research-area-text">
      <h2 class="research-area-title">{{ area.title }}</h2>
      <p class="research-area-summary">{{ area.summary }}</p>
      {{ area.content }}
    </div>
    <div class="col-md-4 research-area-side">
      <figure class="research-area-figure">
        <img class="img-fluid rounded z-depth-1" src="{{ area.img | relative_url }}" alt="">
        {% if area.img_credit %}<figcaption class="caption">{{ area.img_credit }}</figcaption>{% endif %}
      </figure>

      {%- assign people = site.data.people.members | where_exp: "m", "m.research contains area.slug" -%}
      {%- if people.size > 0 %}
      <h3 class="research-area-subtitle">People</h3>
      <ul class="research-area-people">
        {% for person in people %}
        <li><a href="{{ '/group/' | relative_url }}#{{ person.id }}">{% include person_avatar.html person=person variant="xs" %} {{ person.name }}</a></li>
        {% endfor %}
      </ul>
      {%- endif %}

      {%- if area.software %}
      <h3 class="research-area-subtitle">Software</h3>
      <div class="repositories research-area-software">
        {% for repo in area.software %}
          {% include repository/repo.html repository=repo %}
        {% endfor %}
      </div>
      {%- endif %}
    </div>
  </div>

  <h3 class="research-area-subtitle">Key papers</h3>
  <div class="publications research-area-papers">
    {% bibliography -f {{ site.scholar.bibliography }} --group_by none --max 5 -q @*[keywords^={{ area.keywords }}]* %}
  </div>
  <p class="section-more"><a href="{{ '/publications/' | relative_url }}?topic={{ area.keywords }}">All papers on this topic &rarr;</a></p>
</section>
{% endfor %}
