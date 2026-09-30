---
layout: page
permalink: /software/
title: software
description: open-source software written or co-developed by the group. Details are refreshed weekly from GitHub.
nav: true
nav_order: 6
---

{% if site.data.repositories.github_repos %}
<div class="repositories d-flex flex-wrap flex-md-row flex-column justify-content-between align-items-stretch">
  {% for repo in site.data.repositories.github_repos %}
    {% include repository/repo.html repository=repo %}
  {% endfor %}
</div>
{% endif %}
