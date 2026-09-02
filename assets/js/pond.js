const waves = document.querySelectorAll(".wave");

const waveData = [];

const waveSpacing = 150;
const screenHeight = 1000;
const buffer = 150;

let wiggleAmplitude = 4 + Math.random() * 1.3;
let wiggleSpeed = 0.00002 + Math.random() * 0.002;
let randomStartingPoint = Math.random() * Math.PI * 2;
waves.forEach((wave, index) => {
    waveData.push({
        wave: wave,

        // Starting position.
        // The first wave starts above the screen.
        baseY: index * waveSpacing - buffer,

        // Overall downward movement speed
        verticalSpeed: 0.02,

        // Individual vertical movement
        verticalAmplitude: 2.5,

        // Horizontal wiggle
        wiggleAmplitude: wiggleAmplitude,

        // How quickly the wiggle moves
        wiggleSpeed: wiggleSpeed,

        // Random starting point
        phase: randomStartingPoint
    });
});


function animate(time) {

    waveData.forEach(data => {

        // Move the wave downward continuously.
        let y =
            data.baseY +
            time * data.verticalSpeed;

        // Once the wave has moved below the screen,
        // move it back above the screen.
        y =
            ((y + buffer) % (screenHeight + buffer))
            - buffer;


        // Individual vertical wiggle
        const verticalWiggle =
            Math.sin(
                time * 0.001 + data.phase
            ) * data.verticalAmplitude;


        y += verticalWiggle;


        // Create points across the width.
        const points = [];

        for (let x = 0; x <= 1000; x += 100) {

            const wiggle =
                Math.sin(
                    x * 0.02 +
                    time * data.wiggleSpeed +
                    data.phase
                ) * data.wiggleAmplitude;

            points.push({
                x: x,
                y: y + wiggle
            });
        }


        // Build the SVG path.
        let path =
            `M${points[0].x} ${points[0].y}`;


        for (let i = 1; i < points.length; i++) {

            const previous = points[i - 1];
            const current = points[i];

            const controlX =
                (previous.x + current.x) / 2;

            path += `
Q${controlX} ${previous.y}
${current.x} ${current.y}
`;
        }


        data.wave.setAttribute("d", path);
    });


    requestAnimationFrame(animate);
}


requestAnimationFrame(animate);