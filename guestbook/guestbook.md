---
layout: default
title: "Guestbook"
---

<form method="POST" action="https://guestbook-bridge.alexblakegoudemond.workers.dev/submit">
  <label>
    Name
    <input type="text" name="name" required maxlength="100">
  </label>

  <label>
    Your site (optional)
    <input type="url" name="url" maxlength="300" placeholder="https://">
  </label>

  <label>
    Message
    <textarea name="message" required maxlength="1000"></textarea>
  </label>

<button type="submit">Sign the guestbook</button>
</form>