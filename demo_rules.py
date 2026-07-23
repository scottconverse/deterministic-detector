"""Throwaway module for the phase C mutation demo (docs/plan-v1.2.md).

This file exists only on the demo branch and is never merged.
"""


def within_line_limit(line: str, limit: int = 100) -> bool:
    return len(line) <= limit
