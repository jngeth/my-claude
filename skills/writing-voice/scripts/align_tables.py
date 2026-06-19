#!/usr/bin/env python3
"""Align markdown table columns by display width, not character count.

Usage:
    align_tables.py [--write] [paths ...]

With no paths, reads markdown from stdin and writes the aligned result to stdout.
With paths, prints each aligned file to stdout, or rewrites in place when --write is set.

Column widths are measured by how many terminal cells a string occupies, so emoji,
CJK text, combining marks, flag sequences, and ZWJ emoji sequences stay aligned. A
naive len()-based aligner over-pads or under-pads any cell holding those characters.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

DELIMITER_CELL = re.compile(r"^:?-+:?$")

# Supplementary-plane pictographs that terminals render two cells wide regardless
# of any variation selector. Regional indicators (flags) and skin-tone modifiers
# live inside this span but are handled separately so sequences collapse correctly.
WIDE_EMOJI_START = 0x1F000
WIDE_EMOJI_END = 0x1FAFF


def _is_wide_codepoint(codepoint: int) -> bool:
    """Return whether a single codepoint renders two terminal cells wide."""
    if WIDE_EMOJI_START <= codepoint <= WIDE_EMOJI_END:
        return True
    return unicodedata.east_asian_width(chr(codepoint)) in ("W", "F")


def string_width(text: str) -> int:
    """Return the number of terminal cells `text` occupies.

    Combining marks and zero-width characters add nothing. East Asian wide
    characters and supplementary-plane emoji count as two. A trailing U+FE0F
    promotes the preceding text-presentation symbol from one cell to two. ZWJ
    sequences, skin-tone modifiers, and regional-indicator flag pairs collapse
    into the single glyph they render as.

    Examples
    --------
    >>> string_width("abc")
    3
    >>> string_width("漢字")
    4
    """
    total = 0
    last_width = 0
    after_zwj = False
    after_regional = False
    for char in text:
        codepoint = ord(char)

        if codepoint == 0x200D:  # zero-width joiner: the next char merges in
            after_zwj = True
            continue

        if codepoint == 0xFE0F:  # emoji variation selector promotes width 1 -> 2
            if last_width == 1:
                total += 1
                last_width = 2
            after_zwj = False
            continue

        if 0xFE00 <= codepoint <= 0xFE0E or codepoint in (0x200B, 0x200C, 0xFEFF):
            after_zwj = False
            continue

        if unicodedata.combining(char):
            after_zwj = False
            continue

        if 0x1F3FB <= codepoint <= 0x1F3FF:  # skin-tone modifier merges in
            after_zwj = False
            after_regional = False
            continue

        if after_zwj:  # this codepoint joins the previous glyph, no added width
            after_zwj = False
            after_regional = 0x1F1E6 <= codepoint <= 0x1F1FF
            continue

        if 0x1F1E6 <= codepoint <= 0x1F1FF:  # regional indicator
            if after_regional:  # second of a pair completes one flag glyph
                after_regional = False
                last_width = 0
                continue
            after_regional = True
            total += 2
            last_width = 2
            continue

        after_regional = False

        if codepoint < 0x20 or 0x7F <= codepoint < 0xA0:  # control character
            last_width = 0
            continue

        char_width = 2 if _is_wide_codepoint(codepoint) else 1
        total += char_width
        last_width = char_width
    return total


def _split_unescaped(text: str, delimiter: str) -> list[str]:
    r"""Split ``text`` on ``delimiter``, ignoring backslash-escaped delimiters.

    Examples
    --------
    >>> _split_unescaped(r"a\|b|c", "|")
    ['a\\|b', 'c']
    """
    parts = []
    current = []
    escaped = False
    for char in text:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            current.append(char)
            escaped = True
        elif char == delimiter:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    parts.append("".join(current))
    return parts


def split_cells(line: str) -> list[str]:
    """Split a markdown table row into stripped cell strings.

    Examples
    --------
    >>> split_cells("| a | b | c |")
    ['a', 'b', 'c']
    """
    content = line.strip()
    if content.startswith("|"):
        content = content[1:]
    if content.endswith("|") and not content.endswith("\\|"):
        content = content[:-1]
    return [cell.strip() for cell in _split_unescaped(content, "|")]


def is_delimiter_row(line: str) -> bool:
    """Return whether ``line`` is a table delimiter row (``|---|:--:|``).

    Examples
    --------
    >>> is_delimiter_row("|---|:--:|")
    True
    >>> is_delimiter_row("| a | b |")
    False
    """
    if "-" not in line:
        return False
    cells = split_cells(line)
    return bool(cells) and all(cell and DELIMITER_CELL.match(cell) for cell in cells)


def parse_alignment(cell: str) -> str:
    """Return the alignment a delimiter cell encodes via leading/trailing colons.

    Examples
    --------
    >>> parse_alignment(":--:")
    'center'
    >>> parse_alignment("--:")
    'right'
    >>> parse_alignment("---")
    'none'
    """
    cell = cell.strip()
    left = cell.startswith(":")
    right = cell.endswith(":")
    if left and right:
        return "center"
    if right:
        return "right"
    if left:
        return "left"
    return "none"


def _pad(cell: str, width: int, alignment: str) -> str:
    """Pad ``cell`` with spaces to ``width`` display cells per ``alignment``."""
    deficit = width - string_width(cell)
    if deficit <= 0:
        return cell
    if alignment == "right":
        return " " * deficit + cell
    if alignment == "center":
        left = deficit // 2
        return " " * left + cell + " " * (deficit - left)
    return cell + " " * deficit


def _delimiter_cell(width: int, alignment: str) -> str:
    """Render a delimiter cell of ``width`` dashes carrying ``alignment`` colons."""
    if alignment == "center":
        return ":" + "-" * (width - 2) + ":"
    if alignment == "right":
        return "-" * (width - 1) + ":"
    if alignment == "left":
        return ":" + "-" * (width - 1)
    return "-" * width


def _render_row(
    cells: list[str], widths: list[int], alignments: list[str], indent: str
) -> str:
    """Render one padded table row with ``| ... |`` separators and ``indent``."""
    padded = [
        _pad(cells[col] if col < len(cells) else "", width, alignments[col])
        for col, width in enumerate(widths)
    ]
    return indent + "| " + " | ".join(padded) + " |"


def _render_delimiter(widths: list[int], alignments: list[str], indent: str) -> str:
    """Render the delimiter row sized to ``widths`` and carrying ``alignments``."""
    cells = [
        _delimiter_cell(width, alignments[col]) for col, width in enumerate(widths)
    ]
    return indent + "| " + " | ".join(cells) + " |"


def _table_end(lines: list[str], start: int) -> int | None:
    """Return the exclusive end index of the table starting at ``start``, or None.

    A table requires a header row containing ``|`` followed by a delimiter row.
    Returns ``None`` when no table begins at ``start``.
    """
    header = lines[start]
    if "|" not in header or is_delimiter_row(header):
        return None
    if start + 1 >= len(lines) or not is_delimiter_row(lines[start + 1]):
        return None
    end = start + 2
    while end < len(lines) and lines[end].strip() and "|" in lines[end]:
        end += 1
    return end


def _align_block(rows: list[str]) -> list[str]:
    """Align one full table block (header, delimiter, body) to common widths."""
    indent = rows[0][: len(rows[0]) - len(rows[0].lstrip())]
    header = split_cells(rows[0])
    delimiters = split_cells(rows[1])
    body = [split_cells(row) for row in rows[2:]]

    column_count = max([len(header), len(delimiters)] + [len(row) for row in body])
    alignments = [
        parse_alignment(delimiters[col]) if col < len(delimiters) else "none"
        for col in range(column_count)
    ]

    content_rows = [header] + body
    widths = []
    for col in range(column_count):
        widest = max(
            (string_width(row[col]) for row in content_rows if col < len(row)),
            default=0,
        )
        widths.append(max(widest, 3))

    aligned = [
        _render_row(header, widths, alignments, indent),
        _render_delimiter(widths, alignments, indent),
    ]
    aligned.extend(_render_row(row, widths, alignments, indent) for row in body)
    return aligned


def align_tables(text: str) -> str:
    r"""Re-align every markdown table in ``text``, leaving other lines untouched.

    Examples
    --------
    >>> print(align_tables("| a | bb |\n|---|---|\n| ccc | d |"))
    | a   | bb  |
    | --- | --- |
    | ccc | d   |
    """
    lines = text.split("\n")
    output = []
    index = 0
    while index < len(lines):
        end = _table_end(lines, index)
        if end is None:
            output.append(lines[index])
            index += 1
        else:
            output.extend(_align_block(lines[index:end]))
            index = end
    return "\n".join(output)


def main() -> None:
    """Align tables from stdin or the given files, printing or rewriting in place."""
    parser = argparse.ArgumentParser(
        description="Align markdown table columns, accounting for emoji and wide characters."
    )
    parser.add_argument(
        "paths", nargs="*", help="Markdown files to align. Reads stdin when omitted."
    )
    parser.add_argument(
        "-w",
        "--write",
        action="store_true",
        help="Rewrite files in place instead of printing.",
    )
    args = parser.parse_args()

    if args.write and not args.paths:
        parser.error("--write requires at least one file path")

    if not args.paths:
        sys.stdout.write(align_tables(sys.stdin.read()))
        return

    for path_str in args.paths:
        path = Path(path_str)
        result = align_tables(path.read_text(encoding="utf-8"))
        if args.write:
            path.write_text(result, encoding="utf-8")
        else:
            sys.stdout.write(result)


if __name__ == "__main__":
    main()
