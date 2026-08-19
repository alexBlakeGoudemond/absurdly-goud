---
layout: default
title: Posts
permalink: /posts/
---

<h1>Posts</h1>

{% for post in site.posts %}

<article class="h-entry">

    <h2>
        <a class="u-url p-name"
           href="{{ post.url }}">
            {{ post.title }}
        </a>
    </h2>

    <time class="dt-published"
          datetime="{{ post.date | date_to_xmlschema }}">
        {{ post.date | date: "%d %B %Y" }}
    </time>

    <div class="e-content">
        {{ post.excerpt }}
    </div>

</article>

{% endfor %}