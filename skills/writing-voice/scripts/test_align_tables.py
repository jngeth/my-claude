#!/usr/bin/env python3
"""Tests for align_tables.py. Run with: python3 -m unittest test_align_tables"""

import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "align_tables.py"

spec = importlib.util.spec_from_file_location("align_tables", SCRIPT)
align_tables = importlib.util.module_from_spec(spec)
spec.loader.exec_module(align_tables)

width = align_tables.string_width
align = align_tables.align_tables


class StringWidthTest(unittest.TestCase):
    def test_ascii(self):
        self.assertEqual(width("abc"), 3)

    def test_cjk_is_double_wide(self):
        self.assertEqual(width("日本"), 4)

    def test_combining_mark_adds_nothing(self):
        self.assertEqual(width("é"), 1)  # e + combining acute

    def test_zero_width_space(self):
        self.assertEqual(width("a​b"), 2)

    def test_basic_emoji(self):
        self.assertEqual(width("\U0001f600"), 2)  # grinning face

    def test_text_symbol_without_selector(self):
        self.assertEqual(width("❤"), 1)  # heavy black heart, text presentation

    def test_variation_selector_promotes_to_emoji(self):
        self.assertEqual(width("❤️"), 2)  # red heart emoji

    def test_flag_pair_is_one_glyph(self):
        self.assertEqual(width("\U0001f1fa\U0001f1f8"), 2)  # US flag

    def test_zwj_family_is_one_glyph(self):
        family = "\U0001f468‍\U0001f469‍\U0001f467"  # man + woman + girl
        self.assertEqual(width(family), 2)

    def test_skin_tone_modifier_merges(self):
        self.assertEqual(width("\U0001f44d\U0001f3fb"), 2)  # thumbs up + light skin


class AlignmentTest(unittest.TestCase):
    def _segment_widths(self, row: str) -> list[int]:
        # Measure the rendered width between pipes, padding included.
        return [width(segment) for segment in row.split("|")[1:-1]]

    def test_ascii_table(self):
        # Columns pad to a 3-char minimum so delimiter rows stay valid markdown.
        source = "| a | bbbb |\n| - | - |\n| cc | d |\n"
        expected = "| a   | bbbb |\n| --- | ---- |\n| cc  | d    |\n"
        self.assertEqual(align(source), expected)

    def test_columns_share_display_width_with_emoji(self):
        source = "| Name | Mark |\n| --- | --- |\n| ok | \U0001f600 |\n| longer | \U0001f1fa\U0001f1f8 |\n"
        out = align(source)
        rows = [line for line in out.splitlines() if line.startswith("|")]
        reference = self._segment_widths(rows[0])
        for row in rows:
            self.assertEqual(self._segment_widths(row), reference)

    def test_alignment_markers_preserved(self):
        source = "| a | b | c |\n| :- | :-: | -: |\n| x | y | z |\n"
        out = align(source)
        delimiter = out.splitlines()[1]
        self.assertIn(":--", delimiter)
        self.assertIn(":-:", delimiter)
        self.assertIn("--:", delimiter)

    def test_non_table_text_untouched(self):
        source = "# Title\n\nSome prose with a | pipe but no table.\n"
        self.assertEqual(align(source), source)

    def test_trailing_newline_preserved(self):
        self.assertTrue(align("| a |\n| - |\n| b |\n").endswith("|\n"))
        self.assertFalse(align("| a |\n| - |\n| b |").endswith("\n"))

    def test_idempotent(self):
        source = "| Name | Mark |\n| --- | --- |\n| ok | \U0001f600 |\n| longer | \U0001f1fa\U0001f1f8 |\n"
        once = align(source)
        self.assertEqual(align(once), once)


if __name__ == "__main__":
    unittest.main()
