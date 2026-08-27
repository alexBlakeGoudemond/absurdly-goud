Curious to see if Wikilink images work (ie. this format: `![[theImage.png]]`)

<!--more-->

Normal markdown syntax: `![Screenshot showing the pagination test](pagination-test-screenshot.png)` should show
here: ![Screenshot showing the pagination test](pagination-test-screenshot.png)

Wikilink Syntax: `![[pagination-test-screenshot.png]]` should show here: ![[pagination-test-screenshot.png]]

In addition to this, its worth noting that Jekyll does not support dynamic image sizing!
In other words, controlling the size of the images using the `bar` syntax won't work. Proof is below

`![[theImage.png|300]]`: ![[pagination-test-screenshot.png|300]]

`![[theImage.png|300x100]]`: ![[pagination-test-screenshot.png|300x100]]
