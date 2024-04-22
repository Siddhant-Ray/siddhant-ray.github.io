---
layout: page
permalink: /publications/
title: Publications
description: Publications by categories in reversed chronological order.
years: [2024, 2022, 2020]
nav: true
nav_order: 1
---
<!-- _pages/publications.md -->
<div class="publications">

<h1> peer reviewed </h1>

{% for y in page.years %}
  <h2 class="year">{{y}}</h2>
  {% bibliography -f papers -q @*[year={{y}}]* %}
{% endfor %}

<h1>preprints</h1>

{% bibliography -f preprints %}

</div>
