---
layout: page
title: Topics
description: "Browse the archive by research area."
permalink: /topics/
---

{% assign topics = "reverse-engineering,game-hacking,windows-internals,compatibility,hardware-security,arcade,emulation,tooling,low-level-systems,masterpiece" | split: "," %}

{% for topic in topics %}
  {% assign topic_has_posts = false %}
  {% for p in site.posts %}
    {% if p.tags contains topic %}
      {% assign topic_has_posts = true %}
    {% endif %}
  {% endfor %}
  {% if topic_has_posts %}
<section id="{{ topic | slugify }}" class="archive-section">
<h2>{{ topic }}</h2>
<ul class="no-padding none-list archive-list">
{% for p in site.posts %}
{% if p.tags contains topic %}
{% include post-list-row.html post=p %}
{% endif %}
{% endfor %}
</ul>
</section>
  {% endif %}
{% endfor %}
