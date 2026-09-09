The animated background in this website was built up slowly, and now there are swimming ducks! Below I will explain how I achieved this

![[swimming-duck-example.png]]

The animation is done with CSS, JS and HTML. It is made up of the 'water' and the ducks themselves. JS then updates the position of the waves and the ducks to create the movement. 

Specifically, when looking at [[website-design#How does this website work?|how this website works]], inside `site_src`:
- `assets/js/pond.js` has the movement logic
- `_includes/animated-background.html` has the template for the animation itself
- `assets/site-background/*.svg` has the duck collection
- `assets/css/animated-background.css` has the styling
- 10 wave elements are defined, with JS filling in their data each frame
	- This movement is achieved through `requestAnimationFrame()` see [MDN Reference | requestAnimationFrame](https://developer.mozilla.org/docs/Web/API/DedicatedWorkerGlobalScope/requestAnimationFrame)
- Key parts of this animation include:
	- The `time` attribute, provided by the browser via `requestAnimationFrame`
	- The wave shape via trigonometry: `phase`, `wiggleSpeed`, and `wiggleAmplitude`
	- A SVG path is built from those points using quadratic curves (`Q`)
	- JS fills in the data each frame - creation movement as the

The smoothness is done with tricks:
- Waves and ducks begin and end outside the view window - moving downward
- The wave oscillation created the up-down wobble that bends
- As the wave bends it also moves downwards

`animateDucks(time)` then moves the ducks, simulating gentle side-to-side movement and bobbing. A ripple periodically comes out the back of them - implying movement ontop of the water

Finally there is a power toggle to pause the animation