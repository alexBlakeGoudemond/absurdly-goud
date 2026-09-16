---
layout: default
title: "Guestbook"
---

{% include_relative guestbook-blurb.md %}

<div id="guestbook-toast" class="guestbook-toast" hidden>
  <span class="guestbook-toast-icon">✓</span>
  <span>Captured! Your message is in the queue in webmentions.io. The author will review and bring in when he can!</span>
</div>

<form class="guestbook-form" method="POST" action="https://guestbook-bridge.alexblakegoudemond.workers.dev/submit">
  <div class="guestbook-field">
    <label for="gb-name">Name</label>
    <input type="text" id="gb-name" name="name" required maxlength="100">
  </div>

  <div class="guestbook-field">
    <label for="gb-url">Your site <span class="optional">(optional)</span></label>
    <input type="url" id="gb-url" name="url" maxlength="300" placeholder="https://">
  </div>

  <div class="guestbook-field guestbook-field--message">
    <label for="gb-message">Message</label>
    <textarea id="gb-message" name="message" required maxlength="1000" rows="3"></textarea>
  </div>

<button type="submit" class="guestbook-submit">Sign the guestbook ✎</button>
</form>

