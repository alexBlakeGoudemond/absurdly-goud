import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

# scripts/88x31/gif_to_88x31.py can't be reached with a normal dotted
# import (a path segment starting with a digit, '88x31', isn't a legal
# Python identifier), so it's loaded directly from its file path instead.
MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "88x31" / "gif_to_88x31.py"
_spec = importlib.util.spec_from_file_location("gif_to_88x31", MODULE_PATH)
gif_to_88x31 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gif_to_88x31)

WIDTH = gif_to_88x31.WIDTH
HEIGHT = gif_to_88x31.HEIGHT


def make_frame(width: int, height: int, color=(255, 0, 0)) -> Image.Image:
    return Image.new("RGB", (width, height), color)


def write_gif(path: Path, frames: list, durations: list, loop: int = 0) -> None:
    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=loop,
    )


class TestPrepareForeground(unittest.TestCase):

    def test_scales_to_target_height_preserving_aspect_ratio(self):
        frame = make_frame(200, 100)  # 2:1 aspect ratio

        foreground = gif_to_88x31.prepare_foreground(frame)

        self.assertEqual(foreground.height, HEIGHT)
        self.assertEqual(foreground.width, 62)  # 200 * (31 / 100), truncated

    def test_tall_frame_produces_narrow_foreground(self):
        frame = make_frame(50, 200)  # tall, narrow source

        foreground = gif_to_88x31.prepare_foreground(frame)

        self.assertEqual(foreground.height, HEIGHT)
        self.assertLess(foreground.width, WIDTH)


class TestMakeBlurredBackground(unittest.TestCase):

    def test_output_is_exactly_88x31(self):
        frame = make_frame(300, 150)

        background = gif_to_88x31.make_blurred_background(frame)

        self.assertEqual(background.size, (WIDTH, HEIGHT))

    def test_narrow_tall_frame_still_fills_canvas(self):
        # scale is driven by whichever dimension needs to grow more, so a
        # tall/narrow source shouldn't leave the background under-cropped.
        frame = make_frame(20, 200)

        background = gif_to_88x31.make_blurred_background(frame)

        self.assertEqual(background.size, (WIDTH, HEIGHT))


class TestMakeMirroredBackground(unittest.TestCase):
    """make_mirrored_background alpha-composites its tiled copies onto an
    RGBA canvas, so — unlike make_blurred_background — it requires an RGBA
    input frame. In production this is guaranteed by create_button, which
    always converts before calling it; these tests do the same."""

    def test_output_is_exactly_88x31(self):
        frame = make_frame(100, 50).convert("RGBA")

        background = gif_to_88x31.make_mirrored_background(frame)

        self.assertEqual(background.size, (WIDTH, HEIGHT))

    def test_output_has_alpha_channel(self):
        frame = make_frame(100, 50).convert("RGBA")

        background = gif_to_88x31.make_mirrored_background(frame)

        self.assertEqual(background.mode, "RGBA")

    def test_narrow_frame_requiring_multiple_tiles_still_fills_canvas(self):
        # A frame whose scaled-down foreground is much narrower than 88px
        # forces the while-loop in make_mirrored_background to place several
        # alternating (flipped) tiles before the canvas is full.
        frame = make_frame(20, 100).convert("RGBA")

        background = gif_to_88x31.make_mirrored_background(frame)

        self.assertEqual(background.size, (WIDTH, HEIGHT))


class TestCreateButton(unittest.TestCase):

    def test_blur_background_produces_88x31_rgba(self):
        frame = make_frame(120, 60)

        button = gif_to_88x31.create_button(frame, "blur")

        self.assertEqual(button.size, (WIDTH, HEIGHT))
        self.assertEqual(button.mode, "RGBA")

    def test_mirror_background_produces_88x31_rgba(self):
        frame = make_frame(120, 60)

        button = gif_to_88x31.create_button(frame, "mirror")

        self.assertEqual(button.size, (WIDTH, HEIGHT))
        self.assertEqual(button.mode, "RGBA")

    def test_unknown_background_type_raises_value_error(self):
        frame = make_frame(120, 60)

        with self.assertRaises(ValueError) as raised:
            gif_to_88x31.create_button(frame, "sparkle")

        self.assertIn("sparkle", str(raised.exception))

    def test_non_rgba_input_frame_is_converted(self):
        # create_button should accept any source mode (e.g. plain RGB, as
        # produced straight off a GIF frame) and not require the caller to
        # convert to RGBA first.
        frame = Image.new("RGB", (120, 60), (10, 20, 30))

        button = gif_to_88x31.create_button(frame, "blur")

        self.assertEqual(button.mode, "RGBA")


class TestSaveGif(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.tmp_path = Path(self.tmp_dir.name)

    def test_output_preserves_frame_count(self):
        input_path = self.tmp_path / "in.gif"
        output_path = self.tmp_path / "out.gif"
        frames = [make_frame(60, 30, (255, 0, 0)), make_frame(60, 30, (0, 255, 0))]
        write_gif(input_path, frames, durations=[80, 120])

        gif_to_88x31.save_gif(input_path, output_path, "blur")

        result = Image.open(output_path)
        self.assertEqual(result.n_frames, 2)

    def test_output_is_88x31(self):
        input_path = self.tmp_path / "in.gif"
        output_path = self.tmp_path / "out.gif"
        frames = [make_frame(60, 30)]
        write_gif(input_path, frames, durations=[100])

        gif_to_88x31.save_gif(input_path, output_path, "blur")

        result = Image.open(output_path)
        self.assertEqual(result.size, (WIDTH, HEIGHT))

    def test_output_preserves_per_frame_durations(self):
        input_path = self.tmp_path / "in.gif"
        output_path = self.tmp_path / "out.gif"
        frames = [make_frame(60, 30, (255, 0, 0)), make_frame(60, 30, (0, 255, 0))]
        write_gif(input_path, frames, durations=[80, 150])

        gif_to_88x31.save_gif(input_path, output_path, "blur")

        result = Image.open(output_path)
        result.seek(0)
        self.assertEqual(result.info.get("duration"), 80)
        result.seek(1)
        self.assertEqual(result.info.get("duration"), 150)

    def test_missing_duration_metadata_falls_back_to_default(self):
        # GIFs saved without explicit per-frame duration should still work,
        # falling back to gif.info.get("duration", 40).
        input_path = self.tmp_path / "in.gif"
        output_path = self.tmp_path / "out.gif"
        frame = make_frame(60, 30)
        frame.save(input_path)  # single static frame, no duration set

        gif_to_88x31.save_gif(input_path, output_path, "blur")

        result = Image.open(output_path)
        self.assertEqual(result.n_frames, 1)


class TestMain(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.tmp_path = Path(self.tmp_dir.name)
        self.original_argv = sys.argv
        self.addCleanup(setattr, sys, "argv", self.original_argv)

    def test_no_arguments_exits_with_usage_error(self):
        sys.argv = ["gif_to_88x31.py"]

        with self.assertRaises(SystemExit) as raised:
            gif_to_88x31.main()

        self.assertEqual(raised.exception.code, 1)

    def test_too_many_arguments_exits_with_usage_error(self):
        sys.argv = ["gif_to_88x31.py", "one.gif", "two.gif"]

        with self.assertRaises(SystemExit) as raised:
            gif_to_88x31.main()

        self.assertEqual(raised.exception.code, 1)

    def test_valid_argument_writes_blurred_output_next_to_input(self):
        input_path = self.tmp_path / "free-real-estate.gif"
        write_gif(input_path, [make_frame(60, 30)], durations=[100])
        sys.argv = ["gif_to_88x31.py", str(input_path)]

        gif_to_88x31.main()

        expected_output = self.tmp_path / "free-real-estate-blurred.gif"
        self.assertTrue(expected_output.exists())


if __name__ == "__main__":
    unittest.main()
