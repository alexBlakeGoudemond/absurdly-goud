const waves = document.querySelectorAll(".wave");

const waveData = [];

const waveSpacing = 180;
const screenHeight = 1000;
const buffer = 250;

// How wide each arc is.
const arcWidth = 400;

let verticalSpeed = 0.03;
let verticalAmplitude = 1.5;
let wiggleAmplitude = 20 + Math.random() * 15;
let wiggleSpeed = 0.0005 + Math.random() * 0.001;
let randomStartingPoint = Math.random() * Math.PI * 2;
waves.forEach((wave, index) => {
    let startingPosition = index * waveSpacing - buffer;
    waveData.push({
        wave: wave,
        baseY: startingPosition,
        verticalSpeed: verticalSpeed,
        verticalAmplitude: verticalAmplitude,
        wiggleAmplitude: wiggleAmplitude,
        wiggleSpeed: wiggleSpeed,
        phase: randomStartingPoint
    });
});


function animate(time) {
    waveData.forEach(data => { // Move the arc downward.
        let y = data.baseY + time * data.verticalSpeed;
        // Wrap the arc back to the top.
        y = ((y + buffer) % (screenHeight + buffer)) - buffer;

        // Give this arc its own gentle vertical movement.
        y += Math.sin(time * 0.001 + data.phase) * data.verticalAmplitude;

        /*
        * * Build a large arc.
        *
        *
        * The arc extends beyond both sides
        * of the screen, so we only see part of it.
        * */
        const points = [];
        for (let x = -200; x <= 1200; x += 100) { // Large, slow curve across the screen.
            const arc = Math.sin((x / arcWidth) + time * data.wiggleSpeed + data.phase) * data.wiggleAmplitude;
            points.push({x: x, y: y + arc});
        }
        // Build the SVG path.
        let svgPath = `M${points[0].x} ${points[0].y}`;
        // Use quadratic curves instead of straight lines.
        for (let i = 1; i < points.length; i++) {
            const previous = points[i - 1];
            const current = points[i];
            const controlX = (previous.x + current.x) / 2;
            const controlY = (previous.y + current.y) / 2;
            svgPath += ` Q${controlX} ${previous.y} ` + `${current.x} ${current.y}`;
        }
        data.wave.setAttribute("d", svgPath);
    });
    requestAnimationFrame(animate);
}

requestAnimationFrame(animate);

const ducks = document.querySelectorAll(
    "#pond-duck-1, #pond-duck-2, #pond-duck-3"
);

const rippleContainer =
    document.querySelector("#duck-ripples");

const duckData = [];

const duckScreenHeight = 1000;
const duckBuffer = 150;

// Stagger settings: one duck every N ms
const duckStaggerInterval = 8400; // milliseconds between duck spawns
let animationStart = null; // will be set to the first animate timestamp
let lastDuckSpawnOffset = 0; // offset (ms) of the last scheduled spawn (relative to animationStart)


// How often each duck creates a ripple.
const rippleInterval = 900;

// Random speed (increased for faster vertical movement).
let duckSpeed = 0.3 + Math.random() * 0.5;
// Create data for each duck. Assign an initial spawn offset so ducks appear staggered in a sequence.
ducks.forEach((duck, index) => {

    const data = {
        duck: duck,

        // Starting position (closer so they appear sooner once spawned).
        x: Math.random() * 1000,
        y: -duckBuffer / 2,

        // Distance travelled (small randomized offset to avoid simultaneous alignment).
        distance: Math.random() * 10,

        // Movement (will be randomized on reset).
        speed: 2,

        angle: 0,
        directionX: 0,
        directionY: 1,

        // Floating motion.
        bobAmplitude: 8,
        bobSpeed: 0.001,

        // Gentle sideways drift.
        driftAmplitude: 5,
        driftSpeed: 0.001,

        // Random movement phase.
        phase: Math.random() * Math.PI * 2,

        // Time of the last ripple.
        lastRipple: 0,

        // Spawn control (offset in ms relative to animationStart)
        spawnOffset: index * duckStaggerInterval,
        spawned: false
    };

    duckData.push(data);
});


// Give a duck a new journey.
function resetDuck(data) {

    // Start above the screen (closer so they appear sooner).
    data.y = -duckBuffer / 2;

    // Random horizontal position.
    data.x = Math.random() * 1000;

    // Reset journey distance (small random offset so some ducks start closer).
    data.distance = Math.random() * 10;

    data.speed = duckSpeed;

    // Random direction.
    // -30° = down-left
    // +30° = down-right
    data.angle =
        -15 + Math.random() * 30;

    const angle =
        data.angle * Math.PI / 180;

    data.directionX =
        Math.sin(angle);

    data.directionY =
        Math.cos(angle);

    // Randomise floating behaviour.
    data.phase =
        Math.random() * Math.PI * 2;

    data.bobSpeed =
        0.001 + Math.random() * 0.001;

    data.driftSpeed =
        0.001 + Math.random() * 0.001;

    // Allow a ripple shortly after entering.
    data.lastRipple = 0;
}


// Give every duck its first journey.
duckData.forEach(data => {
    resetDuck(data);
});

// Initialize the spawn offset tracker so future respawns continue the stagger sequence.
lastDuckSpawnOffset = (ducks.length - 1) * duckStaggerInterval;


// Create a ripple at the duck's current position.
function createRipple(data, time) {

    const ripple =
        document.createElementNS(
            "http://www.w3.org/2000/svg",
            "ellipse"
        );

    ripple.classList.add("duck-ripple");

    /*
     * The duck coordinates are already using
     * the same 0–1000 coordinate system as
     * the SVG.
     */
    const x =
        data.x +
        data.distance * data.directionX;

    const y =
        data.y +
        data.distance * data.directionY;


    ripple.setAttribute("cx", x);
    ripple.setAttribute("cy", y);

    // Start as a small ripple.
    ripple.setAttribute("rx", 5);
    ripple.setAttribute("ry", 2);

    rippleContainer.appendChild(ripple);


    // Animate the ripple.
    const duration = 2500;
    const startTime = time;


    function animateRipple(currentTime) {

        const elapsed =
            currentTime - startTime;

        const progress =
            Math.min(elapsed / duration, 1);


        /*
         * Ease-out makes the ripple expand
         * quickly at first and then slow down.
         */
        const eased =
            1 - Math.pow(1 - progress, 3);


        // Grow the ripple.
        const rx =
            5 + eased * 55;

        const ry =
            2 + eased * 18;


        ripple.setAttribute("rx", rx);
        ripple.setAttribute("ry", ry);


        // Fade out gradually.
        const opacity =
            0.20 * (1 - progress);

        ripple.style.stroke =
            `rgba(255, 255, 255, ${opacity})`;


        // Remove once finished.
        if (progress < 1) {

            requestAnimationFrame(
                animateRipple
            );

        } else {

            ripple.remove();
        }
    }


    requestAnimationFrame(animateRipple);
}


function animateDucks(time) {

    // Establish a consistent animation baseline on first frame
    if (animationStart === null) {
        animationStart = time;
        // ensure lastDuckSpawnOffset begins at the last initial spawn we've assigned
        // (this was set after initial resets)
    }

    duckData.forEach(data => {

        // If it's not yet this duck's turn to appear, keep it hidden/offscreen.
        if (time < animationStart + (data.spawnOffset || 0)) {
            data.duck.style.display = 'none';
            return;
        }

        // Make visible once spawned
        data.duck.style.display = '';

        // Move the duck forward.
        data.distance += data.speed;

        // Calculate its position.
        let x =
            data.x +
            data.distance * data.directionX;

        let y =
            data.y +
            data.distance * data.directionY;


        // Gentle bobbing.
        y +=
            Math.sin(
                time * data.bobSpeed +
                data.phase
            ) *
            data.bobAmplitude;


        // Gentle sideways drift.
        x +=
            Math.sin(
                time * data.driftSpeed +
                data.phase
            ) *
            data.driftAmplitude;


        // Position the duck.
        data.duck.style.left =
            `${x / 10}%`;

        data.duck.style.top =
            `${y / 10}%`;


        // Create a new ripple periodically.
        if (
            time - data.lastRipple >
            rippleInterval
        ) {

            createRipple(data, time);

            data.lastRipple = time;
        }


        // Reset when the duck leaves the bottom.
        if (
            y >
            duckScreenHeight + duckBuffer
        ) {

            // Schedule its next spawn so ducks keep appearing one-by-one.
            lastDuckSpawnOffset += duckStaggerInterval;

            resetDuck(data);

            // Assign the next spawn offset (relative to animationStart)
            data.spawnOffset = lastDuckSpawnOffset;

            // Hide until its spawn time arrives
            data.duck.style.display = 'none';
            return;
        }

    });


    requestAnimationFrame(animateDucks);
}


requestAnimationFrame(animateDucks);