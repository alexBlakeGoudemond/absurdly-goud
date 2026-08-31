import unittest

from scripts.parsing_markdown.filenames import slugify_filename


class TestSlugifyFilename(unittest.TestCase):

    def test_spaces_become_hyphens_and_lowercased(self):
        result = slugify_filename("2026-08-27 Vision Whiteboard Showing.md")
        self.assertEqual(result, "2026-08-27-vision-whiteboard-showing.md")

    def test_existing_hyphens_in_date_are_untouched(self):
        result = slugify_filename("2026-08-27 Update.md")
        self.assertEqual(result, "2026-08-27-update.md")

    def test_extension_is_preserved_as_is(self):
        result = slugify_filename("My Drawing.excalidraw.md")
        self.assertEqual(result, "my-drawing.excalidraw.md")

    def test_already_slug_filename_is_unchanged(self):
        result = slugify_filename("already-a-slug.md")
        self.assertEqual(result, "already-a-slug.md")

    def test_no_extension_still_slugifies_stem(self):
        result = slugify_filename("CNAME")
        self.assertEqual(result, "cname")


if __name__ == '__main__':
    unittest.main()
