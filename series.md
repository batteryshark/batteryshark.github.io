---
layout: page
title: Series
description: "Longer threads that are easier to read in order."
permalink: /series/
---

{% assign masterpiece_posts = site.posts | where: "series", "Masterpiece" | sort: "series_part" %}

<section class="archive-section">
  <h2>Masterpiece</h2>
  <p class="muted">A six-part writeup series on building a custom operating context and frontend for PC gaming.</p>

  <ol class="archive-list">
    {% for p in masterpiece_posts %}
      {% include post-list-row.html post=p %}
    {% endfor %}
  </ol>
</section>
