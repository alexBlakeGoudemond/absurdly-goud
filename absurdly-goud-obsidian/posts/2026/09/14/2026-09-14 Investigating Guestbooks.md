A video popped into my feed that I liked, about guestbooks: [Veronika Explains | Guestbook](https://youtu.be/ZSBYO1BYrDM?si=TL2T-jEKnaiFY-sN). I have been seeing guestbooks on other websites, and something in Veronika's video made me feel like I could achieve this on mine.

In terms of design, guestbooks at their core are about allowing other people to add content to your site. Two broad strategies exist:

- **Guestbook entries become part of the site's resources/content**, either immediately or after a delay
    - They can be saved, cached, generated, etc. and somehow `merged` into the site's content
    - The merge can be delayed so that entries can be moderated before publication
- **Guestbook entries are stored somewhere else and loaded dynamically into the site via JavaScript**
    - The site fetches the data and updates the DOM
    - The guestbook entries are therefore never part of the site's statically generated content

In addition to these strategies, people have expressed how, in the early days of the web, guestbooks had several challenges:
- **Security** — incoming content is untrusted and needs to be handled safely. For example, allowing arbitrary HTML or JavaScript into a page could create security vulnerabilities.
- **Bullying / abuse** — people can bicker, be unpleasant, or use the guestbook to harass others because the platform accepts incoming content.
- **Low-quality additions / spam** — people can send multiple low-value comments such as `HI`, `HI`, `HI`.

Considering all of this, I am leaning towards a design that allows me to:
- moderate content
- control what data I want to add to my website
- control when content is added to my site and by whom
    - as such, delay bringing additions into the published site
- maintain the system easily
- keep the site itself static

From my existing research, here is the flow I like:

```text
Visitor submits something
        ↓
It gets stored somewhere
        ↓
I review it later
        ↓
I approve/reject it
        ↓
Approved content becomes part of my site
        ↓
Jekyll rebuilds the static site
```

Options exist:
- **Render** — host a small API/application with a database that I interact with.
- **Railway** — similar: host a small API/application and database, with relatively little infrastructure to manage.
- **Fly.io** — similar, but with more infrastructure/control.
- **AWS** — similar capabilities, but with substantially more cloud infrastructure and concepts.
- **DigitalOcean / Hetzner / Cloudflare / Netlify** — alternatives for hosting applications, databases, serverless functions, or related infrastructure.
- **Webmentions and Webmention.io**
    - **Webmention** as the protocol: a notification that a source URL mentions a target URL.
    - **Webmention.io** as a hosted receiver that can receive, store, and expose Webmentions through an API.

Before committing to anything, I need to investigate:
- cost?
- setup and maintenance?
- does it actually work for my guestbook use case?
- can I delay retrieval/processing?
- does the service provide persistent storage, or would I need my own database?
- how long is submitted data retained before I retrieve and ingest it into my site?
- how does moderation work?
- can I export/recover all of my data if I stop using the service?
