---
layout: page
permalink: /group/
title: group
description: the people behind the research, at Columbia University and the Flatiron Institute's Center for Computational Astrophysics.
nav: true
nav_order: 2
wide: true
---

{% for role in site.data.people.roles %}
{%- assign people = site.data.people.members | where: "role", role.key -%}
{%- if people.size > 0 %}
<h2 class="people-role">{{ role.title }}</h2>
{% include people_grid.html role=role.key %}
{%- endif %}
{% endfor %}

{%- if site.data.people.alumni and site.data.people.alumni.size > 0 %}
<h2 class="people-role">Alumni and former mentees</h2>
<ul class="alumni-list">
  {% for person in site.data.people.alumni %}
  <li>
    <span class="alumni-name">{% if person.url %}<a href="{{ person.url }}">{{ person.name }}</a>{% else %}{{ person.name }}{% endif %}</span>
    {%- if person.role or person.start or person.end %}
    <span class="alumni-meta">
      {%- if person.role %}{{ person.role }}{% endif -%}
      {%- if person.start or person.end %} ({{ person.start }}–{{ person.end }}){% endif -%}
    </span>
    {%- endif %}
    {%- if person.now %}
    <span class="alumni-now">&rarr; {% if person.now_url %}<a href="{{ person.now_url }}">{{ person.now }}</a>{% else %}{{ person.now }}{% endif %}</span>
    {%- endif %}
  </li>
  {% endfor %}
</ul>
{%- endif %}

<h2 class="people-role" id="join">Joining the group</h2>
<div class="measure-left">
<p>
We are always happy to hear from people interested in gravitational-wave astrophysics,
black holes, statistical inference or scientific machine learning.
</p>
<ul>
  <li><strong>Undergraduates</strong> at Columbia can join for a research project during the
  semester or over the summer; get in touch with a short note on your background and interests.</li>
  <li><strong>Prospective PhD students</strong> apply through the
  <a href="https://www.astro.columbia.edu/">Columbia Astronomy graduate program</a>;
  mention your interest in the group in your application and feel free to email beforehand.</li>
  <li><strong>Postdoctoral researchers</strong> are typically supported through fellowships such as the
  <a href="https://www.simonsfoundation.org/flatiron/center-for-computational-astrophysics/">Flatiron Research Fellowship</a>
  at CCA or the <a href="https://www.stsci.edu/stsci-research/fellowships/nasa-hubble-fellowship-program">NASA Hubble Fellowship</a>.
  Please reach out before applying so we can coordinate.</li>
</ul>
<p>Contact: <a href="mailto:{{ site.email | encode_email }}">{{ site.email }}</a>.</p>
</div>
