const waves = document.querySelectorAll(".wave");

const waveData = [];

waves.forEach((wave, index) => {
    waveData.push({
        wave: wave,

        // Starting vertical position
        baseY: index * 150,

        // Overall vertical movement speed
        verticalSpeed: 0.02,

        // How much this wave moves up/down
        verticalAmplitude: 2.5,

        // Horizontal wiggle
        wiggleAmplitude: 3 + Math.random() * 10,

        // How quickly the wiggle moves
        wiggleSpeed: 0.00002 + Math.random() * 0.002,

        // Random starting point
        phase: Math.PI * 2
    });
});


function animate(time) {

    waveData.forEach(data => {

        // Move the entire wave downward.
        const verticalFlow =
            (time * data.verticalSpeed) % 1050;

        // Move this particular wave up and down.
        const verticalWiggle =
            Math.sin(
                time * 0.001 + data.phase
            ) * data.verticalAmplitude;

        const y =
            data.baseY +
            verticalFlow +
            verticalWiggle;

        // Create several points across the width.
        const points = [];

        for (let x = 0; x <= 1000; x += 100) {

            // Each point gets a slightly different
            // position along the sine wave.
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
        let path = `M${points[0].x} ${points[0].y}`;

        for (let i = 1; i < points.length; i++) {
            const previous = points[i - 1];
            const current = points[i];

            const controlX = (previous.x + current.x) / 2;

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