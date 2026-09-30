---
layout: page
permalink: /teaching/
title: teaching
description: courses taught at Columbia, guest lectures, and summer schools.
nav: true
nav_order: 4
---

{%- assign t = site.data.teaching -%}

## Courses

<div class="teaching-courses">
{% for c in t.courses %}
<div class="course">
  <div class="course-code">{{ c.code }}</div>
  <div class="course-body">
    <div class="course-title">{% if c.url %}<a href="{{ c.url }}">{{ c.title }}</a>{% else %}{{ c.title }}{% endif %}</div>
    <div class="course-meta">{{ c.role }}, {{ c.institution }} &middot; {{ c.years }}</div>
    {% if c.description %}<div class="course-description">{{ c.description }}</div>{% endif %}
  </div>
</div>
{% endfor %}
</div>

{% if t.guest_lectures %}
## Guest lectures

<ul class="teaching-list">
{% for g in t.guest_lectures %}
  <li><strong>{{ g.institution }}</strong> ({{ g.year }}): {{ g.courses | join: "; " }}.</li>
{% endfor %}
</ul>
{% endif %}

{% if t.schools %}
## Summer schools

<ul class="teaching-list">
{% for s in t.schools %}
  <li><strong>{{ s.name }}</strong>, {{ s.institution }} ({{ s.year }}).{% if s.description %} {{ s.description }}{% endif %}</li>
{% endfor %}
</ul>
{% endif %}

{% if t.mentoring %}
## Mentoring

{{ t.mentoring }}
{% endif %}
