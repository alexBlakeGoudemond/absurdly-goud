export default {
    async fetch(request, env) {
        const url = new URL(request.url);

        // Serves the stored entry page — this becomes the "source" URL
        // that webmention.io verifies and stores.
        if (request.method === "GET" && url.pathname.startsWith("/entry/")) {
            const id = url.pathname.split("/entry/")[1];
            const entry = await env.GUESTBOOK_KV.get(id);
            if (!entry) return new Response("Not found", {status: 404});
            return new Response(entry, {
                headers: {"content-type": "text/html; charset=utf-8"},
            });
        }

        // Accepts the guestbook form POST, publishes an entry page,
        // then sends the actual webmention.
        if (request.method === "POST" && url.pathname === "/submit") {
            const ip = request.headers.get("cf-connecting-ip") || "unknown";
            const {success} = await env.GUESTBOOK_RATE_LIMITER.limit({key: ip});
            if (!success) {
                return new Response("Too many submissions — please try again in a minute.", {
                    status: 429,
                });
            }

            const form = await request.formData();
            const name = (form.get("name") || "Anonymous").toString().slice(0, 100);
            const message = (form.get("message") || "").toString().slice(0, 1000);
            const authorUrl = (form.get("url") || "").toString().slice(0, 300);

            if (!message.trim()) {
                return new Response("Message required", {status: 400});
            }

            const id = crypto.randomUUID();
            const entryUrl = `${url.origin}/entry/${id}`;

            const html = renderEntry({name, message, authorUrl, target: env.TARGET_URL});
            await env.GUESTBOOK_KV.put(id, html, {expirationTtl: 60 * 60 * 24 * 365});

            const body = new URLSearchParams({source: entryUrl, target: env.TARGET_URL});
            const wmResponse = await fetch(env.WEBMENTION_ENDPOINT, {
                method: "POST",
                headers: {"content-type": "application/x-www-form-urlencoded"},
                body,
            });

            if (!wmResponse.ok) {
                return new Response("Webmention failed to send", {status: 502});
            }

            // Send the visitor back to the guestbook page on your actual site
            return Response.redirect(`${env.TARGET_URL}?signed=1`, 303);
        }

        return new Response("Not found", {status: 404});
    },
};

function renderEntry({name, message, authorUrl, target}) {
    const escape = (s) =>
        s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    const authorLink = authorUrl
        ? `<a href="${escape(authorUrl)}" rel="author">${escape(name)}</a>`
        : escape(name);

    return `<!doctype html>
<html>
<head><meta charset="utf-8"><title>Guestbook entry from ${escape(name)}</title></head>
<body>
  <article class="h-entry">
    <p class="p-author h-card">${authorLink}</p>
    <p class="p-content">${escape(message)}</p>
    <a href="${escape(target)}" class="u-in-reply-to">Signed the guestbook</a>
  </article>
</body>
</html>`;
}