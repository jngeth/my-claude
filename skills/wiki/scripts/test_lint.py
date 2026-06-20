"""Tests for lint.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import ModuleType


def run_lint(module: ModuleType, wiki_dir: Path) -> str:
    """Invoke lint.py as a subprocess and return its stdout."""
    script = module.__file__
    assert script is not None
    result = subprocess.run(
        [sys.executable, script, str(wiki_dir)],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def test_parse_links_plain_link(lint: ModuleType) -> None:
    assert lint.parse_links("see [[alpha]] here") == ["alpha"]


def test_parse_links_strips_whitespace(lint: ModuleType) -> None:
    assert lint.parse_links("[[  alpha  ]]") == ["alpha"]


def test_parse_links_alias_keeps_target_only(lint: ModuleType) -> None:
    assert lint.parse_links("[[alpha|Display Name]]") == ["alpha"]


def test_parse_links_anchor_keeps_target_only(lint: ModuleType) -> None:
    assert lint.parse_links("[[alpha#section]]") == ["alpha"]


def test_parse_links_anchor_and_alias(lint: ModuleType) -> None:
    assert lint.parse_links("[[alpha#section|Name]]") == ["alpha"]


def test_parse_links_multiple_links(lint: ModuleType) -> None:
    assert lint.parse_links("[[alpha]] [[beta]]") == ["alpha", "beta"]


def test_parse_links_no_links(lint: ModuleType) -> None:
    assert lint.parse_links("plain text") == []


def test_index_wikilink_reference(lint: ModuleType) -> None:
    assert lint.index_referenced_stems("[[beta]]") == {"beta"}


def test_index_markdown_link_reference(lint: ModuleType) -> None:
    assert lint.index_referenced_stems("[Alpha](alpha.md)") == {"alpha"}


def test_index_markdown_link_with_anchor(lint: ModuleType) -> None:
    assert lint.index_referenced_stems("[Alpha](alpha.md#intro)") == {"alpha"}


def test_index_lowercased(lint: ModuleType) -> None:
    assert lint.index_referenced_stems("[[Beta]]") == {"beta"}


def test_index_mixed_styles(lint: ModuleType) -> None:
    assert lint.index_referenced_stems("[Alpha](alpha.md) and [[beta]]") == {
        "alpha",
        "beta",
    }


def test_index_ignores_non_md_links(lint: ModuleType) -> None:
    assert lint.index_referenced_stems("[x](https://example.com)") == set()


def test_word_count_plain_words(lint: ModuleType) -> None:
    assert lint.word_count("one two three") == 3


def test_word_count_strips_frontmatter(lint: ModuleType) -> None:
    text = "---\ntitle: x\ntags: a b c\n---\none two\n"
    assert lint.word_count(text) == 2


def test_word_count_strips_code_fence(lint: ModuleType) -> None:
    text = "before\n```\nignored code here\n```\nafter"
    assert lint.word_count(text) == 2


def test_word_count_empty(lint: ModuleType) -> None:
    assert lint.word_count("") == 0


def test_e2e_full_report(lint: ModuleType, tmp_path: Path) -> None:
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    (wiki / "index.md").write_text("# Index\n- [Alpha](alpha.md)\n- [[beta]]\n")
    (wiki / "alpha.md").write_text("Alpha links to [[beta]] and [[ghost]].\n")
    (wiki / "beta.md").write_text("Beta short.\n")
    (wiki / "gamma.md").write_text(
        "Gamma is not indexed and has no inbound links at all.\n"
    )

    out = run_lint(lint, wiki)

    assert "[[ghost]]" in out  # broken link
    assert "- `gamma.md`" in out  # orphan + missing from index
    assert "- Broken links: 1" in out
    assert "- Missing from index: 1" in out


def test_e2e_missing_index(lint: ModuleType, tmp_path: Path) -> None:
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    (wiki / "alpha.md").write_text("content [[beta]]\n")
    (wiki / "beta.md").write_text("content\n")

    out = run_lint(lint, wiki)

    assert "`index.md` not found." in out


def test_e2e_bad_dir_exits_nonzero(lint: ModuleType) -> None:
    script = lint.__file__
    assert script is not None
    result = subprocess.run(
        [sys.executable, script, "/no/such/dir"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "not a directory" in result.stderr
