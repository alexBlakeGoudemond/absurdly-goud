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

const duckData = [];

const duckScreenHeight = 1000;
const duckBuffer = 150;


// Create data for each duck.
ducks.forEach(duck => {

    const data = {
        duck: duck,

        // Starting position.
        // This is always above the screen.
        x: Math.random() * 1000,
        y: -duckBuffer,

        // Distance travelled so far.
        distance: 0,

        // Speed will be randomised.
        speed: 0,

        // Direction.
        angle: 0,
        directionX: 0,
        directionY: 1,

        // Floating motion.
        bobAmplitude: 8,
        bobSpeed: 0,

        // Gentle sideways drift.
        driftAmplitude: 5,
        driftSpeed: 0,

        // Random phase.
        phase: 0
    };

    duckData.push(data);
});


// Give a duck a new journey.
function resetDuck(data) {

    // Start above the screen.
    data.y = -duckBuffer;

    // Random horizontal starting position.
    data.x = Math.random() * 1000;

    // Start the journey from zero.
    data.distance = 0;


    // Random speed.
    data.speed =
        0.15 + Math.random() * 0.35;


    // Random direction.
    // -30° = down-left
    // +30° = down-right
    data.angle =
        -30 + Math.random() * 60;


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
}


// Give every duck its first journey.
duckData.forEach(data => {
    resetDuck(data);
});


function animateDucks(time) {

    duckData.forEach(data => {

        // Move this duck forward.
        data.distance += data.speed;


        // Calculate position along its journey.
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


        // Once the duck has completely left
        // the bottom of the pond, start a new journey.
        if (
            y > duckScreenHeight + duckBuffer
        ) {
            resetDuck(data);
        }

    });


    requestAnimationFrame(animateDucks);
}


requestAnimationFrame(animateDucks);
