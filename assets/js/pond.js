const wave = document.querySelector(".wave");

console.log("Wave found:", wave);

function animate(time) {
    const y = (time * 0.1) % 1000;

    wave.setAttribute(
        "d",
        `M0 ${y}
         Q250 ${y - 50} 500 ${y}
         T1000 ${y}`
    );

    requestAnimationFrame(animate);
}

requestAnimationFrame(animate);