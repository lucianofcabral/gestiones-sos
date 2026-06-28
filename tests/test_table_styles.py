"""Unit tests for table styling CSS.

Tests verify that the style.css file contains required CSS classes and rules
for table inactive rows and Quasar table compatibility.
"""

import os


class TestTableStylesCSS:
    """Tests for table styles CSS file."""

    @staticmethod
    def _read_css_file() -> str:
        """Read the style.css file from src/ui/assets/."""
        css_path = "src/ui/assets/style.css"
        if not os.path.exists(css_path):
            raise FileNotFoundError(f"CSS file not found at {css_path}")
        with open(css_path, "r") as f:
            return f.read()

    def test_css_file_exists(self) -> None:
        """style.css file must exist at src/ui/assets/style.css."""
        css_path = "src/ui/assets/style.css"
        assert os.path.exists(css_path), f"CSS file not found at {css_path}"

    def test_css_contains_table_inactive_row_class(self) -> None:
        """CSS must define .table-inactive-row class."""
        css = self._read_css_file()
        assert ".table-inactive-row" in css

    def test_table_inactive_row_has_left_border(self) -> None:
        """table-inactive-row must have left border (2px solid)."""
        css = self._read_css_file()
        assert "border-left" in css
        assert "2px" in css

    def test_table_inactive_row_has_orange_color(self) -> None:
        """table-inactive-row left border must be orange (rgb(249, 115, 22))."""
        css = self._read_css_file()
        assert "249, 115, 22" in css or "orange" in css.lower()

    def test_table_inactive_row_has_opacity(self) -> None:
        """table-inactive-row must have opacity less than 1.0."""
        css = self._read_css_file()
        assert "opacity" in css
        # Check that opacity is set to 0.55 or similar
        assert "0.55" in css or "55%" in css

    def test_css_contains_q_table_class(self) -> None:
        """CSS must define .q-table class for Quasar table styling."""
        css = self._read_css_file()
        assert ".q-table" in css

    def test_css_contains_q_table_card_class(self) -> None:
        """CSS must define .q-table__card class for table card styling."""
        css = self._read_css_file()
        assert ".q-table__card" in css

    def test_q_table_has_transparent_background(self) -> None:
        """q-table must have transparent background for dark theme."""
        css = self._read_css_file()
        assert "background-color: transparent" in css

    def test_q_table_card_has_border(self) -> None:
        """q-table__card must have border for dark theme."""
        css = self._read_css_file()
        assert "border" in css

    def test_q_table_has_hover_state(self) -> None:
        """q-table must have hover state for rows."""
        css = self._read_css_file()
        assert "hover" in css or "tbody tr:hover" in css

    def test_css_no_syntax_errors(self) -> None:
        """CSS file should not have obvious syntax errors."""
        css = self._read_css_file()
        # Basic validation: count braces
        opening_braces = css.count("{")
        closing_braces = css.count("}")
        assert opening_braces == closing_braces, \
            f"CSS brace mismatch: {opening_braces} opening, {closing_braces} closing"

    def test_css_contains_comments(self) -> None:
        """CSS should contain section comments for readability."""
        css = self._read_css_file()
        assert "──" in css or "/*" in css
