"""Strengthened tests for the phase C mutation demo.

The weak version tested one point far inside the boundary; these pin the
boundary itself (inclusive), the rejection side, and the custom limit, so
boundary mutants have nowhere to hide.
"""

from demo_rules import within_line_limit


def test_short_line_fits():
    assert within_line_limit("x" * 10) is True


def test_boundary_is_inclusive():
    assert within_line_limit("x" * 100) is True


def test_over_limit_rejected():
    assert within_line_limit("x" * 101) is False


def test_custom_limit_respected():
    assert within_line_limit("x" * 4, limit=4) is True
    assert within_line_limit("x" * 5, limit=4) is False
