"""Tests for align_tables.py."""

from types import ModuleType


def segment_widths(align_tables: ModuleType, row: str) -> list[int]:
    """Measure the rendered width between pipes, padding included."""
    return [align_tables.string_width(segment) for segment in row.split("|")[1:-1]]


def test_width_ascii(align_tables: ModuleType) -> None:
    assert align_tables.string_width("abc") == 3


def test_width_cjk_is_double_wide(align_tables: ModuleType) -> None:
    assert align_tables.string_width("日本") == 4


def test_width_combining_mark_adds_nothing(align_tables: ModuleType) -> None:
    assert align_tables.string_width("é") == 1  # e + combining acute


def test_width_zero_width_space(align_tables: ModuleType) -> None:
    assert align_tables.string_width("a​b") == 2


def test_width_basic_emoji(align_tables: ModuleType) -> None:
    assert align_tables.string_width("\U0001f600") == 2  # grinning face


def test_width_text_symbol_without_selector(align_tables: ModuleType) -> None:
    assert align_tables.string_width("❤") == 1  # heavy black heart, text presentation


def test_width_variation_selector_promotes_to_emoji(align_tables: ModuleType) -> None:
    assert align_tables.string_width("❤️") == 2  # red heart emoji


def test_width_flag_pair_is_one_glyph(align_tables: ModuleType) -> None:
    assert align_tables.string_width("\U0001f1fa\U0001f1f8") == 2  # US flag


def test_width_zwj_family_is_one_glyph(align_tables: ModuleType) -> None:
    family = "\U0001f468‍\U0001f469‍\U0001f467"  # man + woman + girl
    assert align_tables.string_width(family) == 2


def test_width_skin_tone_modifier_merges(align_tables: ModuleType) -> None:
    assert (
        align_tables.string_width("\U0001f44d\U0001f3fb") == 2
    )  # thumbs up + light skin


def test_ascii_table(align_tables: ModuleType) -> None:
    # Columns pad to a 3-char minimum so delimiter rows stay valid markdown.
    source = "| a | bbbb |\n| - | - |\n| cc | d |\n"
    expected = "| a   | bbbb |\n| --- | ---- |\n| cc  | d    |\n"
    assert align_tables.align_tables(source) == expected


def test_columns_share_display_width_with_emoji(align_tables: ModuleType) -> None:
    source = "| Name | Mark |\n| --- | --- |\n| ok | \U0001f600 |\n| longer | \U0001f1fa\U0001f1f8 |\n"
    out = align_tables.align_tables(source)
    rows = [line for line in out.splitlines() if line.startswith("|")]
    reference = segment_widths(align_tables, rows[0])
    for row in rows:
        assert segment_widths(align_tables, row) == reference


def test_alignment_markers_preserved(align_tables: ModuleType) -> None:
    source = "| a | b | c |\n| :- | :-: | -: |\n| x | y | z |\n"
    out = align_tables.align_tables(source)
    delimiter = out.splitlines()[1]
    assert ":--" in delimiter
    assert ":-:" in delimiter
    assert "--:" in delimiter


def test_non_table_text_untouched(align_tables: ModuleType) -> None:
    source = "# Title\n\nSome prose with a | pipe but no table.\n"
    assert align_tables.align_tables(source) == source


def test_trailing_newline_preserved(align_tables: ModuleType) -> None:
    assert align_tables.align_tables("| a |\n| - |\n| b |\n").endswith("|\n")
    assert not align_tables.align_tables("| a |\n| - |\n| b |").endswith("\n")


def test_idempotent(align_tables: ModuleType) -> None:
    source = "| Name | Mark |\n| --- | --- |\n| ok | \U0001f600 |\n| longer | \U0001f1fa\U0001f1f8 |\n"
    once = align_tables.align_tables(source)
    assert align_tables.align_tables(once) == once
