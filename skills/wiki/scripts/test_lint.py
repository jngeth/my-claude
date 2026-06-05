#!/usr/bin/env python3
"""Tests for lint.py. Run with: python3 -m unittest test_lint"""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "lint.py"

spec = importlib.util.spec_from_file_location("lint", SCRIPT)
lint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lint)


class ParseLinksTest(unittest.TestCase):
    def test_plain_link(self):
        self.assertEqual(lint.parse_links("see [[alpha]] here"), ["alpha"])

    def test_strips_whitespace(self):
        self.assertEqual(lint.parse_links("[[  alpha  ]]"), ["alpha"])

    def test_alias_keeps_target_only(self):
        self.assertEqual(lint.parse_links("[[alpha|Display Name]]"), ["alpha"])

    def test_anchor_keeps_target_only(self):
        self.assertEqual(lint.parse_links("[[alpha#section]]"), ["alpha"])

    def test_anchor_and_alias(self):
        self.assertEqual(lint.parse_links("[[alpha#section|Name]]"), ["alpha"])

    def test_multiple_links(self):
        self.assertEqual(lint.parse_links("[[alpha]] [[beta]]"), ["alpha", "beta"])

    def test_no_links(self):
        self.assertEqual(lint.parse_links("plain text"), [])


class IndexReferencedStemsTest(unittest.TestCase):
    def test_wikilink_reference(self):
        self.assertEqual(lint.index_referenced_stems("[[beta]]"), {"beta"})

    def test_markdown_link_reference(self):
        self.assertEqual(lint.index_referenced_stems("[Alpha](alpha.md)"), {"alpha"})

    def test_markdown_link_with_anchor(self):
        self.assertEqual(
            lint.index_referenced_stems("[Alpha](alpha.md#intro)"), {"alpha"}
        )

    def test_lowercased(self):
        self.assertEqual(lint.index_referenced_stems("[[Beta]]"), {"beta"})

    def test_mixed_styles(self):
        self.assertEqual(
            lint.index_referenced_stems("[Alpha](alpha.md) and [[beta]]"),
            {"alpha", "beta"},
        )

    def test_ignores_non_md_links(self):
        self.assertEqual(lint.index_referenced_stems("[x](https://example.com)"), set())


class WordCountTest(unittest.TestCase):
    def test_plain_words(self):
        self.assertEqual(lint.word_count("one two three"), 3)

    def test_strips_frontmatter(self):
        text = "---\ntitle: x\ntags: a b c\n---\none two\n"
        self.assertEqual(lint.word_count(text), 2)

    def test_strips_code_fence(self):
        text = "before\n```\nignored code here\n```\nafter"
        self.assertEqual(lint.word_count(text), 2)

    def test_empty(self):
        self.assertEqual(lint.word_count(""), 0)


class EndToEndTest(unittest.TestCase):
    def run_lint(self, wiki_dir: Path):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(wiki_dir)],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout

    def test_full_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki = Path(tmp) / "wiki"
            wiki.mkdir()
            (wiki / "index.md").write_text("# Index\n- [Alpha](alpha.md)\n- [[beta]]\n")
            (wiki / "alpha.md").write_text("Alpha links to [[beta]] and [[ghost]].\n")
            (wiki / "beta.md").write_text("Beta short.\n")
            (wiki / "gamma.md").write_text(
                "Gamma is not indexed and has no inbound links at all.\n"
            )

            out = self.run_lint(wiki)

            self.assertIn("[[ghost]]", out)  # broken link
            self.assertIn("- `gamma.md`", out)  # orphan + missing from index
            self.assertIn("- Broken links: 1", out)
            self.assertIn("- Missing from index: 1", out)

    def test_missing_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki = Path(tmp) / "wiki"
            wiki.mkdir()
            (wiki / "alpha.md").write_text("content [[beta]]\n")
            (wiki / "beta.md").write_text("content\n")

            out = self.run_lint(wiki)

            self.assertIn("`index.md` not found.", out)

    def test_bad_dir_exits_nonzero(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "/no/such/dir"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("not a directory", result.stderr)


if __name__ == "__main__":
    unittest.main()
