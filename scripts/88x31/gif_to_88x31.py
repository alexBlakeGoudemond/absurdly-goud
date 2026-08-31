# Setup: pip install pillow
# Usage: python gif_to_88x31.py free-real-estate.gif

import sys
from pathlib import Path

from PIL import Image, ImageFilter

WIDTH = 88
HEIGHT = 31


def prepare_foreground(frame):
    """
    Scale the frame to 31px high while preserving its aspect ratio,
    then sharpen it to recover detail lost during downscaling.
    """

    width = int(frame.width * (HEIGHT / frame.height))

    foreground = frame.resize(
        (width, HEIGHT),
        Image.Resampling.LANCZOS
    )

    # Restore crispness lost during downscaling.
    foreground = foreground.filter(
        ImageFilter.UnsharpMask(
            radius=0.8,
            percent=150,
            threshold=2
        )
    )

    return foreground


def make_blurred_background(frame):
    """
    Create an 88x31 background using a zoomed and blurred
    version of the current frame.
    """

    scale = max(
        WIDTH / frame.width,
        HEIGHT / frame.height
    )

    bg = frame.resize(
        (
            int(frame.width * scale),
            int(frame.height * scale)
        ),
        Image.Resampling.LANCZOS
    )

    left = (bg.width - WIDTH) // 2
    top = (bg.height - HEIGHT) // 2

    bg = bg.crop(
        (
            left,
            top,
            left + WIDTH,
            top + HEIGHT
        )
    )

    return bg.filter(
        ImageFilter.GaussianBlur(radius=3)
    )


def make_mirrored_background(frame):
    """
    Create an 88x31 background by extending the image horizontally
    using mirrored copies of the frame.
    """

    # Scale the frame to the correct height.
    foreground = prepare_foreground(frame)

    canvas = Image.new(
        "RGBA",
        (WIDTH, HEIGHT)
    )

    x = 0
    direction = 1

    while x < WIDTH:

        if direction == 1:
            piece = foreground
        else:
            piece = foreground.transpose(
                Image.Transpose.FLIP_LEFT_RIGHT
            )

        canvas.alpha_composite(
            piece,
            (x, 0)
        )

        x += piece.width
        direction *= -1

    # Crop the mirrored pattern to exactly 88px wide.
    left = (canvas.width - WIDTH) // 2

    return canvas.crop(
        (
            left,
            0,
            left + WIDTH,
            HEIGHT
        )
    )


def create_button(frame, background_type):
    """
    Create a single 88x31 frame.
    """

    frame = frame.convert("RGBA")

    # Prepare the sharp, undistorted foreground.
    foreground = prepare_foreground(frame)

    # Create the requested background.
    if background_type == "blur":
        background = make_blurred_background(frame)

    elif background_type == "mirror":
        background = make_mirrored_background(frame)

    else:
        raise ValueError(
            f"Unknown background type: {background_type}"
        )

    # Centre the original image.
    x = (WIDTH - foreground.width) // 2

    background.alpha_composite(
        foreground,
        (x, 0)
    )

    return background


def save_gif(input_path, output_path, background_type):
    """
    Convert the input GIF into an animated 88x31 GIF.
    """

    gif = Image.open(input_path)

    frames = []
    durations = []

    for frame_number in range(gif.n_frames):
        gif.seek(frame_number)

        frame = gif.convert("RGBA")

        durations.append(
            gif.info.get("duration", 40)
        )

        button = create_button(
            frame,
            background_type
        )

        # Convert to an adaptive 256-colour palette.
        button = button.convert(
            "P",
            palette=Image.Palette.ADAPTIVE
        )

        frames.append(button)

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=gif.info.get("loop", 0),
        disposal=2
    )


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python gif2button.py input.gif"
        )
        sys.exit(1)

    input_path = Path(sys.argv[1])

    blurred_output = input_path.with_name(
        f"{input_path.stem}-blurred.gif"
    )

    # mirrored_output = input_path.with_name(
    #    f"{input_path.stem}-mirrored.gif"
    # )

    print("Creating blurred version...")

    save_gif(
        input_path,
        blurred_output,
        "blur"
    )

    # print("Creating mirrored version...")

    # save_gif(
    #    input_path,
    #    mirrored_output,
    #    "mirror"
    # )

    print()
    print("Done!")
    print()
    print(f"  Blurred:  {blurred_output}")
    # print(f"  Mirrored: {mirrored_output}")


if __name__ == "__main__":
    main()
