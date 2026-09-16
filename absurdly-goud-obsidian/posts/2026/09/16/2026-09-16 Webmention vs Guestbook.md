While pursuing a Guestbook on this site, I stumbled upon explanations of Webmention Publishers and Webmention Receivers. The distinction landed for me when I thought about Guestbooks vs Chat Forums: particularly **where the source mention lives**.

[Guestbooks](https://indieweb.org/guestbook) are journals that allow other people to leave notes when visiting your site. They are a tradition present to this day at weddings, funerals, museums, etc. Through their usage, other people can read the content, including the author. On the web, I argue, we can achieve a similar thing by allowing an individual to add a message directly on the site, where that message stays on the site. In my case, the Guestbook is therefore a localised ledger of people who have visited and left a note.

A Guestbook **can use Webmentions**, but it doesn't have to. In my implementation, I use a Webmention Receiver as part of the machinery behind the Guestbook.

Chat Forums, on the other hand, have a different strategy. They allow people to publish messages in a shared space and continue a conversation back and forth. When one of those messages contains a link to another website, the authoring site can act as a **Webmention Sender**, notifying the linked website's Webmention Receiver.

The distinction is important as I am trying to adhere to the protocol with my own site!

I want messages posted on the Guestbook to remain part of my Guestbook. Where appropriate, my site can also use Webmention to notify my own Webmention Receiver about those entries.

Separately, I want other sites mentioning my website to be able to send Webmentions to my Webmention Receiver. And when I publish something that links to someone else's website, I want my site to act as a Webmention Sender and notify their Webmention Receiver.

This is what I am trying to achieve on the site! ![[calculating-puzzled.gif]]