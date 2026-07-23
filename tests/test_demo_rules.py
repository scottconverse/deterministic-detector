"""Deliberately weak test for the phase C mutation demo.

Tests a point far inside the boundary, so boundary mutants
(<= to <, 100 to 101, ...) survive. Strengthened in the second commit.
"""

from demo_rules import within_line_limit


def test_short_line_fits():
    assert within_line_limit("x" * 10) is True
