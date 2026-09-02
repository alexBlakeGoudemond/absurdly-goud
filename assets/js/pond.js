const waves = document.querySelectorAll(".wave");

const waveData = [];

const waveSpacing = 150;
const screenHeight = 1000;
const buffer = 150;

let wiggleAmplitude = 4 + Math.random() * 1.3;
let wiggleSpeed = 0.00002 + Math.random() * 0.002;
let randomStartingPoint = Math.random() * Math.PI * 2;
let verticalSpeed = 0.02;
let verticalAmplitude = 2.5;
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
    waveData.forEach(data => {
        let downwardMovement = data.baseY + (time * data.verticalSpeed);
        // Once the wave has moved below the screen,
        // move it back above the screen.
        downwardMovement = ((downwardMovement + buffer) % (screenHeight + buffer)) - buffer;
        const verticalWiggle = Math.sin(time * 0.001 + data.phase) * data.verticalAmplitude;
        downwardMovement += verticalWiggle;

        // Create points across the width.
        const points = [];
        for (let x = 0; x <= 1000; x += 100) {
            const wiggle = Math.sin(x * verticalSpeed + time * data.wiggleSpeed + data.phase) * data.wiggleAmplitude;
            points.push({x: x, y: downwardMovement + wiggle});
        }

        // Build the SVG svgPath.
        let svgPath = `M${points[0].x} ${points[0].y}`;

        for (let i = 1; i < points.length; i++) {
            const previous = points[i - 1];
            const current = points[i];
            const controlX =
                (previous.x + current.x) / 2;
            svgPath += `Q${controlX} ${previous.y} ${current.x} ${current.y}`;
        }

        data.wave.setAttribute("d", svgPath);
    });

    requestAnimationFrame(animate);
}

requestAnimationFrame(animate);
