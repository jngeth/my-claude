#!/usr/bin/env python3
"""Wiki health check: broken [[links]], orphans, stubs, and index gaps.

Usage:
    lint.py [wiki_dir]

Default wiki_dir is ./wiki. Prints a markdown report to stdout. Exit code is 0 regardless of findings.
"""

import logging
import re
import sys
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)

SKIP_FILES = {"index.md", "log.md"}
STUB_WORD_LIMIT = 60
WIKILINK_REGEX = re.compile(r"\[\[([^\]|#]+?)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
MARKDOWN_LINK_REGEX = re.compile(r"\]\(([^)]+?\.md)(?:#[^)]*)?\)")


def find_md_files(root: Path) -> list[Path]:
    """Return every ``*.md`` file under ``root``, sorted by path."""
    return sorted(path for path in root.rglob("*.md") if path.is_file())


def parse_links(text: str) -> list[str]:
    """Extract the page names from all ``[[wikilinks]]`` in ``text``.

    Examples
    --------
    >>> parse_links("see [[Alpha]] and [[Beta#section|alias]]")
    ['Alpha', 'Beta']
    """
    return [match.group(1).strip() for match in WIKILINK_REGEX.finditer(text)]


def index_referenced_stems(text: str) -> set[str]:
    """Return lowercased page stems referenced by wikilinks or markdown links."""
    stems = {link.lower() for link in parse_links(text)}
    for match in MARKDOWN_LINK_REGEX.finditer(text):
        stems.add(Path(match.group(1)).stem.lower())
    return stems


def word_count(text: str) -> int:
    """Count words in ``text``, ignoring frontmatter and fenced code blocks.

    Examples
    --------
    >>> word_count("---\\ntitle: x\\n---\\nhello world")
    2
    """
    text = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.DOTALL)
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    return len(text.split())


def section(title: str, lines: list[str], empty: str = "None.") -> list[str]:
    """Render a report section, substituting ``empty`` when there are no lines."""
    block = [f"{title}\n"]
    if lines:
        block.extend(lines)
        block.append("")
    else:
        block.append(f"{empty}\n")
    return block


def main() -> None:
    """Lint the wiki directory (argv[1] or ./wiki) and print a markdown report."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    wiki_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "wiki").resolve()
    if not wiki_dir.is_dir():
        logger.error("not a directory: %s", wiki_dir)
        sys.exit(1)

    files = find_md_files(wiki_dir)
    by_name = {page.stem: page for page in files}
    by_lower = {page.stem.lower(): page for page in files}

    inbound: dict[Path, set[Path]] = defaultdict(set)
    broken: dict[Path, list[str]] = defaultdict(list)
    stubs: list[tuple[Path, int]] = []

    for page in files:
        text = page.read_text(encoding="utf-8", errors="replace")
        words = word_count(text)
        if page.name not in SKIP_FILES and words < STUB_WORD_LIMIT:
            stubs.append((page, words))
        for link in parse_links(text):
            target = by_name.get(link) or by_lower.get(link.lower())
            if target and target != page:
                inbound[target].add(page)
            elif not target:
                broken[page].append(link)

    orphans = [
        page for page in files if page.name not in SKIP_FILES and not inbound.get(page)
    ]

    index = wiki_dir / "index.md"
    index_text = (
        index.read_text(encoding="utf-8", errors="replace") if index.exists() else ""
    )

    referenced = index_referenced_stems(index_text)
    missing_from_index = [
        page
        for page in files
        if page.name not in SKIP_FILES and page.stem.lower() not in referenced
    ]

    def rel(page: Path) -> str:
        """Return ``page`` as a wiki-relative POSIX path for display."""
        return page.relative_to(wiki_dir).as_posix()

    out = []
    out.append("# Wiki Lint Report\n")
    out.append(f"Scanned `{wiki_dir}`: {len(files)} pages.\n")

    broken_lines = []
    for page, links in sorted(broken.items()):
        broken_lines.append(f"- `{rel(page)}`")
        for link in links:
            broken_lines.append(f"  - `[[{link}]]`")

    out += section("## Broken `[[links]]`", broken_lines)

    orphan_lines = [f"- `{rel(page)}`" for page in orphans]
    out += section("## Orphan pages (no inbound links)", orphan_lines)

    stub_lines = [
        f"- `{rel(page)}` ({count} words)"
        for page, count in sorted(stubs, key=lambda entry: entry[1])
    ]

    out += section(f"## Stub pages (< {STUB_WORD_LIMIT} words)", stub_lines)

    if not index.exists():
        out += section(
            "## Pages missing from `index.md`", [], empty="`index.md` not found."
        )
    else:
        missing_lines = [f"- `{rel(page)}`" for page in missing_from_index]
        out += section("## Pages missing from `index.md`", missing_lines)

    out.append("## Summary\n")
    out.append(f"- Pages: {len(files)}")
    out.append(f"- Broken links: {sum(len(links) for links in broken.values())}")
    out.append(f"- Orphans: {len(orphans)}")
    out.append(f"- Stubs: {len(stubs)}")
    out.append(f"- Missing from index: {len(missing_from_index)}")

    print("\n".join(out))


if __name__ == "__main__":
    main()
