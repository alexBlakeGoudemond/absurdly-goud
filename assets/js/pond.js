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
